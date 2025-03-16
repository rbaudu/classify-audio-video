import logging
import cv2
import numpy as np
import base64
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
                
                # Ajout de logs de débogage pour diagnostiquer l'erreur 'img'
                self.logger.info(f"Réponse brute de TakeSourceScreenshot: {response.datain}")
                
                # Récupérer les données de l'image en base64
                img_data = response.getImg()
                self.logger.info(f"Type de img_data: {type(img_data)}, Longueur: {len(str(img_data)) if img_data else 'None'}")
                
                # Vérifier si img_data est valide
                if not img_data:
                    raise ValueError("Réponse d'image vide reçue d'OBS")
                
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
                
                # Si l'erreur indique une perte de connexion, tenter de se reconnecter
                if self._is_connection_error(str(e)):
                    self.logger.warning("Connexion perdue lors de la capture d'image. Tentative de reconnecter...")
                    self._handle_connection_lost()
                    
                    # Retourner la dernière frame réussie si disponible
                    if self.last_successful_frame is not None:
                        return self.last_successful_frame
                
                # Générer une image noire de remplacement pour éviter les erreurs en aval
                dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                self.logger.info("Génération d'une image noire de remplacement")
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
