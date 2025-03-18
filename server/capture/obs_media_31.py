# -*- coding: utf-8 -*-
"""
Module de gestion des médias OBS pour OBS 31.0.2+
"""

import logging
import time
import threading
import obsws_python as obsws

logger = logging.getLogger(__name__)

class OBS31MediaManager:
    """
    Gestionnaire de médias pour OBS 31.0.2+
    """
    
    def __init__(self, host="localhost", port=4455, password=None):
        """Initialise le gestionnaire de médias OBS
        
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
        
        # État des médias (suivi des sources média)
        self.media_states = {}
        
        # Verrou pour les opérations WebSocket
        self.ws_lock = threading.Lock()
        
        # Initialisation de la gestion des erreurs
        self._initialize_media_state()
        
        # Se connecter à OBS
        self._connect()
    
    def _connect(self):
        """Se connecte à OBS WebSocket"""
        try:
            with self.ws_lock:
                logger.info(f"Tentative de connexion au gestionnaire de médias OBS sur {self.host}:{self.port}")
                
                # Initialiser le client OBS WebSocket
                if self.password:
                    self.client = obsws.ReqClient(host=self.host, port=self.port, password=self.password)
                else:
                    self.client = obsws.ReqClient(host=self.host, port=self.port)
                
                # Vérifier la connexion
                version = self.client.get_version()
                logger.info(f"Gestionnaire de médias OBS connecté avec succès")
                logger.info(f"Version OBS: {version.obs_version}, WebSocket: {version.obs_web_socket_version}")
                
                # Marquer comme connecté
                self.connected = True
                
        except Exception as e:
            logger.error(f"Erreur de connexion au gestionnaire de médias OBS: {str(e)}")
            self.connected = False
            self.client = None
    
    def _initialize_media_state(self):
        """Initialise l'état de média pour la gestion des erreurs répétées"""
        # Compteur d'erreurs consécutives pour les opérations média
        self.consecutive_media_errors = 0
        # Nombre maximum d'erreurs consécutives avant temporisation
        self.max_consecutive_media_errors = 5
        # Horodatage de la dernière temporisation média
        self.last_media_backoff_time = 0
        # Durée de temporisation en secondes (augmente progressivement)
        self.current_media_backoff_duration = 5
        # Durée maximale de temporisation média
        self.max_media_backoff_duration = 60
    
    def _should_attempt_media_operation(self):
        """Détermine si une opération média doit être tentée ou si on est en période de temporisation
        
        Returns:
            bool: True si on peut tenter une opération média, False si on est en temporisation
        """
        current_time = time.time()
        
        # Si nous sommes encore en période de temporisation
        if self.consecutive_media_errors >= self.max_consecutive_media_errors:
            time_since_backoff = current_time - self.last_media_backoff_time
            
            # Si la période de temporisation n'est pas encore terminée
            if time_since_backoff < self.current_media_backoff_duration:
                return False
            
            # La période de temporisation est terminée, on réinitialise le compteur
            self.consecutive_media_errors = 0
            logger.info(f"Période de temporisation média terminée après {self.current_media_backoff_duration} secondes. Reprise des opérations média.")
            
            # On augmente la durée de la prochaine temporisation, avec un maximum
            self.current_media_backoff_duration = min(self.current_media_backoff_duration * 2, self.max_media_backoff_duration)
        
        return True
    
    def _handle_media_success(self):
        """Appelé quand une opération média réussit"""
        # Réinitialiser le compteur d'erreurs et la durée de temporisation
        if self.consecutive_media_errors > 0:
            self.consecutive_media_errors = 0
            self.current_media_backoff_duration = 5  # Réinitialiser à la valeur initiale
            logger.info("Opération média réussie, réinitialisation du compteur d'erreurs")
    
    def _handle_media_error(self, error_message):
        """Gère une erreur d'opération média et met à jour l'état
        
        Args:
            error_message (str): Message d'erreur
        
        Returns:
            bool: True si c'est la première erreur, False si c'est une erreur répétée
        """
        self.consecutive_media_errors += 1
        
        # Si c'est la première erreur ou une erreur intermédiaire
        if self.consecutive_media_errors < self.max_consecutive_media_errors:
            return True
        
        # Si on atteint le seuil d'erreurs consécutives
        if self.consecutive_media_errors == self.max_consecutive_media_errors:
            self.last_media_backoff_time = time.time()
            logger.warning(
                f"Atteint {self.max_consecutive_media_errors} erreurs média consécutives. "
                f"Temporisation pendant {self.current_media_backoff_duration} secondes. "
                f"Erreur : {error_message}"
            )
            return True
        
        # On est au-delà du seuil, on ne log pas cette erreur
        return False
    
    def get_media_sources(self):
        """Récupère la liste des sources média disponibles dans OBS
        
        Returns:
            list: Liste des sources média
        """
        with self.ws_lock:
            if not self.connected or not self.client:
                logger.warning("Non connecté à OBS, impossible de récupérer les sources média")
                return []
            
            # Vérifier si on est en période de temporisation
            if not self._should_attempt_media_operation():
                return []
                
            try:
                # Utiliser la méthode GetInputList() pour récupérer toutes les sources
                sources_response = self.client.get_input_list()
                
                # Filtrer les sources média
                media_types = ['ffmpeg_source', 'vlc_source', 'media_source']
                media_sources = []
                
                # Parcourir les sources et filtrer les types média
                if hasattr(sources_response, 'inputs'):
                    for source in sources_response.inputs:
                        kind = None
                        name = None
                        
                        # Extraire les propriétés selon la structure
                        if hasattr(source, 'inputKind'):
                            kind = source.inputKind
                        elif hasattr(source, 'kind'):
                            kind = source.kind
                        
                        if hasattr(source, 'inputName'):
                            name = source.inputName
                        elif hasattr(source, 'name'):
                            name = source.name
                        
                        # Ajouter si c'est une source média
                        if kind in media_types and name:
                            media_sources.append(name)
                
                self._handle_media_success()
                logger.info(f"Sources média trouvées: {media_sources}")
                return media_sources
            
            except Exception as e:
                error_message = str(e)
                if self._handle_media_error(error_message):
                    logger.error(f"Erreur lors de la récupération des sources média: {error_message}")
                return []
    
    def get_media_properties(self, source_name):
        """Récupère les propriétés d'une source média
        
        Args:
            source_name (str): Nom de la source média
        
        Returns:
            dict: Propriétés de la source média ou None en cas d'erreur
        """
        with self.ws_lock:
            if not self.connected or not self.client:
                logger.warning("Non connecté à OBS, impossible de récupérer les propriétés média")
                return None
            
            # Vérifier si on est en période de temporisation
            if not self._should_attempt_media_operation():
                return None
                
            try:
                # Récupérer les paramètres de la source
                settings_response = self.client.get_input_settings(source_name)
                
                # Récupérer l'état du média
                try:
                    media_info = self.client.get_media_input_status(source_name)
                    
                    # Extraire les données de média
                    media_state = {
                        'duration': getattr(media_info, 'media_duration', 0),
                        'position': getattr(media_info, 'media_cursor', 0),
                        'playing': getattr(media_info, 'media_state', '') == 'OBS_MEDIA_STATE_PLAYING'
                    }
                    
                    # Mettre à jour l'état de la source
                    if source_name in self.media_states:
                        self.media_states[source_name].update({
                            'duration': media_state['duration'],
                            'position': media_state['position'],
                            'playing': media_state['playing'],
                            'last_update': time.time()
                        })
                    else:
                        self.media_states[source_name] = {
                            'duration': media_state['duration'],
                            'position': media_state['position'],
                            'playing': media_state['playing'],
                            'last_update': time.time()
                        }
                    
                    # Combiner les informations
                    properties = {
                        'settings': settings_response,
                        'state': media_state,
                        'duration': media_state['duration'],
                        'position': media_state['position'],
                        'playing': media_state['playing']
                    }
                    
                    self._handle_media_success()
                    return properties
                
                except Exception as media_error:
                    logger.warning(f"Erreur lors de la récupération de l'état du média: {media_error}")
                    # Retourner au moins les paramètres
                    return {'settings': settings_response}
            
            except Exception as e:
                error_message = str(e)
                if self._handle_media_error(error_message):
                    logger.error(f"Erreur lors de la récupération des propriétés média: {error_message}")
                return None
    
    def control_media(self, source_name, action, position=None):
        """Contrôle la lecture d'un média
        
        Args:
            source_name (str): Nom de la source média
            action (str): Action à effectuer ('play', 'pause', 'restart', 'stop', 'seek')
            position (float, optional): Position en secondes pour l'action 'seek'. Défaut à None.
        
        Returns:
            bool: True si l'action a été effectuée avec succès, False sinon
        """
        with self.ws_lock:
            if not self.connected or not self.client:
                logger.warning("Non connecté à OBS, impossible de contrôler le média")
                return False
            
            # Vérifier si on est en période de temporisation
            if not self._should_attempt_media_operation():
                return False
                
            try:
                if action == 'play':
                    self.client.trigger_media_input_action(source_name, 'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY')
                elif action == 'pause':
                    self.client.trigger_media_input_action(source_name, 'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE')
                elif action == 'restart':
                    self.client.trigger_media_input_action(source_name, 'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART')
                elif action == 'stop':
                    self.client.trigger_media_input_action(source_name, 'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP')
                elif action == 'seek' and position is not None:
                    # Pour seek, il faut d'abord vérifier si c'est possible
                    self.client.scrub_media_input_cursor(source_name, float(position))
                else:
                    logger.warning(f"Action média non reconnue: {action}")
                    return False
                
                # Mettre à jour l'état du média
                if source_name in self.media_states:
                    if action == 'play':
                        self.media_states[source_name]['playing'] = True
                    elif action == 'pause' or action == 'stop':
                        self.media_states[source_name]['playing'] = False
                    elif action == 'restart':
                        self.media_states[source_name]['playing'] = True
                        self.media_states[source_name]['position'] = 0
                    elif action == 'seek':
                        self.media_states[source_name]['position'] = position
                    
                    self.media_states[source_name]['last_update'] = time.time()
                
                self._handle_media_success()
                return True
            
            except Exception as e:
                error_message = str(e)
                if self._handle_media_error(error_message):
                    logger.error(f"Erreur lors du contrôle du média: {error_message}")
                return False
    
    def get_media_time(self, source_name):
        """Récupère le temps de lecture actuel d'un média
        
        Args:
            source_name (str): Nom de la source média
        
        Returns:
            dict: Informations de temps du média
        """
        with self.ws_lock:
            if not self.connected or not self.client:
                logger.warning("Non connecté à OBS, impossible de récupérer le temps média")
                
                # Si l'état est déjà enregistré, retourner les dernières valeurs connues
                if source_name in self.media_states:
                    return {
                        'currentTime': self.media_states[source_name]['position'],
                        'totalTime': self.media_states[source_name]['duration'],
                        'isPlaying': self.media_states[source_name]['playing']
                    }
                
                return None
            
            # Vérifier si on est en période de temporisation
            if not self._should_attempt_media_operation():
                # Retourner les dernières valeurs connues si disponibles
                if source_name in self.media_states:
                    return {
                        'currentTime': self.media_states[source_name]['position'],
                        'totalTime': self.media_states[source_name]['duration'],
                        'isPlaying': self.media_states[source_name]['playing']
                    }
                return None
                
            try:
                # Récupérer l'état du média avec get_media_input_status
                media_info = self.client.get_media_input_status(source_name)
                
                # Extraire les valeurs en utilisant getattr avec valeurs par défaut
                current_time = getattr(media_info, 'media_cursor', 0)
                total_time = getattr(media_info, 'media_duration', 0)
                media_state = getattr(media_info, 'media_state', '')
                is_playing = media_state == 'OBS_MEDIA_STATE_PLAYING'
                
                # Mettre à jour l'état de la source
                if source_name in self.media_states:
                    self.media_states[source_name].update({
                        'position': current_time,
                        'duration': total_time,
                        'playing': is_playing,
                        'last_update': time.time()
                    })
                else:
                    self.media_states[source_name] = {
                        'position': current_time,
                        'duration': total_time,
                        'playing': is_playing,
                        'last_update': time.time()
                    }
                
                self._handle_media_success()
                return {
                    'currentTime': current_time,
                    'totalTime': total_time,
                    'isPlaying': is_playing
                }
            
            except Exception as e:
                error_message = str(e)
                if self._handle_media_error(error_message):
                    logger.error(f"Erreur lors de la récupération du temps média: {error_message}")
                
                # Si l'état est déjà enregistré, retourner les dernières valeurs connues
                if source_name in self.media_states:
                    return {
                        'currentTime': self.media_states[source_name]['position'],
                        'totalTime': self.media_states[source_name]['duration'],
                        'isPlaying': self.media_states[source_name]['playing']
                    }
                
                return None
    
    def disconnect(self):
        """Déconnecte du serveur OBS WebSocket"""
        with self.ws_lock:
            if self.client:
                try:
                    # Pas besoin d'appeler disconnect() explicitement avec obsws_python
                    pass
                except Exception as e:
                    logger.error(f"Erreur lors de la déconnexion: {str(e)}")
                
                self.client = None
                self.connected = False
                logger.info("Déconnecté du gestionnaire de médias OBS")
