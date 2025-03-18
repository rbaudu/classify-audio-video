# -*- coding: utf-8 -*-
"""
Adaptateur pour faciliter l'utilisation de OBS31Capture avec les modules existants
"""

import logging
from server.capture.obs_31_capture import OBS31Capture
from server.capture.obs_events_31 import OBS31EventHandler
from server.capture.obs_media_31 import OBS31MediaManager
from server.capture.obs_sources_31 import OBS31SourceManager

logger = logging.getLogger(__name__)

class OBS31Adapter:
    """
    Classe adaptateur qui enveloppe OBS31Capture et ses modules pour faciliter la migration
    depuis l'ancienne implémentation OBSCapture
    """
    
    def __init__(self, host="localhost", port=4455, password=None):
        """Initialise l'adaptateur OBS 31.0.2+
        
        Args:
            host (str, optional): Hôte OBS WebSocket. Par défaut "localhost".
            port (int, optional): Port OBS WebSocket. Par défaut 4455.
            password (str, optional): Mot de passe OBS WebSocket. Par défaut None.
        """
        # Créer les instances des composants OBS 31
        self.capture = OBS31Capture(host=host, port=port, password=password)
        self.events = OBS31EventHandler(host=host, port=port, password=password)
        self.media = OBS31MediaManager(host=host, port=port, password=password)
        self.sources = OBS31SourceManager(host=host, port=port, password=password)
        
        # État de la connexion
        self.connected = self.capture.connected
        
        # Récupérer les sources disponibles
        self.video_sources = self.capture.video_sources
        self.media_sources = self.capture.media_sources
        
        # Permettre le mode fallback avec des images de test
        self.use_test_images = False
        
        logger.info("Adaptateur OBS31 initialisé")
    
    def _get_sources(self):
        """Rafraîchit la liste des sources disponibles"""
        # Récupérer les sources via la capture principale
        self.capture._get_sources()
        
        # Synchroniser avec les autres composants
        self.video_sources = self.capture.video_sources
        self.media_sources = self.capture.media_sources
    
    def capture_frame(self, source_name=None):
        """Capture une image d'une source OBS
        
        Args:
            source_name (str, optional): Nom de la source à capturer. Par défaut None.
        
        Returns:
            PIL.Image.Image: Image capturée
        """
        # Utiliser directement la méthode de OBS31Capture
        return self.capture.capture_frame(source_name)
    
    def get_current_frame(self):
        """Récupère l'image capturée la plus récente
        
        Returns:
            tuple: (PIL.Image.Image, float) Image et timestamp
        """
        return self.capture.get_current_frame()
    
    def get_frame_as_jpeg(self, quality=85):
        """Convertit l'image courante en JPEG
        
        Args:
            quality (int): Qualité JPEG (1-100)
            
        Returns:
            bytes: Données JPEG
        """
        return self.capture.get_frame_as_jpeg(quality)
    
    def start_capture(self, source_name=None, interval=0.1):
        """Démarre la capture continue en arrière-plan
        
        Args:
            source_name (str, optional): Source à capturer. Par défaut None.
            interval (float, optional): Intervalle entre les captures (secondes). Par défaut 0.1.
        """
        self.capture.start_capture(source_name, interval)
    
    def stop_capture(self):
        """Arrête la capture continue"""
        self.capture.stop_capture()
    
    def enable_test_images(self, enable=True):
        """Active ou désactive l'utilisation d'images de test en cas d'échec
        
        Args:
            enable (bool): True pour activer, False pour désactiver
        """
        self.use_test_images = enable
        self.capture.enable_test_images(enable)
    
    def disconnect(self):
        """Déconnecte du serveur OBS WebSocket"""
        # Arrêter la capture
        self.stop_capture()
        
        # Déconnecter tous les composants
        self.capture.disconnect()
        self.events.disconnect()
        self.media.disconnect()
        self.sources.disconnect()
        
        # Mettre à jour l'état
        self.connected = False
        
        logger.info("Déconnecté d'OBS WebSocket")
    
    # Méthodes de compatibilité avec l'ancienne API
    
    def get_media_sources(self):
        """Récupère la liste des sources média disponibles
        
        Returns:
            list: Liste des sources média
        """
        return self.media.get_media_sources()
    
    def get_media_properties(self, source_name):
        """Récupère les propriétés d'une source média
        
        Args:
            source_name (str): Nom de la source média
        
        Returns:
            dict: Propriétés de la source média
        """
        return self.media.get_media_properties(source_name)
    
    def control_media(self, source_name, action, position=None):
        """Contrôle la lecture d'un média
        
        Args:
            source_name (str): Nom de la source média
            action (str): Action à effectuer ('play', 'pause', 'restart', 'stop', 'seek')
            position (float, optional): Position en secondes pour l'action 'seek'.
        
        Returns:
            bool: True si l'action a été effectuée avec succès
        """
        return self.media.control_media(source_name, action, position)
    
    def get_media_time(self, source_name):
        """Récupère le temps de lecture actuel d'un média
        
        Args:
            source_name (str): Nom de la source média
        
        Returns:
            dict: Informations de temps du média
        """
        return self.media.get_media_time(source_name)
    
    def register_event_callback(self, event_name, callback):
        """Enregistre un callback pour un événement OBS
        
        Args:
            event_name (str): Nom de l'événement
            callback (callable): Fonction à appeler lors de la réception de l'événement
        
        Returns:
            bool: True si l'enregistrement a réussi
        """
        return self.events.register_callback(event_name, callback)
