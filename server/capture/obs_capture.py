import logging
import time
import threading
from obswebsocket import obsws, requests, events
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import random

# Import de la configuration
from server import OBS_HOST, OBS_PORT, OBS_PASSWORD, VIDEO_SOURCE_NAME
from server import OBS_RECONNECT_INTERVAL, OBS_MAX_RECONNECT_INTERVAL, OBS_MAX_RECONNECT_ATTEMPTS

class OBSCapture:
    """
    Classe pour capturer les flux vidéo depuis OBS Studio via le plugin websocket
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ws = None
        self.connected = False
        self.current_source = None
        self.video_sources = []
        self.media_sources = []
        self.current_frame = None
        self.reconnect_thread = None
        
        # Paramètres de reconnexion (importés depuis la configuration)
        self.reconnect_interval = OBS_RECONNECT_INTERVAL
        self.max_reconnect_interval = OBS_MAX_RECONNECT_INTERVAL
        self.max_reconnect_attempts = OBS_MAX_RECONNECT_ATTEMPTS
        
        self.reconnect_attempts = 0
        self.should_reconnect = True
        self.connection_lost_time = None
        
        # État des média
        self.media_states = {}
        
        # Mutex pour protéger l'accès au WebSocket
        self.ws_lock = threading.RLock()
        
        # Dernière image réussie (pour la récupération d'erreur)
        self.last_successful_frame = None
        
        # Tentative de connexion initiale
        self.connect()
    
    def connect(self):
        """
        Établit une connexion WebSocket avec OBS Studio
        """
        with self.ws_lock:
            if self.connected:
                return True
                
            try:
                self.logger.info(f"Tentative de connexion à OBS sur {OBS_HOST}:{OBS_PORT}")
                
                # Créer l'objet de connexion
                self.ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
                
                # Enregistrer les callbacks pour les événements
                self.ws.register(self._on_switch_scene, events.SwitchScenes)
                self.ws.register(self._on_stream_starting, events.StreamStarting)
                self.ws.register(self._on_stream_stopping, events.StreamStopping)
                self.ws.register(self._on_media_play, events.MediaStarted)
                self.ws.register(self._on_media_pause, events.MediaPaused)
                self.ws.register(self._on_media_stop, events.MediaStopped)
                self.ws.register(self._on_media_end, events.MediaEnded)
                self.ws.register(self._on_exit_started, events.ExitStarted)
                self.ws.register(self._on_connection_closed, events.ConnectionClosed)
                
                # Se connecter à OBS
                self.ws.connect()
                self.connected = True
                self.reconnect_attempts = 0
                self.connection_lost_time = None
                self.logger.info("Connecté à OBS avec succès")
                
                # Récupérer les sources disponibles
                self._refresh_sources()
                
                return True
            except Exception as e:
                self.logger.error(f"Erreur lors de la connexion à OBS: {str(e)}")
                self.connected = False
                
                # Enregistrer le moment où la connexion a été perdue
                if self.connection_lost_time is None:
                    self.connection_lost_time = time.time()
                
                # Lancer un thread pour tenter la reconnexion automatique
                if not self.reconnect_thread or not self.reconnect_thread.is_alive():
                    self.reconnect_thread = threading.Thread(target=self._reconnect_loop)
                    self.reconnect_thread.daemon = True
                    self.reconnect_thread.start()
                
                return False
    
    def disconnect(self):
        """
        Ferme la connexion avec OBS
        """
        with self.ws_lock:
            self.should_reconnect = False
            if self.ws and self.connected:
                try:
                    self.ws.disconnect()
                    self.logger.info("Déconnecté d'OBS")
                except Exception as e:
                    self.logger.error(f"Erreur lors de la déconnexion d'OBS: {str(e)}")
                finally:
                    self.connected = False
                    self.reconnect_attempts = 0
                    self.connection_lost_time = None
    
    def _reconnect_loop(self):
        """
        Boucle pour tenter de se reconnecter à OBS à intervalles réguliers
        """
        while self.should_reconnect and (self.max_reconnect_attempts == 0 or self.reconnect_attempts < self.max_reconnect_attempts):
            # Incrémenter le compteur de tentatives
            self.reconnect_attempts += 1
            
            # Calculer l'intervalle de reconnexion avec un backoff exponentiel
            if self.reconnect_attempts > 1:
                # Augmenter l'intervalle de reconnexion avec un peu d'aléatoire pour éviter les tempêtes de reconnexion
                jitter = random.uniform(0.8, 1.2)
                current_interval = min(
                    self.reconnect_interval * (1.5 ** (self.reconnect_attempts - 1)) * jitter,
                    self.max_reconnect_interval
                )
            else:
                current_interval = self.reconnect_interval
            
            self.logger.info(f"Tentative de reconnexion {self.reconnect_attempts} à OBS dans {current_interval:.1f} secondes...")
            
            # Attendre l'intervalle calculé
            time.sleep(current_interval)
            
            # Tentative de reconnexion
            if self.connect():
                self.logger.info(f"Reconnexion réussie après {self.reconnect_attempts} tentatives")
                # Durée totale de l'interruption
                if self.connection_lost_time:
                    downtime = time.time() - self.connection_lost_time
                    self.logger.info(f"Durée totale de l'interruption: {downtime:.1f} secondes")
                    self.connection_lost_time = None
                break  # Sortir de la boucle si reconnecté avec succès
    
    def _is_connection_error(self, error_message):
        """
        Détecte si une erreur est liée à une perte de connexion
        
        Args:
            error_message (str): Message d'erreur à analyser
        
        Returns:
            bool: True si c'est une erreur de connexion, False sinon
        """
        connection_error_patterns = [
            "socket is already closed",
            "not connected",
            "connection refused",
            "connection reset",
            "timed out",
            "network is unreachable",
            "connection was closed",
            "disconnected",
            "connection error",
            "failed to connect"
        ]
        
        for pattern in connection_error_patterns:
            if pattern.lower() in error_message.lower():
                return True
        
        return False
    
    def _handle_connection_lost(self):
        """
        Gère la perte de connexion et initialise la procédure de reconnexion
        """
        # Ne pas réinitialiser si déjà déconnecté
        if not self.connected:
            return
            
        self.connected = False
        
        # Enregistrer le moment où la connexion a été perdue
        if self.connection_lost_time is None:
            self.connection_lost_time = time.time()
        
        # Lancer la reconnexion si nécessaire
        if self.should_reconnect and (not self.reconnect_thread or not self.reconnect_thread.is_alive()):
            self.reconnect_thread = threading.Thread(target=self._reconnect_loop)
            self.reconnect_thread.daemon = True
            self.reconnect_thread.start()
    
    def _on_connection_closed(self, event):
        """
        Callback pour l'événement de fermeture de connexion
        """
        self.logger.warning("Événement de fermeture de connexion reçu")
        self._handle_connection_lost()
    
    def _on_exit_started(self, event):
        """
        Callback pour l'événement de fermeture d'OBS
        """
        self.logger.warning("Événement de fermeture d'OBS reçu")
        with self.ws_lock:
            self.connected = False
            self.should_reconnect = True  # On veut se reconnecter quand OBS redémarre
            
            # Enregistrer le moment où la connexion a été perdue
            if self.connection_lost_time is None:
                self.connection_lost_time = time.time()
