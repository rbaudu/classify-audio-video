import logging
import time
import threading
from obswebsocket import obsws, requests, events
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image

# Import de la configuration
from server import OBS_HOST, OBS_PORT, OBS_PASSWORD, VIDEO_SOURCE_NAME

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
        self.reconnect_interval = 5  # secondes
        self.should_reconnect = True
        
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
                
                # Se connecter à OBS
                self.ws.connect()
                self.connected = True
                self.logger.info("Connecté à OBS avec succès")
                
                # Récupérer les sources disponibles
                self._refresh_sources()
                
                return True
            except Exception as e:
                self.logger.error(f"Erreur lors de la connexion à OBS: {str(e)}")
                self.connected = False
                
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
    
    def _reconnect_loop(self):
        """
        Boucle pour tenter de se reconnecter à OBS à intervalles réguliers
        """
        while self.should_reconnect and not self.connected:
            self.logger.info(f"Tentative de reconnexion à OBS dans {self.reconnect_interval} secondes...")
            time.sleep(self.reconnect_interval)
            self.connect()
    
    def _refresh_sources(self):
        """
        Rafraîchit la liste des sources disponibles dans OBS
        """
        with self.ws_lock:
            if not self.connected:
                return
            
            try:
                # Récupérer la liste des sources
                self.logger.info("Tentative de récupération des sources via GetSourcesList()")
                sources_response = self.ws.call(requests.GetSourcesList())
                self.logger.info(f"Réponse de GetSourcesList(): {sources_response.datain}")
                sources = sources_response.getSources()
                
                # Filtrer les sources vidéo et média
                self.video_sources = [s for s in sources if self._is_video_source(s['typeId'])]
                self.media_sources = [s for s in sources if self._is_media_source(s['typeId'])]
                
                self.logger.info(f"Sources vidéo trouvées: {[s['name'] for s in self.video_sources]}")
                self.logger.info(f"Sources média trouvées: {[s['name'] for s in self.media_sources]}")
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération des sources: {str(e)}")
                # Vérifier si l'erreur est liée à la connexion
                if "socket is already closed" in str(e):
                    self.logger.warning("Socket fermé. Tentative de reconnecter...")
                    self.connected = False
                    if not self.reconnect_thread or not self.reconnect_thread.is_alive():
                        self.reconnect_thread = threading.Thread(target=self._reconnect_loop)
                        self.reconnect_thread.daemon = True
                        self.reconnect_thread.start()
                    return
                    
                # Alternative: tenter d'utiliser GetInputList pour les versions récentes d'OBS
                try:
                    self.logger.info("Tentative de récupération des sources via GetInputList() (OBS 28+)")
                    sources_response = self.ws.call(requests.GetInputList())
                    sources = sources_response.getInputs()
                    
                    self.logger.info(f"Sources récupérées via GetInputList(): {sources}")
                    
                    # Filtrer les sources vidéo et média
                    self.video_sources = []
                    self.media_sources = []
                    
                    for source in sources:
                        kind = source.get('inputKind', '')
                        name = source.get('inputName', '')
                        
                        # Adapter les types aux nouvelles conventions OBS v28+
                        if kind in ['dshow_input', 'monitor_capture', 'window_capture', 'game_capture',
                                  'v4l2_input', 'av_capture_input', 'image_source', 'color_source',
                                  'browser_source', 'video_capture_device', 'display_capture']:
                            self.video_sources.append({'name': name, 'typeId': kind})
                        
                        if kind in ['ffmpeg_source', 'vlc_source', 'media_source', 'media']:
                            self.media_sources.append({'name': name, 'typeId': kind})
                    
                    self.logger.info(f"Sources vidéo trouvées (via GetInputList): {[s['name'] for s in self.video_sources]}")
                    self.logger.info(f"Sources média trouvées (via GetInputList): {[s['name'] for s in self.media_sources]}")
                except Exception as e2:
                    self.logger.error(f"Échec également avec GetInputList: {str(e2)}")
                    # Par défaut, créer au moins une source virtuelle pour pouvoir continuer
                    self.video_sources = [{'name': 'Default Video Source', 'typeId': 'unknown'}]
                    self.media_sources = []
    
    def is_connected(self):
        """
        Vérifie si la connexion à OBS est active
        
        Returns:
            bool: True si connecté, False sinon
        """
        with self.ws_lock:
            if not self.connected:
                return False
                
            try:
                # Effectuer un appel simple pour vérifier la connexion
                self.ws.call(requests.GetVersion())
                return True
            except Exception as e:
                self.logger.warning(f"La connexion à OBS semble interrompue: {str(e)}")
                self.connected = False
                
                # Lancer la reconnexion si nécessaire
                if not self.reconnect_thread or not self.reconnect_thread.is_alive():
                    self.reconnect_thread = threading.Thread(target=self._reconnect_loop)
                    self.reconnect_thread.daemon = True
                    self.reconnect_thread.start()
                    
                return False
    
    def _is_video_source(self, type_id):
        """
        Vérifie si un type de source est une source vidéo
        """
        video_types = [
            'dshow_input', 'monitor_capture', 'window_capture', 'game_capture',
            'v4l2_input', 'av_capture_input', 'image_source', 'color_source',
            'browser_source', 'video_capture_device', 'display_capture'
        ]
        return type_id in video_types
    
    def _is_media_source(self, type_id):
        """
        Vérifie si un type de source est une source média (fichier vidéo)
        """
        media_types = [
            'ffmpeg_source', 'vlc_source', 'media_source', 'media'
        ]
        return type_id in media_types
    
    def _on_switch_scene(self, event):
        """
        Callback pour l'événement de changement de scène
        """
        scene_name = event.getSceneName()
        self.logger.info(f"Scène active changée: {scene_name}")
        self._refresh_sources()
    
    def _on_stream_starting(self, event):
        """
        Callback pour l'événement de démarrage de stream
        """
        self.logger.info("Stream en cours de démarrage")
    
    def _on_stream_stopping(self, event):
        """
        Callback pour l'événement d'arrêt de stream
        """
        self.logger.info("Stream en cours d'arrêt")
    
    def _on_media_play(self, event):
        """
        Callback pour l'événement de lecture média
        """
        source_name = event.getSourceName()
        self.logger.info(f"Média démarré: {source_name}")
        if source_name in self.media_states:
            self.media_states[source_name]['playing'] = True
    
    def _on_media_pause(self, event):
        """
        Callback pour l'événement de pause média
        """
        source_name = event.getSourceName()
        self.logger.info(f"Média en pause: {source_name}")
        if source_name in self.media_states:
            self.media_states[source_name]['playing'] = False
    
    def _on_media_stop(self, event):
        """
        Callback pour l'événement d'arrêt média
        """
        source_name = event.getSourceName()
        self.logger.info(f"Média arrêté: {source_name}")
        if source_name in self.media_states:
            self.media_states[source_name]['playing'] = False
            self.media_states[source_name]['position'] = 0
    
    def _on_media_end(self, event):
        """
        Callback pour l'événement de fin média
        """
        source_name = event.getSourceName()
        self.logger.info(f"Média terminé: {source_name}")
        if source_name in self.media_states:
            self.media_states[source_name]['playing'] = False
            self.media_states[source_name]['position'] = 0
    
    def get_video_frame(self, source_name=None):
        """
        Récupère une image de la source vidéo spécifiée ou la source par défaut
        
        Args:
            source_name (str, optional): Nom de la source vidéo. Défaut à None (utilise VIDEO_SOURCE_NAME).
        
        Returns:
            numpy.ndarray: Image au format OpenCV (BGR) ou None en cas d'erreur
        """
        with self.ws_lock:
            # Vérifier la connexion et tenter de se reconnecter si nécessaire
            if not self.connected:
                if self.last_successful_frame is not None:
                    return self.last_successful_frame
                self.logger.warning("Non connecté à OBS, impossible de récupérer une image")
                # Générer une image noire de remplacement pour éviter les erreurs en aval
                dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                return dummy_frame
            
            if not source_name:
                source_name = VIDEO_SOURCE_NAME
            
            try:
                # Appel à l'API OBS pour récupérer une capture d'écran de la source
                self.logger.info(f"Tentative de capture d'image pour la source: {source_name}")
                response = self.ws.call(requests.TakeSourceScreenshot(
                    sourceName=source_name,
                    embedPictureFormat="png",
                    width=640,  # Résolution réduite pour des performances meilleures
                    height=360
                ))
                
                # Récupérer les données de l'image en base64
                img_data = response.getImg()
                
                # Supprimer le préfixe data:image/png;base64,
                if "base64," in img_data:
                    img_data = img_data.split("base64,")[1]
                
                # Décoder l'image
                img_bytes = base64.b64decode(img_data)
                img_buffer = BytesIO(img_bytes)
                img = Image.open(img_buffer)
                
                # Convertir en format OpenCV
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                self.current_frame = frame
                self.last_successful_frame = frame
                return frame
            except Exception as e:
                self.logger.error(f"Erreur lors de la capture d'image: {str(e)}")
                
                # Si l'erreur indique que le socket est fermé, tenter de se reconnecter
                if "socket is already closed" in str(e):
                    self.logger.warning("Socket fermé. Tentative de reconnecter...")
                    self.connected = False
                    if not self.reconnect_thread or not self.reconnect_thread.is_alive():
                        self.reconnect_thread = threading.Thread(target=self._reconnect_loop)
                        self.reconnect_thread.daemon = True
                        self.reconnect_thread.start()
                    
                    # Retourner la dernière frame réussie si disponible
                    if self.last_successful_frame is not None:
                        return self.last_successful_frame
                
                # Générer une image noire de remplacement pour éviter les erreurs en aval
                dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                self.logger.info("Génération d'une image noire de remplacement")
                return dummy_frame
    
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
                
                # Vérifier si la connexion est perdue
                if "socket is already closed" in str(e):
                    self.connected = False
                    self.logger.warning("Socket fermé. Tentative de reconnecter...")
                    if not self.reconnect_thread or not self.reconnect_thread.is_alive():
                        self.reconnect_thread = threading.Thread(target=self._reconnect_loop)
                        self.reconnect_thread.daemon = True
                        self.reconnect_thread.start()
                
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
                
                # Vérifier si la connexion est perdue
                if "socket is already closed" in str(e):
                    self.connected = False
                    self.logger.warning("Socket fermé. Tentative de reconnecter...")
                    if not self.reconnect_thread or not self.reconnect_thread.is_alive():
                        self.reconnect_thread = threading.Thread(target=self._reconnect_loop)
                        self.reconnect_thread.daemon = True
                        self.reconnect_thread.start()
                
                # Si l'état est déjà enregistré, retourner les dernières valeurs connues
                if source_name in self.media_states:
                    return {
                        'currentTime': self.media_states[source_name]['position'],
                        'totalTime': self.media_states[source_name]['duration'],
                        'isPlaying': self.media_states[source_name]['playing']
                    }
                
                return None
    
    def get_current_frame(self):
        """
        Récupère l'image actuelle de la source sélectionnée
        
        Returns:
            numpy.ndarray: Image au format OpenCV (BGR) ou None en cas d'erreur
        """
        if self.current_source:
            return self.get_video_frame(self.current_source)
        else:
            return self.get_video_frame()
