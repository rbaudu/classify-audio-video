#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import threading
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)

class SyncManager:
    """
    Gestionnaire de synchronisation entre audio et vidéo.
    Permet de maintenir une cohérence temporelle entre les flux audio et vidéo
    pour l'analyse et la classification.
    """
    
    def __init__(self, buffer_size=5):
        """
        Initialise le gestionnaire de synchronisation.
        
        Args:
            buffer_size (int): Taille du buffer en secondes
        """
        self.buffer_size = buffer_size
        self.lock = threading.RLock()
        
        # Buffers pour les données vidéo et audio
        self.video_buffer = deque(maxlen=100)  # Stocke les timestamps et frames vidéo
        self.audio_buffer = deque(maxlen=100)  # Stocke les timestamps et données audio
        
        # Données les plus récentes (pour accès rapide)
        self.latest_video = None
        self.latest_audio = None
        
        # Données synchronisées actuelles
        self.current_sync_data = None
        
        logger.info(f"SyncManager initialisé avec buffer_size={buffer_size}s")
    
    def add_video_frame(self, frame_data):
        """
        Ajoute une frame vidéo au buffer.
        
        Args:
            frame_data (dict): Données de la frame vidéo
                Doit contenir au moins 'timestamp' et 'frame'
        """
        if not frame_data or 'timestamp' not in frame_data:
            return
        
        with self.lock:
            # Ajouter au buffer
            self.video_buffer.append(frame_data)
            
            # Mettre à jour la frame la plus récente
            self.latest_video = frame_data
            
            # Essayer de synchroniser
            self._try_sync()
    
    def add_audio_data(self, audio_data):
        """
        Ajoute des données audio au buffer.
        
        Args:
            audio_data (dict): Données audio
                Doit contenir au moins 'timestamp'
        """
        if not audio_data or 'timestamp' not in audio_data:
            return
        
        with self.lock:
            # Ajouter au buffer
            self.audio_buffer.append(audio_data)
            
            # Mettre à jour les données audio les plus récentes
            self.latest_audio = audio_data
            
            # Essayer de synchroniser
            self._try_sync()
    
    def _try_sync(self):
        """
        Essaie de synchroniser les dernières données audio et vidéo.
        """
        if not self.video_buffer or not self.audio_buffer:
            return
        
        # Trouver la paire la plus proche en temps
        best_video = None
        best_audio = None
        min_diff = float('inf')
        
        # Comparer les dernières entrées (plus efficace)
        video_times = [v['timestamp'] for v in self.video_buffer]
        audio_times = [a['timestamp'] for a in self.audio_buffer]
        
        # Trouver l'entrée audio la plus proche de la dernière vidéo
        if self.latest_video:
            video_time = self.latest_video['timestamp']
            closest_audio_idx = np.argmin(np.abs(np.array(audio_times) - video_time))
            closest_audio = self.audio_buffer[closest_audio_idx]
            
            diff = abs(closest_audio['timestamp'] - video_time)
            if diff < min_diff:
                min_diff = diff
                best_video = self.latest_video
                best_audio = closest_audio
        
        # Trouver l'entrée vidéo la plus proche de la dernière audio
        if self.latest_audio:
            audio_time = self.latest_audio['timestamp']
            closest_video_idx = np.argmin(np.abs(np.array(video_times) - audio_time))
            closest_video = self.video_buffer[closest_video_idx]
            
            diff = abs(closest_video['timestamp'] - audio_time)
            if diff < min_diff:
                min_diff = diff
                best_video = closest_video
                best_audio = self.latest_audio
        
        # Si la différence est acceptable (moins de 100ms), mettre à jour les données synchronisées
        if min_diff < 0.1:  # 100ms
            self.current_sync_data = {
                'video': best_video,
                'audio': best_audio,
                'timestamp': (best_video['timestamp'] + best_audio['timestamp']) / 2,
                'sync_diff_ms': min_diff * 1000
            }
            
            logger.debug(f"Synchronisation A/V réussie avec différence de {min_diff * 1000:.2f}ms")
    
    def get_synced_data(self, max_age_ms=500):
        """
        Récupère les dernières données audio/vidéo synchronisées.
        
        Args:
            max_age_ms (int): Âge maximal en millisecondes des données synchronisées
            
        Returns:
            dict: Données synchronisées ou None si pas de données récentes disponibles
        """
        with self.lock:
            if not self.current_sync_data:
                return None
            
            # Vérifier l'âge des données
            age = (time.time() - self.current_sync_data['timestamp']) * 1000
            if age > max_age_ms:
                logger.debug(f"Données synchronisées trop anciennes: {age:.2f}ms > {max_age_ms}ms")
                return None
            
            return self.current_sync_data
    
    def get_latest_data(self):
        """
        Récupère les dernières données audio et vidéo, même si elles ne sont pas parfaitement synchronisées.
        
        Returns:
            dict: Dernières données audio et vidéo
        """
        with self.lock:
            return {
                'video': self.latest_video,
                'audio': self.latest_audio,
                'timestamp': time.time(),
                'sync_diff_ms': None  # Non synchronisé
            }
    
    def clear_buffers(self):
        """
        Vide les buffers audio et vidéo.
        """
        with self.lock:
            self.video_buffer.clear()
            self.audio_buffer.clear()
            logger.info("Buffers audio et vidéo vidés")
