# -*- coding: utf-8 -*-
"""
Module de gestion des sources OBS pour OBS 31.0.2+
"""

import logging
import time
import threading
import os
import tempfile
import base64
import io
from PIL import Image
import obsws_python as obsws

logger = logging.getLogger(__name__)

class OBS31SourceManager:
    """
    Gestionnaire de sources pour OBS 31.0.2+
    """
    
    def __init__(self, host="localhost", port=4455, password=None):
        """Initialise le gestionnaire de sources OBS
        
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
        
        # Listes des sources
        self.video_sources = []
        self.media_sources = []
        
        # Source actuelle sélectionnée
        self.current_source = None
        
        # Verrou pour les opérations WebSocket
        self.ws_lock = threading.Lock()
        
        # Pour la capture par fichier
        self.temp_dir = tempfile.gettempdir()
        self.temp_image_path = os.path.join(self.temp_dir, "obs31_capture_temp.png")
        
        # Initialisation de la gestion des erreurs de capture
        self._initialize_capture_state()
        
        # Se connecter à OBS
        self._connect()
    
    def _connect(self):
        """Se connecte à OBS WebSocket"""
        try:
            with self.ws_lock:
                logger.info(f"Tentative de connexion au gestionnaire de sources OBS sur {self.host}:{self.port}")
                
                # Initialiser le client OBS WebSocket
                if self.password:
                    self.client = obsws.ReqClient(host=self.host, port=self.port, password=self.password)
                else:
                    self.client = obsws.ReqClient(host=self.host, port=self.port)
                
                # Vérifier la connexion
                version = self.client.get_version()
                logger.info(f"Gestionnaire de sources OBS connecté avec succès")
                logger.info(f"Version OBS: {version.obs_version}, WebSocket: {version.obs_web_socket_version}")
                
                # Marquer comme connecté
                self.connected = True
                
                # Récupérer les sources disponibles
                self._get_sources()
                
        except Exception as e:
            logger.error(f"Erreur de connexion au gestionnaire de sources OBS: {str(e)}")
            self.connected = False
            self.client = None
    
    def _initialize_capture_state(self):
        """Initialise l'état de capture pour la gestion des erreurs répétées"""
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
        
        # Dernière image capturée avec succès
        self.last_successful_frame = None
    
    def _get_sources(self):
        """Récupère les sources disponibles dans OBS"""
        with self.ws_lock:
            if not self.connected or not self.client:
                logger.error("Impossible de récupérer les sources: non connecté à OBS")
                return
            
            try:
                # Utiliser get_input_list pour obtenir toutes les sources
                inputs_response = self.client.get_input_list()
                
                # Types de sources vidéo et média
                video_types = ['dshow_input', 'v4l2_input', 'video_capture_device', 
                             'av_capture_input', 'game_capture', 'window_capture', 
                             'screen_capture', 'browser_source', 'image_source']
                
                media_types = ['ffmpeg_source', 'vlc_source', 'media_source']
                
                # Listes pour stocker les sources trouvées
                self.video_sources = []
                self.media_sources = []
                
                # Analyser la réponse pour extraire les sources
                if hasattr(inputs_response, 'inputs'):
                    all_inputs = inputs_response.inputs
                    
                    for input_data in all_inputs:
                        # Les noms des champs peuvent varier
                        kind = None
                        name = None
                        
                        # Extraire le type de source
                        if hasattr(input_data, 'inputKind'):
                            kind = input_data.inputKind
                        elif hasattr(input_data, 'kind'):
                            kind = input_data.kind
                        elif isinstance(input_data, dict):
                            kind = input_data.get('inputKind', input_data.get('kind', ''))
                        
                        # Extraire le nom de la source
                        if hasattr(input_data, 'inputName'):
                            name = input_data.inputName
                        elif hasattr(input_data, 'name'):
                            name = input_data.name
                        elif isinstance(input_data, dict):
                            name = input_data.get('inputName', input_data.get('name', ''))
                        
                        # Classer selon le type
                        if kind in video_types:
                            self.video_sources.append(name)
                        elif kind in media_types:
                            self.media_sources.append(name)
                    
                    logger.info(f"Sources vidéo trouvées: {self.video_sources}")
                    logger.info(f"Sources média trouvées: {self.media_sources}")
                else:
                    logger.warning("Format de réponse inattendu pour get_input_list()")
            
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des sources: {str(e)}")
    
    def _should_attempt_capture(self):
        """Détermine si une tentative de capture doit être effectuée ou si on est en période de temporisation
        
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
            logger.info(f"Période de temporisation terminée après {self.current_backoff_duration} secondes. Reprise des tentatives de capture.")
            
            # On augmente la durée de la prochaine temporisation, avec un maximum
            self.current_backoff_duration = min(self.current_backoff_duration * 2, self.max_backoff_duration)
        
        return True
    
    def _handle_capture_success(self):
        """Appelé quand une capture réussit"""
        # Réinitialiser le compteur d'erreurs et la durée de temporisation
        if self.consecutive_capture_errors > 0:
            self.consecutive_capture_errors = 0
            self.current_backoff_duration = 5  # Réinitialiser à la valeur initiale
            logger.info("Capture réussie, réinitialisation du compteur d'erreurs")
    
    def _handle_capture_error(self, error_message):
        """Gère une erreur de capture et met à jour l'état
        
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
            logger.warning(
                f"Atteint {self.max_consecutive_errors} erreurs consécutives. "
                f"Temporisation pendant {self.current_backoff_duration} secondes. "
                f"Erreur : {error_message}"
            )
            return True
        
        # On est au-delà du seuil, on ne log pas cette erreur
        return False
    
    def _create_dummy_image(self, source_name="Unknown", width=640, height=480):
        """Crée une image factice en cas d'erreur de capture
        
        Args:
            source_name (str): Nom de la source
            width (int): Largeur de l'image
            height (int): Hauteur de l'image
            
        Returns:
            PIL.Image.Image: Image factice
        """
        # Créer une image noire
        img = Image.new('RGB', (width, height), color=(0, 0, 0))
        
        # Ajouter du texte explicatif
        try:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            
            # Messages à afficher
            draw.text((20, height//2 - 30), f"Source: {source_name}", fill=(255, 255, 255))
            draw.text((20, height//2), "Erreur de capture", fill=(255, 255, 255))
            draw.text((20, height//2 + 30), "Vérifiez OBS Studio", fill=(255, 255, 255))
        except Exception as e:
            logger.warning(f"Impossible d'ajouter du texte à l'image factice: {e}")
        
        return img
    
    def _capture_to_file(self, source_name):
        """Capture l'image d'une source vers un fichier temporaire
        
        Args:
            source_name (str): Nom de la source à capturer
            
        Returns:
            bool: True si la capture a réussi, False sinon
        """
        try:
            with self.ws_lock:
                if not self.connected or not self.client:
                    logger.warning("Non connecté à OBS, impossible de capturer vers fichier")
                    return False
                
                logger.info(f"Tentative de capture vers fichier pour: {source_name}")
                
                # Supprimer le fichier temporaire s'il existe déjà
                if os.path.exists(self.temp_image_path):
                    try:
                        os.remove(self.temp_image_path)
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")
                
                # Utiliser save_source_screenshot pour capturer l'image
                self.client.save_source_screenshot(
                    source_name,
                    self.temp_image_path,
                    "png",
                    640,
                    480,
                    100  # Qualité
                )
                
                # Vérifier si le fichier a été créé
                if os.path.exists(self.temp_image_path):
                    file_size = os.path.getsize(self.temp_image_path)
                    logger.info(f"Fichier temporaire créé: {self.temp_image_path}, taille: {file_size} octets")
                    return True
                else:
                    logger.warning(f"Fichier temporaire non créé: {self.temp_image_path}")
                    return False
        
        except Exception as e:
            logger.error(f"Erreur lors de la capture vers fichier: {e}")
            return False
    
    def capture_screenshot(self, source_name=None):
        """Capture une image d'une source OBS
        
        Args:
            source_name (str, optional): Nom de la source. Par défaut None (utilise la première source disponible).
            
        Returns:
            PIL.Image.Image: Image capturée ou None en cas d'erreur
        """
        with self.ws_lock:
            if not self.connected or not self.client:
                logger.warning("Non connecté à OBS, impossible de capturer une image")
                if self.last_successful_frame is not None:
                    return self.last_successful_frame
                return self._create_dummy_image("Non connecté")
            
            # Si aucune source n'est spécifiée, utiliser la première source disponible
            if not source_name:
                if not self.video_sources:
                    logger.warning("Aucune source vidéo disponible")
                    return self._create_dummy_image("Aucune source")
                source_name = self.video_sources[0]
            
            # Vérifier si on doit tenter une capture ou si on est en période de temporisation
            if not self._should_attempt_capture():
                logger.info("En période de temporisation, utilisation de la dernière image")
                if self.last_successful_frame is not None:
                    return self.last_successful_frame
                return self._create_dummy_image(source_name)
            
            try:
                # Tentative 1: Utiliser get_source_screenshot
                logger.info(f"Tentative de capture avec get_source_screenshot pour: {source_name}")
                screenshot = self.client.get_source_screenshot(
                    source_name,
                    "png",
                    640,
                    480,
                    75  # Qualité
                )
                
                # Extraire les données d'image
                img_data = None
                if hasattr(screenshot, 'imageData'):
                    img_data = screenshot.imageData
                elif hasattr(screenshot, 'img'):
                    img_data = screenshot.img
                elif hasattr(screenshot, 'image'):
                    img_data = screenshot.image
                elif hasattr(screenshot, 'data'):
                    img_data = screenshot.data
                else:
                    # Parcourir tous les attributs pour trouver les données
                    for attr_name in dir(screenshot):
                        if attr_name.startswith('_'):
                            continue
                        
                        attr_value = getattr(screenshot, attr_name)
                        if isinstance(attr_value, str) and len(attr_value) > 100:
                            img_data = attr_value
                            logger.info(f"Données d'image trouvées dans l'attribut '{attr_name}'")
                            break
                
                # Si img_data est trouvé, décoder l'image
                if img_data:
                    # Traiter le préfixe data:image/png;base64, si présent
                    if isinstance(img_data, str) and ';base64,' in img_data:
                        img_data = img_data.split(';base64,')[1]
                    
                    # Décoder l'image base64
                    img_bytes = base64.b64decode(img_data)
                    img = Image.open(io.BytesIO(img_bytes))
                    
                    # La capture a réussi
                    self._handle_capture_success()
                    self.last_successful_frame = img
                    return img
                
                # Si la méthode directe échoue, essayer la capture vers fichier
                logger.info("Méthode directe échouée, tentative de capture vers fichier")
                if self._capture_to_file(source_name):
                    img = Image.open(self.temp_image_path)
                    self._handle_capture_success()
                    self.last_successful_frame = img
                    return img
                
                # Si toutes les méthodes échouent
                logger.error(f"Toutes les méthodes de capture ont échoué pour {source_name}")
                if self._handle_capture_error("Toutes les méthodes de capture ont échoué"):
                    pass  # L'erreur est déjà loguée
                
                # Retourner la dernière image réussie ou une image factice
                if self.last_successful_frame is not None:
                    return self.last_successful_frame
                return self._create_dummy_image(source_name)
            
            except Exception as e:
                error_message = str(e)
                if self._handle_capture_error(error_message):
                    logger.error(f"Erreur lors de la capture d'image: {error_message}")
                
                # Retourner la dernière image réussie ou une image factice
                if self.last_successful_frame is not None:
                    return self.last_successful_frame
                return self._create_dummy_image(source_name)
    
    def get_source_settings(self, source_name):
        """Récupère les paramètres d'une source OBS
        
        Args:
            source_name (str): Nom de la source
            
        Returns:
            dict: Paramètres de la source ou None en cas d'erreur
        """
        with self.ws_lock:
            if not self.connected or not self.client:
                logger.warning("Non connecté à OBS, impossible de récupérer les paramètres")
                return None
            
            try:
                # Récupérer les paramètres avec get_input_settings
                settings_response = self.client.get_input_settings(source_name)
                return settings_response
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des paramètres de {source_name}: {e}")
                return None
    
    def set_source_settings(self, source_name, settings):
        """Modifie les paramètres d'une source OBS
        
        Args:
            source_name (str): Nom de la source
            settings (dict): Nouveaux paramètres à appliquer
            
        Returns:
            bool: True si les paramètres ont été appliqués avec succès, False sinon
        """
        with self.ws_lock:
            if not self.connected or not self.client:
                logger.warning("Non connecté à OBS, impossible de modifier les paramètres")
                return False
            
            try:
                # Modifier les paramètres avec set_input_settings
                self.client.set_input_settings(source_name, settings, True)
                return True
            except Exception as e:
                logger.error(f"Erreur lors de la modification des paramètres de {source_name}: {e}")
                return False
    
    def get_current_scene(self):
        """Récupère la scène actuellement active dans OBS
        
        Returns:
            str: Nom de la scène active ou None en cas d'erreur
        """
        with self.ws_lock:
            if not self.connected or not self.client:
                logger.warning("Non connecté à OBS, impossible de récupérer la scène active")
                return None
            
            try:
                # Récupérer la scène active avec get_current_program_scene
                scene_response = self.client.get_current_program_scene()
                
                # Le nom de la scène est directement retourné comme string
                if isinstance(scene_response, str):
                    return scene_response
                
                # Si c'est un objet, chercher le nom
                if hasattr(scene_response, 'current_program_scene_name'):
                    return scene_response.current_program_scene_name
                elif hasattr(scene_response, 'name'):
                    return scene_response.name
                
                # En dernier recours, utiliser la représentation en chaîne
                return str(scene_response)
            
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de la scène active: {e}")
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
                logger.info("Déconnecté du gestionnaire de sources OBS")
