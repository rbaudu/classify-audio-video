import logging
import cv2
import numpy as np
import base64
import time
import os
import tempfile
from io import BytesIO
from PIL import Image
from obswebsocket import requests

# Import de la configuration
from server import VIDEO_SOURCE_NAME

# Cette classe est définie partiellement, 
# elle est destinée à être importée dans OBSCapture dans obs_capture.py
class OBSSourcesMixin:
    """
    Mixin pour la gestion des sources OBS.
    Ces méthodes sont intégrées à la classe OBSCapture.
    """
    
    def _initialize_capture_state(self):
        """
        Initialise l'état de capture pour la gestion des erreurs répétées
        """
        # Compteur d'erreurs consécutives pour la capture vidéo
        self.consecutive_capture_errors = 0
        # Nombre maximum d'erreurs consécutives avant temporisation
        self.max_consecutive_errors = 5
        # Horodatage de la dernière temporisation
        self.last_backoff_time = 0
        # Durée de temporisation en secondes (augmente progressivement)
        self.current_backoff_duration = 5
        # Durée maximale de temporisation
        self.max_backoff_duration = 60
        
        # Pour la méthode de capture par fichier temporaire
        self.temp_dir = tempfile.gettempdir()
        self.temp_image_path = os.path.join(self.temp_dir, "obs_capture_temp.png")
    
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
                if self._is_connection_error(str(e)):
                    self.logger.warning("Connexion perdue. Tentative de reconnecter...")
                    self._handle_connection_lost()
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
                    # Vérifier si l'erreur est liée à la connexion
                    if self._is_connection_error(str(e2)):
                        self.logger.warning("Connexion perdue. Tentative de reconnecter...")
                        self._handle_connection_lost()
                        return
                    # Par défaut, créer au moins une source virtuelle pour pouvoir continuer
                    self.video_sources = [{'name': VIDEO_SOURCE_NAME, 'typeId': 'unknown'}]
                    self.media_sources = []
    
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
    
    def _should_attempt_capture(self):
        """
        Détermine si une tentative de capture doit être effectuée ou si on est en période de temporisation
        
        Returns:
            bool: True si on peut tenter une capture, False si on est en temporisation
        """
        current_time = time.time()
        
        # Si nous sommes encore en période de temporisation
        if self.consecutive_capture_errors >= self.max_consecutive_errors:
            time_since_backoff = current_time - self.last_backoff_time
            
            # Si la période de temporisation n'est pas encore terminée
            if time_since_backoff < self.current_backoff_duration:
                return False
            
            # La période de temporisation est terminée, on réinitialise le compteur
            self.consecutive_capture_errors = 0
            self.logger.info(f"Période de temporisation terminée après {self.current_backoff_duration} secondes. Reprise des tentatives de capture.")
            
            # On augmente la durée de la prochaine temporisation, avec un maximum
            self.current_backoff_duration = min(self.current_backoff_duration * 2, self.max_backoff_duration)
        
        return True
    
    def _handle_capture_success(self):
        """
        Appelé quand une capture réussit
        """
        # Réinitialiser le compteur d'erreurs et la durée de temporisation
        if self.consecutive_capture_errors > 0:
            self.consecutive_capture_errors = 0
            self.current_backoff_duration = 5  # Réinitialiser à la valeur initiale
            self.logger.info("Capture réussie, réinitialisation du compteur d'erreurs")
    
    def _handle_capture_error(self, error_message):
        """
        Gère une erreur de capture et met à jour l'état
        
        Args:
            error_message (str): Message d'erreur
        
        Returns:
            bool: True si c'est la première erreur, False si c'est une erreur répétée
        """
        self.consecutive_capture_errors += 1
        
        # Si c'est la première erreur ou une erreur intermédiaire
        if self.consecutive_capture_errors < self.max_consecutive_errors:
            return True
        
        # Si on atteint le seuil d'erreurs consécutives
        if self.consecutive_capture_errors == self.max_consecutive_errors:
            self.last_backoff_time = time.time()
            self.logger.warning(
                f"Atteint {self.max_consecutive_errors} erreurs consécutives. "
                f"Temporisation pendant {self.current_backoff_duration} secondes. "
                f"Erreur : {error_message}"
            )
            return True
        
        # On est au-delà du seuil, on ne log pas cette erreur
        return False
    
    def _capture_to_file(self, source_name):
        """
        Nouvelle méthode pour capturer l'image d'une source vers un fichier temporaire
        
        Args:
            source_name (str): Nom de la source à capturer
            
        Returns:
            bool: True si la capture a réussi, False sinon
        """
        try:
            self.logger.info(f"Tentative de capture vers fichier pour: {source_name}")
            
            # Supprimer le fichier temporaire s'il existe déjà
            if os.path.exists(self.temp_image_path):
                try:
                    os.remove(self.temp_image_path)
                except Exception as e:
                    self.logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")
            
            # Récupérer la liste des scènes
            scenes_response = self.ws.call(requests.GetSceneList())
            current_scene = scenes_response.getCurrentScene()
            
            self.logger.info(f"Scène courante: {current_scene}")
            
            # Utiliser SaveSourceScreenshot pour enregistrer l'image
            response = self.ws.call(requests.SaveSourceScreenshot(
                sourceName=source_name,
                filePath=self.temp_image_path,
                fileFormat="png",
                width=640,
                height=360,
                compressionQuality=-1  # Utiliser la qualité par défaut
            ))
            
            self.logger.info(f"Réponse SaveSourceScreenshot: {response.status}")
            
            # Vérifier si le fichier a été créé
            if os.path.exists(self.temp_image_path):
                file_size = os.path.getsize(self.temp_image_path)
                self.logger.info(f"Fichier temporaire créé: {self.temp_image_path}, taille: {file_size} octets")
                return True
            else:
                self.logger.warning(f"Fichier temporaire non créé: {self.temp_image_path}")
                return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la capture vers fichier: {e}")
            return False
    
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
            
            # Vérifier si on doit tenter une capture ou si on est en période de temporisation
            if not self._should_attempt_capture():
                # Si on est en temporisation, on retourne la dernière image réussie ou une image noire
                if self.last_successful_frame is not None:
                    return self.last_successful_frame
                dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                return dummy_frame
            
            try:
                # Méthode 1: Capture vers fichier (OBS 31.x)
                if self._capture_to_file(source_name):
                    try:
                        # Charger l'image depuis le fichier
                        frame = cv2.imread(self.temp_image_path)
                        if frame is not None and frame.size > 0:
                            self.logger.info(f"Image chargée avec succès: {frame.shape}")
                            self._handle_capture_success()
                            self.current_frame = frame
                            self.last_successful_frame = frame
                            return frame
                        else:
                            self.logger.warning(f"Image chargée vide ou invalide")
                    except Exception as e:
                        self.logger.error(f"Erreur lors du chargement de l'image: {e}")
                
                # Méthode 2: Utiliser TakeSourceScreenshot (OBS 28+)
                self.logger.info(f"Tentative de capture avec TakeSourceScreenshot pour: {source_name}")
                try:
                    response = self.ws.call(requests.TakeSourceScreenshot(
                        sourceName=source_name,
                        embedPictureFormat="png",
                        width=640,
                        height=360
                    ))
                    
                    # OBS 31.x peut ne pas renvoyer les attributs 'img' ou 'imageData'
                    # Essayons de lire la réponse directement depuis data
                    img_data = None
                    
                    if hasattr(response, 'data') and isinstance(response.data, dict) and 'imageData' in response.data:
                        img_data = response.data['imageData']
                    elif hasattr(response, 'img'):
                        img_data = response.img
                    elif hasattr(response, 'imageData'):
                        img_data = response.imageData
                    else:
                        # Si on ne trouve pas les données d'image, loguer la structure de la réponse
                        self.logger.info(f"Structure de la réponse TakeSourceScreenshot: {dir(response)}")
                        for attr in dir(response):
                            if not attr.startswith('_') and not callable(getattr(response, attr)):
                                value = getattr(response, attr)
                                self.logger.info(f"Attribut {attr}: {type(value)} - {str(value)[:100]}")
                        
                        raise Exception("Format de réponse non reconnu pour TakeSourceScreenshot")
                
                except Exception as e:
                    # Méthode 3: Essayer avec GetSourceScreenshot (OBS 31.x)
                    self.logger.info(f"Tentative avec GetSourceScreenshot pour: {source_name}")
                    response = self.ws.call(requests.GetSourceScreenshot(
                        sourceName=source_name,
                        imageFormat="png",
                        imageWidth=640,
                        imageHeight=360
                    ))
                    self.logger.info(f"Structure de la réponse GetSourceScreenshot: {dir(response)}")
                    for attr in dir(response):
                        if not attr.startswith('_') and not callable(getattr(response, attr)):
                            value = getattr(response, attr)
                            self.logger.info(f"Attribut {attr}: {type(value)} - {str(value)[:100]}")
                    
                    img_data = None
                    if hasattr(response, 'getImageData') and callable(response.getImageData):
                        img_data = response.getImageData()
                    elif hasattr(response, 'data') and isinstance(response.data, dict):
                        img_data = response.data.get('imageData')
                
                # Vérifier si img_data est valide
                if not img_data:
                    if self._handle_capture_error("Réponse d'image vide reçue d'OBS"):
                        self.logger.error("Réponse d'image vide reçue d'OBS")
                    
                    # Retourner la dernière frame réussie si disponible
                    if self.last_successful_frame is not None:
                        return self.last_successful_frame
                    
                    # Générer une image noire de remplacement pour éviter les erreurs en aval
                    dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                    return dummy_frame
                
                # Supprimer le préfixe data:image/png;base64,
                if isinstance(img_data, str) and "base64," in img_data:
                    img_data = img_data.split("base64,")[1]
                
                # Décoder l'image
                img_bytes = base64.b64decode(img_data)
                img_buffer = BytesIO(img_bytes)
                img = Image.open(img_buffer)
                
                # Convertir en format OpenCV
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # La capture a réussi
                self._handle_capture_success()
                
                self.current_frame = frame
                self.last_successful_frame = frame
                return frame
            except Exception as e:
                error_message = str(e)
                # Si l'erreur indique une perte de connexion, tenter de se reconnecter
                if self._is_connection_error(error_message):
                    self.logger.warning("Connexion perdue lors de la capture d'image. Tentative de reconnecter...")
                    self._handle_connection_lost()
                    
                    # Retourner la dernière frame réussie si disponible
                    if self.last_successful_frame is not None:
                        return self.last_successful_frame
                else:
                    # Pour les autres erreurs, gérer la temporisation
                    if self._handle_capture_error(error_message):
                        self.logger.error(f"Erreur lors de la capture d'image: {error_message}")
                
                # Générer une image noire de remplacement pour éviter les erreurs en aval
                dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                return dummy_frame
    
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
