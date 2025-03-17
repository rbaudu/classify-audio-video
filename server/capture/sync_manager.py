#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import threading
import numpy as np
from collections import deque
import os
import cv2
import wave

# Import des modules de capture
from server.capture.obs_capture import OBSCapture
from server.capture.pyaudio_capture import PyAudioCapture
from server.capture.stream_processor import StreamProcessor

# Import de la configuration
from server import (
    AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_FORMAT, AUDIO_CHUNK_SIZE,
    AUDIO_VIDEO_SYNC_BUFFER_SIZE, VIDEO_SOURCE_NAME, BASE_DIR
)

class SyncManager:
    """
    Gestionnaire de synchronisation entre la capture audio (PyAudio) et vidéo (OBS).
    S'occupe de capturer les deux flux, de les synchroniser et de les traiter.
    """
    
    def __init__(self, stop_event=None):
        self.logger = logging.getLogger(__name__)
        
        # Instancier les objets de capture
        self.obs_capture = OBSCapture()
        self.audio_capture = PyAudioCapture()
        self.processor = StreamProcessor()
        
        # Variables d'état
        self._is_running = False  # Renamed to avoid conflict with is_running() method
        self.capture_thread = None
        
        # Événement d'arrêt
        self.stop_event = stop_event or threading.Event()
        
        # Buffer pour les frames vidéo avec horodatage
        self.video_buffer = deque(maxlen=30)  # 30 frames ~ 1 sec à 30 FPS
        
        # Répertoire temporaire pour les captures
        self.temp_dir = os.path.join(BASE_DIR, '..', 'data', 'temp_captures')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.logger.info("Gestionnaire de synchronisation initialisé")
    
    def start(self):
        """
        Démarre la capture synchronisée audio/vidéo
        
        Returns:
            bool: True si démarré avec succès, False sinon
        """
        if self._is_running:
            self.logger.warning("La capture synchronisée est déjà en cours")
            return True
        
        try:
            # Réinitialiser l'événement d'arrêt
            self.stop_event.clear()
            
            # S'assurer que la connexion OBS est établie
            if not self.obs_capture.connected:
                if not self.obs_capture.connect():
                    self.logger.error("Impossible de se connecter à OBS")
                    return False
            
            # Démarrer la capture audio
            if not self.audio_capture.start_capture():
                self.logger.error("Impossible de démarrer la capture audio")
                return False
            
            # Démarrer le thread de capture synchronisée
            self._is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            self.logger.info("Capture synchronisée démarrée")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage de la capture synchronisée: {str(e)}")
            return False
    
    def start_capture(self):
        """
        Alias pour la méthode start() pour compatibilité avec les appels externes
        
        Returns:
            bool: True si démarré avec succès, False sinon
        """
        self.logger.info("Appel à start_capture(), redirection vers start()")
        return self.start()
    
    def stop(self, timeout=2.0):
        """
        Arrête la capture synchronisée
        
        Args:
            timeout (float): Temps maximum d'attente en secondes
            
        Returns:
            bool: True si arrêté avec succès, False sinon
        """
        if not self._is_running:
            return True
        
        try:
            # Signaler l'arrêt
            self._is_running = False
            self.stop_event.set()
            
            # Arrêter le thread de capture avec timeout
            if self.capture_thread:
                self.logger.info(f"Attente de l'arrêt du thread de capture (timeout: {timeout}s)...")
                self.capture_thread.join(timeout=timeout)
                
                if self.capture_thread.is_alive():
                    self.logger.warning(f"Le thread de capture ne s'est pas terminé dans le délai imparti ({timeout}s)")
            
            # Arrêter la capture audio
            self.audio_capture.stop_capture()
            
            self.logger.info("Capture synchronisée arrêtée")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt de la capture synchronisée: {str(e)}")
            return False
    
    def _capture_loop(self):
        """
        Boucle principale de capture synchronisée qui s'exécute dans un thread séparé
        """
        self.logger.info("Thread de capture synchronisée démarré")
        
        while self._is_running and not self.stop_event.is_set():
            try:
                # 1. Capturer une frame vidéo depuis OBS
                frame = self.obs_capture.get_video_frame(VIDEO_SOURCE_NAME)
                
                if frame is not None:
                    # Ajouter au buffer avec horodatage
                    timestamp = time.time()
                    self.video_buffer.append({
                        'frame': frame,
                        'timestamp': timestamp
                    })
                
                # 2. Vérifier si on doit s'arrêter
                if not self._is_running or self.stop_event.is_set():
                    break
                
                # 3. Dormir brièvement pour éviter de surcharger le CPU
                # Utiliser une période courte pour pouvoir s'arrêter rapidement
                time.sleep(0.01)  # Réactif aux signaux d'arrêt
                
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de capture: {str(e)}")
                # Pause courte en cas d'erreur pour éviter de surcharger le CPU
                time.sleep(0.1)
                
                # Vérifier si on doit s'arrêter même en cas d'erreur
                if not self._is_running or self.stop_event.is_set():
                    break
        
        self.logger.info("Thread de capture synchronisée terminé")
    
    def get_synchronized_data(self):
        """
        Récupère une paire synchronisée de données audio et vidéo
        
        Returns:
            dict: Dictionnaire contenant les données audio et vidéo synchronisées et leurs métadonnées
        """
        if not self._is_running or len(self.video_buffer) == 0:
            return None
        
        try:
            # 1. Récupérer la dernière frame vidéo du buffer
            video_data = self.video_buffer[-1]
            video_frame = video_data['frame']
            video_timestamp = video_data['timestamp']
            
            # 2. Récupérer les données audio actuelles
            audio_data = self.audio_capture.get_audio_data(duration_ms=500)
            
            if audio_data is None:
                self.logger.warning("Aucune donnée audio disponible pour la synchronisation")
                # Créer un tableau audio vide plutôt que de retourner None
                audio_data = np.zeros(int(AUDIO_SAMPLE_RATE * 0.5), dtype=np.int16)  # 500ms de silence
            
            # Créer un dictionnaire audio avec les métadonnées nécessaires
            audio_dict = {
                'samples': audio_data,
                'timestamp': time.time()
            }
            
            # 3. Traiter les données vidéo et audio
            processed_video = self.processor.process_video(video_frame)
            
            try:
                processed_audio = self.processor.process_audio(audio_dict['samples'])
            except Exception as audio_error:
                self.logger.error(f"Erreur lors du traitement audio: {str(audio_error)}")
                # Créer des données audio traitées minimales
                processed_audio = {
                    'processed_audio': np.zeros(100, dtype=np.float32),
                    'features': {
                        'rms_level': 0.0,
                        'zero_crossing_rate': 0.0,
                        'dominant_frequency': 0.0,
                        'mid_freq_ratio': 0.3
                    }
                }
            
            if processed_video is None:
                self.logger.warning("Échec du traitement vidéo")
                # On peut continuer avec des données vidéo minimales
                processed_video = {
                    'processed_frame': np.zeros((360, 640, 3), dtype=np.float32),
                    'features': {
                        'motion_percent': 0.0,
                        'skin_percent': 0.0,
                        'hsv_means': (0.0, 0.0, 0.0)
                    }
                }
            
            # 4. Combiner les résultats
            result = {
                'video': {
                    'frame': video_frame,
                    'processed': processed_video,
                    'timestamp': video_timestamp
                },
                'audio': {
                    'data': audio_dict,
                    'processed': processed_audio,
                    'timestamp': audio_dict.get('timestamp', time.time())
                },
                'sync_offset': abs(video_timestamp - audio_dict.get('timestamp', time.time()))
            }
            
            return result
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des données synchronisées: {str(e)}")
            return None
    
    def save_synchronized_clip(self, duration_seconds=5, prefix="clip"):
        """
        Sauvegarde un clip synchronisé de la durée spécifiée
        
        Args:
            duration_seconds (int, optional): Durée du clip en secondes. Défaut à 5.
            prefix (str, optional): Préfixe pour les noms de fichiers. Défaut à "clip".
            
        Returns:
            dict: Dictionnaire contenant les chemins des fichiers sauvegardés et les métadonnées
        """
        if not self._is_running:
            self.logger.warning("Impossible de sauvegarder: pas de capture en cours")
            return None
        
        try:
            # Générer les noms de fichiers
            timestamp = int(time.time())
            video_filename = os.path.join(self.temp_dir, f"{prefix}_video_{timestamp}.avi")
            audio_filename = os.path.join(self.temp_dir, f"{prefix}_audio_{timestamp}.wav")
            
            # 1. Sauvegarder l'audio
            audio_saved = self.audio_capture.save_audio_to_file(audio_filename, duration_seconds)
            
            # 2. Sauvegarder la vidéo (récupérer les dernières frames du buffer)
            video_saved = False
            
            if len(self.video_buffer) > 0:
                # Déterminer le nombre de frames à garder (supposons 30 FPS)
                frames_to_keep = min(len(self.video_buffer), int(duration_seconds * 30))
                frames = [item['frame'] for item in list(self.video_buffer)[-frames_to_keep:]]
                
                if frames:
                    # Créer une vidéo à partir des frames
                    height, width = frames[0].shape[:2]
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    out = cv2.VideoWriter(video_filename, fourcc, 30.0, (width, height))
                    
                    for frame in frames:
                        out.write(frame)
                    
                    out.release()
                    video_saved = True
            
            # 3. Retourner les informations
            result = {
                'success': audio_saved and video_saved,
                'video_path': video_filename if video_saved else None,
                'audio_path': audio_filename if audio_saved else None,
                'duration': duration_seconds,
                'timestamp': timestamp
            }
            
            if result['success']:
                self.logger.info(f"Clip synchronisé sauvegardé: vidéo={video_filename}, audio={audio_filename}")
            else:
                self.logger.warning(f"Problème lors de la sauvegarde du clip: vidéo={video_saved}, audio={audio_saved}")
            
            return result
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du clip synchronisé: {str(e)}")
            return None
    
    def close(self):
        """
        Ferme proprement toutes les ressources
        """
        try:
            # Arrêter la capture
            self.stop()
            
            # Fermer les captures
            self.audio_capture.close()
            self.obs_capture.disconnect()
            
            self.logger.info("Gestionnaire de synchronisation fermé")
        except Exception as e:
            self.logger.error(f"Erreur lors de la fermeture du gestionnaire de synchronisation: {str(e)}")
    
    def get_audio_devices(self):
        """
        Récupère la liste des périphériques audio disponibles
        
        Returns:
            list: Liste des périphériques audio
        """
        return self.audio_capture.get_devices()
    
    def set_audio_device(self, device_index):
        """
        Change le périphérique audio de capture
        
        Args:
            device_index (int): Indice du périphérique à utiliser
            
        Returns:
            bool: True si changé avec succès, False sinon
        """
        # Si la capture est en cours, l'arrêter temporairement
        was_running = self._is_running
        if was_running:
            self.stop()
        
        # Changer de périphérique
        result = self.audio_capture.stop_capture()
        if result:
            result = self.audio_capture.start_capture(device_index)
        
        # Redémarrer la capture si nécessaire
        if was_running and result:
            self.start()
        
        return result
    
    def is_running(self):
        """
        Indique si la capture est en cours
        
        Returns:
            bool: True si la capture est en cours, False sinon
        """
        return self._is_running
