# -*- coding: utf-8 -*-
"""
Module de gestion des événements OBS pour OBS 31.0.2+
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
        # (chaînes directes au lieu d'utiliser obsws.EventSubscription qui n'existe pas)
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
            
            # Enregistrer les callbacks pour les événements - Version simplifiée
            # N'utilisez plus obsws.EventSubscription qui n'existe pas
            try:
                # Essayer d'enregistrer directement avec les chaînes d'événement
                for event_name, obs_event in self.event_mappings.items():
                    self.client.callback.register(
                        obs_event,  # Utiliser la chaîne directement au lieu de obsws.EventSubscription.X
                        lambda event, event_name=event_name: self._handle_event(event, event_name)
                    )
                
                # Marquer comme connecté
                self.connected = True
                logger.info("Gestionnaire d'événements OBS connecté avec succès")
            except Exception as callback_err:
                logger.error(f"Erreur lors de l'enregistrement des callbacks: {str(callback_err)}")
                # Ne pas échouer complètement, continuer même si les callbacks ne fonctionnent pas
                self.connected = True
                logger.info("Gestionnaire d'événements OBS connecté (sans callbacks)")
            
        except Exception as e:
            logger.error(f"Erreur de connexion au gestionnaire d'événements OBS: {str(e)}")
            self.connected = False
            self.client = None
    
    def _handle_event(self, event, event_name):
        """Gère un événement OBS reçu
        
        Args:
            event: Objet d'événement obsws_python
            event_name (str): Nom de l'événement
        """
        # Trouver la méthode de callback pour cet événement
        if event_name in self.callbacks and callable(self.callbacks[event_name]):
            try:
                # Convertir l'événement en dictionnaire pour le passer au callback
                event_data = {}
                
                # Extraction des données en fonction du type d'événement
                if event_name == 'scene_changed':
                    if hasattr(event, 'scene_name'):
                        event_data['scene_name'] = event.scene_name
                    else:
                        logger.warning(f"Événement {event_name} reçu sans attribut 'scene_name'")
                
                elif event_name == 'media_started' or event_name == 'media_ended' or event_name == 'media_paused':
                    if hasattr(event, 'input_name'):
                        event_data['source_name'] = event.input_name
                    elif hasattr(event, 'source_name'):
                        event_data['source_name'] = event.source_name
                    else:
                        logger.warning(f"Événement {event_name} reçu sans attribut 'source_name'")
                
                elif event_name == 'source_created' or event_name == 'source_removed':
                    if hasattr(event, 'input_name'):
                        event_data['source_name'] = event.input_name
                    elif hasattr(event, 'source_name'):
                        event_data['source_name'] = event.source_name
                    
                    if hasattr(event, 'input_kind'):
                        event_data['source_type'] = event.input_kind
                    elif hasattr(event, 'source_type'):
                        event_data['source_type'] = event.source_type
                
                elif event_name == 'source_activated':
                    if hasattr(event, 'input_name'):
                        event_data['source_name'] = event.input_name
                    elif hasattr(event, 'source_name'):
                        event_data['source_name'] = event.source_name
                    
                    if hasattr(event, 'active'):
                        event_data['active'] = event.active
                
                # Appeler le callback avec les données d'événement
                try:
                    self.callbacks[event_name](event_data)
                except Exception as callback_error:
                    logger.error(f"Erreur lors de l'exécution du callback pour {event_name}: {str(callback_error)}")
            
            except Exception as e:
                logger.error(f"Erreur lors du traitement de l'événement {event_name}: {str(e)}")
        else:
            # Événement reçu mais pas de callback enregistré
            logger.debug(f"Événement {event_name} reçu, mais aucun callback n'est enregistré")
    
    def register_callback(self, event_name, callback):
        """Enregistre un callback pour un événement
        
        Args:
            event_name (str): Nom de l'événement
            callback (callable): Fonction à appeler lors de la réception de l'événement
        
        Returns:
            bool: True si l'enregistrement a réussi, False sinon
        """
        if event_name not in self.event_mappings:
            logger.warning(f"Événement inconnu: {event_name}")
            return False
        
        if not callable(callback):
            logger.warning(f"Le callback pour {event_name} n'est pas callable")
            return False
        
        self.callbacks[event_name] = callback
        logger.info(f"Callback enregistré pour l'événement {event_name}")
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
