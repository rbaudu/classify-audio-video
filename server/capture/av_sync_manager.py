#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import threading
import numpy as np
from collections import deque

# Import des classes de capture
from server.capture.obs_capture import OBSCapture
from server.capture.audio_capture import AudioCapture
from server.capture.stream_processor import StreamProcessor

logger = logging.getLogger(__name__)

class AVSyncManager:
    """
    Gestionnaire de synchronisation audio-vidéo.
    Coordonne la capture et la synchronisation des flux audio et vidéo
    provenant de sources différentes (OBS pour la vidéo, PyAudio pour l'audio).
    """
    
    def __init__(self, obs_capture=None, audio_capture=None, stream_processor=None):
        """
        Initialise le gestionnaire de synchronisation A/V.
        
        Args:
            obs_capture (OBSCapture, optional): Instance de capture OBS.
                Si None, une nouvelle instance est créée.
            audio_capture (AudioCapture, optional): Instance de capture audio.
                Si None, une nouvelle instance est créée.
            stream_processor (StreamProcessor, optional): Instance de traitement de flux.
                Si None, une nouvelle instance est créée.
        """
        # Instances de capture
        self.obs_capture = obs_capture or OBSCapture()
        self.audio_capture = audio_capture or AudioCapture()
        self.stream_processor = stream_processor or StreamProcessor()
        
        # Historique des captures (pour resynchronisation)
        self.video_history = deque(maxlen=30)  # 30 dernières frames
        self.audio_history = deque(maxlen=30)  # 30 derniers échantillons audio
        
        # Paramètres de synchronisation
        self.sync_offset_ms = 0  # Décalage pour compenser la latence
        self.max_sync_diff_ms = 100  # Différence maximale tolérée pour considérer comme synchronisés
        
        # Verrou pour la synchronisation
        self.sync_lock = threading.Lock()
        
        # État de la capture
        self.is_capturing = False
        self.capture_thread = None
        
        # Minuterie pour les mesures de performances
        self.last_capture_time = 0
        self.capture_fps = 0
        
        logger.info("Gestionnaire de synchronisation A/V initialisé")
    
    def start_capture(self):
        """
        Démarre la capture audio et vidéo synchronisée.
        
        Returns:
            bool: True si la capture a démarré avec succès, False sinon.
        """
        if self.is_capturing:
            logger.warning("La capture est déjà en cours")
            return False
        
        try:
            # Démarrer la capture audio
            audio_success = self.audio_capture.start_recording()
            
            if not audio_success:
                logger.error("Impossible de démarrer la capture audio")
                return False
            
            # Vérifier la connexion OBS
            if not self.obs_capture.connected:
                if not self.obs_capture.connect():
                    logger.error("Impossible de se connecter à OBS")
                    self.audio_capture.stop_recording()
                    return False
            
            # Démarrer la capture périodique dans un thread séparé
            self.is_capturing = True
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            logger.info("Capture audio/vidéo synchronisée démarrée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la capture synchronisée: {str(e)}")
            # Nettoyage en cas d'erreur
            if self.audio_capture and hasattr(self.audio_capture, 'is_recording') and self.audio_capture.is_recording:
                self.audio_capture.stop_recording()
            return False
    
    def stop_capture(self):
        """
        Arrête la capture audio et vidéo synchronisée.
        """
        if not self.is_capturing:
            logger.warning("Aucune capture en cours")
            return
        
        # Signaler l'arrêt de la capture
        self.is_capturing = False
        
        # Attendre la fin du thread de capture
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        # Arrêter la capture audio
        if self.audio_capture:
            self.audio_capture.stop_recording()
        
        # Vider les historiques
        self.video_history.clear()
        self.audio_history.clear()
        
        logger.info("Capture audio/vidéo synchronisée arrêtée")
    
    def _capture_loop(self):
        """
        Boucle de capture périodique exécutée dans un thread séparé.
        Capture et synchronise les flux audio et vidéo.
        """
        frame_interval = 1.0 / 15  # ~15 FPS
        
        while self.is_capturing:
            start_time = time.time()
            
            try:
                # Capturer une image depuis OBS
                video_frame = self.obs_capture.get_current_frame()
                video_timestamp = time.time()
                
                if video_frame is not None:
                    # Traiter la frame vidéo
                    processed_video = self.stream_processor.process_video(video_frame)
                    
                    # Stocker dans l'historique vidéo
                    self.video_history.append({
                        'timestamp': video_timestamp,
                        'frame': video_frame,
                        'processed': processed_video
                    })
                
                # Capturer l'audio (déjà en cours en arrière-plan)
                audio_data = self.audio_capture.get_audio_data(duration_ms=500)
                
                if audio_data is not None:
                    # Stocker dans l'historique audio
                    self.audio_history.append(audio_data)
                
                # Calculer le FPS
                current_time = time.time()
                if self.last_capture_time > 0:
                    self.capture_fps = 1.0 / (current_time - self.last_capture_time)
                self.last_capture_time = current_time
                
                # Attendre pour maintenir le FPS cible
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle de capture: {str(e)}")
                time.sleep(1.0)  # Pause plus longue en cas d'erreur
    
    def get_synchronized_data(self, max_age_ms=1000):
        """
        Récupère les dernières données audio et vidéo synchronisées.
        
        Args:
            max_age_ms (int, optional): Âge maximal des données en millisecondes.
                Défaut à 1000ms (1 seconde).
        
        Returns:
            dict: Données audio et vidéo synchronisées ou None si non disponibles.
        """
        with self.sync_lock:
            if not self.video_history or not self.audio_history:
                logger.warning("Historique audio ou vidéo vide")
                return None
            
            # Récupérer la dernière frame vidéo
            last_video = self.video_history[-1]
            video_time = last_video['timestamp']
            
            # Vérifier l'âge de la frame
            current_time = time.time()
            video_age_ms = (current_time - video_time) * 1000
            
            if video_age_ms > max_age_ms:
                logger.warning(f"Frame vidéo trop ancienne ({video_age_ms:.1f}ms)")
                return None
            
            # Trouver les données audio les plus proches en temps
            best_audio = None
            best_time_diff = float('inf')
            
            for audio in self.audio_history:
                audio_time = audio['timestamp']
                time_diff = abs((audio_time - video_time) * 1000 + self.sync_offset_ms)
                
                if time_diff < best_time_diff:
                    best_time_diff = time_diff
                    best_audio = audio
            
            # Vérifier si la différence de temps est acceptable
            if best_time_diff > self.max_sync_diff_ms:
                logger.warning(f"Différence de synchronisation trop importante ({best_time_diff:.1f}ms)")
            
            # Résultat synchronisé
            result = {
                'video': last_video['processed'],
                'audio': best_audio,
                'timestamp': video_time,
                'sync_diff_ms': best_time_diff,
                'fps': self.capture_fps
            }
            
            return result
    
    def adjust_sync_offset(self, offset_ms):
        """
        Ajuste le décalage de synchronisation audio/vidéo.
        
        Args:
            offset_ms (int): Décalage en millisecondes.
                Positif si l'audio est en avance, négatif si en retard.
        """
        with self.sync_lock:
            self.sync_offset_ms = offset_ms
            logger.info(f"Décalage de synchronisation A/V ajusté à {offset_ms}ms")
    
    def get_performance_stats(self):
        """
        Récupère des statistiques de performance.
        
        Returns:
            dict: Statistiques de performance.
        """
        return {
            'fps': self.capture_fps,
            'video_buffer_size': len(self.video_history),
            'audio_buffer_size': len(self.audio_history),
            'sync_offset_ms': self.sync_offset_ms
        }
    
    def get_status(self):
        """
        Récupère l'état actuel du gestionnaire.
        
        Returns:
            dict: État actuel du gestionnaire.
        """
        return {
            'is_capturing': self.is_capturing,
            'obs_connected': self.obs_capture.connected if self.obs_capture else False,
            'audio_recording': self.audio_capture.is_recording if self.audio_capture else False,
            'stats': self.get_performance_stats()
        }
    
    def __del__(self):
        """
        Nettoyage lors de la destruction de l'objet.
        """
        self.stop_capture()
