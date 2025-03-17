# -*- coding: utf-8 -*-
"""
Gestionnaire de synchronisation pour la capture audio/vidéo
"""

import logging
import time
import threading
from queue import Queue
import io
import numpy as np
from PIL import Image
import os

logger = logging.getLogger(__name__)

class SyncManager:
    """Gestionnaire de synchronisation pour coordonner la capture audio et vidéo"""
    
    def __init__(self, obs_capture, pyaudio_capture, stream_processor, buffer_size=10):
        """Initialise le gestionnaire de synchronisation
        
        Args:
            obs_capture (OBSCapture): Instance de capture OBS
            pyaudio_capture (PyAudioCapture): Instance de capture PyAudio
            stream_processor (StreamProcessor): Instance du processeur de flux
            buffer_size (int, optional): Taille du buffer de synchronisation. Par défaut 10.
        """
        self.obs_capture = obs_capture
        self.pyaudio_capture = pyaudio_capture
        self.stream_processor = stream_processor
        self.buffer_size = buffer_size
        
        # Buffer pour les données synchronisées
        self.video_buffer = Queue(maxsize=buffer_size)
        self.audio_buffer = Queue(maxsize=buffer_size)
        
        # Données synchronisées actuelles
        self.current_video_frame = None
        self.current_audio_data = None
        self.last_sync_time = 0
        
        # Fallback image (pour quand il n'y a pas de vidéo)
        self.fallback_image = self._create_fallback_image()
        
        # Verrou pour l'accès aux données synchronisées
        self.sync_lock = threading.Lock()
        
        # Thread de synchronisation
        self.sync_thread = None
        self.is_running = False
        
        logger.info("Gestionnaire de synchronisation initialisé")
    
    def _create_fallback_image(self, width=640, height=480):
        """Crée une image de secours quand la vidéo n'est pas disponible
        
        Args:
            width (int): Largeur de l'image
            height (int): Hauteur de l'image
            
        Returns:
            PIL.Image.Image: Image de secours
        """
        try:
            # Créer une image noire avec un message
            img = Image.new('RGB', (width, height), color='black')
            
            # Essayer d'ajouter un texte explicatif
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                
                # Messages à afficher
                lines = [
                    "Aucune source vidéo disponible",
                    "",
                    "Vérifiez que:",
                    "1. OBS Studio est en cours d'exécution",
                    "2. Le plugin OBS WebSocket est activé",
                    "3. Une source vidéo est configurée et active"
                ]
                
                # Commencer à dessiner le texte au centre
                y_position = height // 3
                for line in lines:
                    # Mesurer la taille du texte (approximativement)
                    text_width = len(line) * 10
                    x_position = (width - text_width) // 2
                    
                    # Dessiner le texte
                    draw.text((x_position, y_position), line, fill='white')
                    y_position += 30
            except Exception as e:
                logger.warning(f"Impossible d'ajouter du texte à l'image de secours: {e}")
            
            return img
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'image de secours: {e}")
            # En cas d'erreur, retourner une image vide
            return Image.new('RGB', (width, height), color='black')
    
    def start(self):
        """Démarre la capture synchronisée"""
        if self.is_running:
            logger.warning("La capture synchronisée est déjà en cours")
            return
        
        # Démarrer la capture audio
        self.pyaudio_capture.start()
        
        # Récupérer et rafraîchir les sources vidéo
        if hasattr(self.obs_capture, '_get_sources'):
            self.obs_capture._get_sources()
        
        # Démarrer la capture vidéo (utiliser la première source vidéo disponible)
        video_source = None
        if hasattr(self.obs_capture, 'video_sources') and self.obs_capture.video_sources:
            video_source = self.obs_capture.video_sources[0]
            logger.info(f"Utilisation de la source vidéo: {video_source}")
        
        if video_source:
            self.obs_capture.start_capture(source_name=video_source, interval=0.1)
        else:
            logger.warning("Aucune source vidéo disponible, capture vidéo désactivée")
            # Initialiser avec l'image de secours
            with self.sync_lock:
                self.current_video_frame = self.fallback_image
        
        # Démarrer le thread de synchronisation
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        logger.info("Thread de capture synchronisée démarré")
        logger.info("Capture synchronisée démarrée")
    
    def start_capture(self):
        """Alias pour start() pour la compatibilité"""
        logger.info("Appel à start_capture(), redirection vers start()")
        self.start()
    
    def _sync_loop(self):
        """Boucle de synchronisation exécutée dans un thread"""
        while self.is_running:
            # Récupérer une image de la caméra
            video_frame, video_time = self.obs_capture.get_current_frame()
            
            # Si pas de vidéo, utiliser l'image de secours
            if video_frame is None:
                video_frame = self.fallback_image
            
            # Récupérer des données audio récentes
            audio_data = self.pyaudio_capture.get_latest_audio()
            
            # Si nous avons à la fois une vidéo et de l'audio
            if video_frame is not None and audio_data is not None:
                # Traiter les données
                processed_video = self.stream_processor.process_video(video_frame)
                processed_audio = self.stream_processor.process_audio(audio_data)
                
                # Mettre à jour les données synchronisées
                with self.sync_lock:
                    self.current_video_frame = processed_video
                    self.current_audio_data = processed_audio
                    self.last_sync_time = time.time()
            
            # Attendre un court instant avant la prochaine synchronisation
            time.sleep(0.05)
    
    def get_sync_data(self):
        """Récupère les données audio/vidéo synchronisées
        
        Returns:
            tuple: (video_frame, audio_data, timestamp) ou (None, None, 0) si aucune donnée
        """
        with self.sync_lock:
            if self.current_video_frame is None and self.current_audio_data is None:
                return None, None, 0
            return self.current_video_frame, self.current_audio_data, self.last_sync_time
    
    def get_current_frame(self):
        """Récupère l'image courante
        
        Returns:
            PIL.Image.Image: Image courante ou image de secours
        """
        # Récupérer directement depuis OBS (plus récent)
        frame, _ = self.obs_capture.get_current_frame()
        
        # Si aucune image n'est disponible, essayer d'utiliser l'image synchronisée
        if frame is None:
            with self.sync_lock:
                if self.current_video_frame is not None:
                    frame = self.current_video_frame
                else:
                    frame = self.fallback_image
        
        return frame
    
    def get_current_audio(self):
        """Récupère les données audio courantes
        
        Returns:
            numpy.ndarray: Données audio ou None
        """
        with self.sync_lock:
            return self.current_audio_data
    
    def get_frame_as_jpeg(self, quality=85):
        """Récupère l'image courante au format JPEG
        
        Args:
            quality (int, optional): Qualité JPEG. Par défaut 85.
        
        Returns:
            bytes: Données JPEG ou None
        """
        frame = self.get_current_frame()
        
        if frame is not None:
            # Convertir l'image en JPEG
            img_buffer = io.BytesIO()
            frame.save(img_buffer, format='JPEG', quality=quality)
            return img_buffer.getvalue()
        
        return None
    
    def stop(self):
        """Arrête la capture synchronisée"""
        if not self.is_running:
            return
        
        # Arrêter le thread de synchronisation
        self.is_running = False
        
        if self.sync_thread:
            self.sync_thread.join(timeout=1.0)
            self.sync_thread = None
        
        # Arrêter la capture audio et vidéo
        self.pyaudio_capture.stop()
        self.obs_capture.stop_capture()
        
        logger.info("Capture synchronisée arrêtée")
    
    def is_video_available(self):
        """Vérifie si la vidéo est disponible
        
        Returns:
            bool: True si la vidéo est disponible (autre que l'image de secours)
        """
        frame, _ = self.obs_capture.get_current_frame()
        return frame is not None
    
    def is_audio_available(self):
        """Vérifie si l'audio est disponible
        
        Returns:
            bool: True si l'audio est disponible
        """
        audio = self.get_current_audio()
        return audio is not None
