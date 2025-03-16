import logging
import time
from obswebsocket import requests

# Cette classe est définie partiellement, 
# elle est destinée à être importée dans OBSCapture dans obs_capture.py
class OBSMediaMixin:
    """
    Mixin pour la gestion des médias OBS.
    Ces méthodes sont intégrées à la classe OBSCapture.
    """
    
    def _initialize_media_state(self):
        """
        Initialise l'état de média pour la gestion des erreurs répétées
        """
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
        """
        Détermine si une opération média doit être tentée ou si on est en période de temporisation
        
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
            self.logger.info(f"Période de temporisation média terminée après {self.current_media_backoff_duration} secondes. Reprise des opérations média.")
            
            # On augmente la durée de la prochaine temporisation, avec un maximum
            self.current_media_backoff_duration = min(self.current_media_backoff_duration * 2, self.max_media_backoff_duration)
        
        return True
    
    def _handle_media_success(self):
        """
        Appelé quand une opération média réussit
        """
        # Réinitialiser le compteur d'erreurs et la durée de temporisation
        if self.consecutive_media_errors > 0:
            self.consecutive_media_errors = 0
            self.current_media_backoff_duration = 5  # Réinitialiser à la valeur initiale
            self.logger.info("Opération média réussie, réinitialisation du compteur d'erreurs")
    
    def _handle_media_error(self, error_message):
        """
        Gère une erreur d'opération média et met à jour l'état
        
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
            self.logger.warning(
                f"Atteint {self.max_consecutive_media_errors} erreurs média consécutives. "
                f"Temporisation pendant {self.current_media_backoff_duration} secondes. "
                f"Erreur : {error_message}"
            )
            return True
        
        # On est au-delà du seuil, on ne log pas cette erreur
        return False
    
    def get_media_sources(self):
        """
        Récupère la liste des sources média disponibles dans OBS
        
        Returns:
            list: Liste des sources média
        """
        with self.ws_lock:
            if not self.connected:
                self.logger.warning("Non connecté à OBS, impossible de récupérer les sources média")
                return []
            
            # Vérifier si on est en période de temporisation
            if not self._should_attempt_media_operation():
                return []
                
            try:
                self._refresh_sources()
                self._handle_media_success()
                return self.media_sources
            except Exception as e:
                error_message = str(e)
                # Vérifier si l'erreur est liée à la connexion
                if self._is_connection_error(error_message):
                    self._handle_connection_lost()
                else:
                    # Pour les autres erreurs, gérer la temporisation
                    if self._handle_media_error(error_message):
                        self.logger.error(f"Erreur lors de la récupération des sources média: {error_message}")
                
                return []
    
    def select_media_source(self, source_name):
        """
        Sélectionne une source média spécifique pour l'analyse
        
        Args:
            source_name (str): Nom de la source média
        
        Returns:
            bool: True si la source a été sélectionnée avec succès, False sinon
        """
        with self.ws_lock:
            if not self.connected:
                self.logger.warning("Non connecté à OBS, impossible de sélectionner une source média")
                return False
            
            # Vérifier si on est en période de temporisation
            if not self._should_attempt_media_operation():
                return False
                
            try:
                # Vérifier que la source existe
                found = False
                for source in self.media_sources:
                    if source['name'] == source_name:
                        found = True
                        break
                
                if not found:
                    self.logger.warning(f"Source média '{source_name}' non trouvée")
                    return False
                
                # Enregistrer la source actuelle
                self.current_source = source_name
                
                # Initialiser l'état de la source si nécessaire
                if source_name not in self.media_states:
                    self.media_states[source_name] = {
                        'playing': False,
                        'position': 0,
                        'duration': 0,
                        'last_update': time.time()
                    }
                
                # Récupérer les propriétés de la source
                self.get_media_properties(source_name)
                
                self._handle_media_success()
                self.logger.info(f"Source média '{source_name}' sélectionnée")
                return True
            except Exception as e:
                error_message = str(e)
                # Vérifier si l'erreur est liée à la connexion
                if self._is_connection_error(error_message):
                    self._handle_connection_lost()
                else:
                    # Pour les autres erreurs, gérer la temporisation
                    if self._handle_media_error(error_message):
                        self.logger.error(f"Erreur lors de la sélection de la source média: {error_message}")
                
                return False
    
    def get_media_properties(self, source_name):
        """
        Récupère les propriétés d'une source média
        
        Args:
            source_name (str): Nom de la source média
        
        Returns:
            dict: Propriétés de la source média ou None en cas d'erreur
        """
        with self.ws_lock:
            if not self.connected:
                self.logger.warning("Non connecté à OBS, impossible de récupérer les propriétés média")
                return None
            
            # Vérifier si on est en période de temporisation
            if not self._should_attempt_media_operation():
                return None
                
            try:
                # Récupérer les paramètres de la source
                response = self.ws.call(requests.GetSourceSettings(sourceName=source_name))
                settings = response.getSourceSettings()
                
                # Récupérer l'état du média
                media_state_response = self.ws.call(requests.GetMediaState(sourceName=source_name))
                media_state = {
                    'duration': media_state_response.getMediaDuration(),
                    'position': media_state_response.getMediaTime(),
                    'playing': media_state_response.getMediaState() == 'OBS_MEDIA_STATE_PLAYING'
                }
                
                # Mettre à jour l'état de la source
                if source_name in self.media_states:
                    self.media_states[source_name].update({
                        'duration': media_state['duration'],
                        'position': media_state['position'],
                        'playing': media_state['playing'],
                        'last_update': time.time()
                    })
                
                # Combiner les informations
                properties = {
                    'settings': settings,
                    'state': media_state,
                    'duration': media_state['duration'],
                    'position': media_state['position'],
                    'playing': media_state['playing']
                }
                
                self._handle_media_success()
                return properties
            except Exception as e:
                error_message = str(e)
                # Vérifier si l'erreur est liée à la connexion
                if self._is_connection_error(error_message):
                    self._handle_connection_lost()
                else:
                    # Pour les autres erreurs, gérer la temporisation
                    if self._handle_media_error(error_message):
                        self.logger.error(f"Erreur lors de la récupération des propriétés média: {error_message}")
                
                return None
    
    def control_media(self, source_name, action, position=None):
        """
        Contrôle la lecture d'un média
        
        Args:
            source_name (str): Nom de la source média
            action (str): Action à effectuer ('play', 'pause', 'restart', 'stop', 'seek')
            position (float, optional): Position en secondes pour l'action 'seek'. Défaut à None.
        
        Returns:
            bool: True si l'action a été effectuée avec succès, False sinon
        """
        with self.ws_lock:
            if not self.connected:
                self.logger.warning("Non connecté à OBS, impossible de contrôler le média")
                return False
            
            # Vérifier si on est en période de temporisation
            if not self._should_attempt_media_operation():
                return False
                
            try:
                if action == 'play':
                    self.ws.call(requests.PlayPauseMedia(sourceName=source_name, playPause=False))
                elif action == 'pause':
                    self.ws.call(requests.PlayPauseMedia(sourceName=source_name, playPause=True))
                elif action == 'restart':
                    self.ws.call(requests.RestartMedia(sourceName=source_name))
                elif action == 'stop':
                    self.ws.call(requests.StopMedia(sourceName=source_name))
                elif action == 'seek' and position is not None:
                    self.ws.call(requests.SetMediaTime(sourceName=source_name, timestamp=float(position)))
                else:
                    self.logger.warning(f"Action média non reconnue: {action}")
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
                # Vérifier si l'erreur est liée à la connexion
                if self._is_connection_error(error_message):
                    self._handle_connection_lost()
                else:
                    # Pour les autres erreurs, gérer la temporisation
                    if self._handle_media_error(error_message):
                        self.logger.error(f"Erreur lors du contrôle du média: {error_message}")
                
                return False
    
    def get_media_time(self, source_name):
        """
        Récupère le temps de lecture actuel d'un média
        
        Args:
            source_name (str): Nom de la source média
        
        Returns:
            dict: Informations de temps du média
        """
        with self.ws_lock:
            if not self.connected:
                self.logger.warning("Non connecté à OBS, impossible de récupérer le temps média")
                
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
                # Récupérer l'état du média
                media_state_response = self.ws.call(requests.GetMediaState(sourceName=source_name))
                current_time = media_state_response.getMediaTime()
                total_time = media_state_response.getMediaDuration()
                is_playing = media_state_response.getMediaState() == 'OBS_MEDIA_STATE_PLAYING'
                
                # Mettre à jour l'état de la source
                if source_name in self.media_states:
                    self.media_states[source_name].update({
                        'position': current_time,
                        'duration': total_time,
                        'playing': is_playing,
                        'last_update': time.time()
                    })
                
                self._handle_media_success()
                return {
                    'currentTime': current_time,
                    'totalTime': total_time,
                    'isPlaying': is_playing
                }
            except Exception as e:
                error_message = str(e)
                # Vérifier si l'erreur est liée à la connexion
                if self._is_connection_error(error_message):
                    self._handle_connection_lost()
                else:
                    # Pour les autres erreurs, gérer la temporisation
                    if self._handle_media_error(error_message):
                        self.logger.error(f"Erreur lors de la récupération du temps média: {error_message}")
                
                # Si l'état est déjà enregistré, retourner les dernières valeurs connues
                if source_name in self.media_states:
                    return {
                        'currentTime': self.media_states[source_name]['position'],
                        'totalTime': self.media_states[source_name]['duration'],
                        'isPlaying': self.media_states[source_name]['playing']
                    }
                
                return None
