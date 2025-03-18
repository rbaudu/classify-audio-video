# -*- coding: utf-8 -*-
"""
Module de gestion des événements OBS pour OBS 31.0.2+
Version très simplifiée pour éviter les problèmes de compatibilité
"""

import logging
import obsws_python as obsws

logger = logging.getLogger(__name__)

class OBS31EventHandler:
    """
    Gestionnaire d'événements pour OBS 31.0.2+
    Cette classe peut être utilisée avec OBS31Capture
    """
    
    def __init__(self, host="localhost", port=4455, password=None):
        """Initialise le gestionnaire d'événements OBS
        
        Args:
            host (str, optional): Hôte OBS WebSocket. Par défaut "localhost".
            port (int, optional): Port OBS WebSocket. Par défaut 4455.
            password (str, optional): Mot de passe OBS WebSocket. Par défaut None.
        """
        self.host = host
        self.port = port
        self.password = password
        self.client = None
        self.connected = False
        self.callbacks = {}
        
        # Définir les mappings d'événements
        self.event_mappings = {
            'scene_changed': 'CurrentProgramSceneChanged',
            'streaming_started': 'StreamStarted',
            'streaming_stopped': 'StreamStopped',
            'recording_started': 'RecordingStarted',
            'recording_stopped': 'RecordingStopped',
            'media_started': 'MediaStarted',
            'media_ended': 'MediaEnded',
            'media_paused': 'MediaPaused',
            'source_created': 'InputCreated',
            'source_removed': 'InputRemoved',
            'source_activated': 'InputActiveStateChanged'
        }
        
        # Tenter de se connecter
        self._connect()
    
    def _connect(self):
        """Se connecte à OBS WebSocket et configure les callbacks d'événements"""
        try:
            logger.info(f"Tentative de connexion au gestionnaire d'événements OBS sur {self.host}:{self.port}")
            
            # Initialiser le client d'événements OBS WebSocket
            if self.password:
                self.client = obsws.EventClient(host=self.host, port=self.port, password=self.password)
            else:
                self.client = obsws.EventClient(host=self.host, port=self.port)
            
            # Version ultra-simplifiée : pas d'enregistrement de callbacks pour éviter les erreurs
            # Ne pas tenter d'utiliser client.callback.register qui cause l'erreur
            
            # Marquer comme connecté
            self.connected = True
            logger.info("Gestionnaire d'événements OBS connecté (sans gestion d'événements - mode compatible)")
            
        except Exception as e:
            logger.error(f"Erreur de connexion au gestionnaire d'événements OBS: {str(e)}")
            self.connected = False
            self.client = None
    
    def register_callback(self, event_name, callback):
        """
        Fonction simulée pour compatibilité. Les callbacks ne sont pas réellement enregistrés.
        
        Args:
            event_name (str): Nom de l'événement
            callback (callable): Fonction à appeler lors de la réception de l'événement
        
        Returns:
            bool: Toujours True pour maintenir la compatibilité
        """
        # Stocker le callback, mais il ne sera jamais appelé dans cette version simplifiée
        self.callbacks[event_name] = callback
        logger.info(f"Callback pour {event_name} enregistré (mode compatible, ne sera pas appelé)")
        return True
    
    def disconnect(self):
        """Déconnecte du serveur OBS WebSocket"""
        if self.client:
            try:
                self.client.disconnect()
            except Exception as e:
                logger.error(f"Erreur lors de la déconnexion: {str(e)}")
            
            self.client = None
            self.connected = False
            logger.info("Déconnecté du gestionnaire d'événements OBS")
