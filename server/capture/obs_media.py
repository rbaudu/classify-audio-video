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
            
            try:
                self._refresh_sources()
                return self.media_sources
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération des sources média: {str(e)}")
                
                # Vérifier si l'erreur est liée à la connexion
                if self._is_connection_error(str(e)):
                    self._handle_connection_lost()
                
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
                
                self.logger.info(f"Source média '{source_name}' sélectionnée")
                return True
            except Exception as e:
                self.logger.error(f"Erreur lors de la sélection de la source média: {str(e)}")
                
                # Vérifier si l'erreur est liée à la connexion
                if self._is_connection_error(str(e)):
                    self._handle_connection_lost()
                
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
                
                return properties
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération des propriétés média: {str(e)}")
                
                # Vérifier si l'erreur est liée à la connexion
                if self._is_connection_error(str(e)):
                    self._handle_connection_lost()
                
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
                
                return True
            except Exception as e:
                self.logger.error(f"Erreur lors du contrôle du média: {str(e)}")
                
                # Vérifier si l'erreur est liée à la connexion
                if self._is_connection_error(str(e)):
                    self._handle_connection_lost()
                
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
                
                return {
                    'currentTime': current_time,
                    'totalTime': total_time,
                    'isPlaying': is_playing
                }
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération du temps média: {str(e)}")
                
                # Vérifier si l'erreur est liée à la connexion
                if self._is_connection_error(str(e)):
                    self._handle_connection_lost()
                
                # Si l'état est déjà enregistré, retourner les dernières valeurs connues
                if source_name in self.media_states:
                    return {
                        'currentTime': self.media_states[source_name]['position'],
                        'totalTime': self.media_states[source_name]['duration'],
                        'isPlaying': self.media_states[source_name]['playing']
                    }
                
                return None
