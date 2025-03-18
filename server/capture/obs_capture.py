# -*- coding: utf-8 -*-
"""
Module de capture vidéo via OBS WebSocket
"""

import logging
import time
import base64
import io
import os
import random
from PIL import Image, ImageDraw, ImageFont
import threading
import obsws_python as obsws
from obsws_python.error import OBSSDKError

logger = logging.getLogger(__name__)

class OBSCapture:
    """Classe pour capturer des vidéos depuis OBS via WebSocket"""
    
    def __init__(self, host="localhost", port=4455, password=None):
        """Initialise la connexion à OBS WebSocket
        
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
        self.video_sources = []
        self.media_sources = []
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.frame_time = 0
        self.is_capturing = False
        self.capture_thread = None
        
        # Pour des images alternatives
        self.test_image_counter = 0
        
        # Mode de fallback (si True, utilise des images de test en cas d'échec)
        self.use_test_images = False
        
        # Se connecter à OBS
        self._connect()
    
    def _connect(self):
        """Se connecte à OBS WebSocket"""
        try:
            logger.info(f"Tentative de connexion à OBS sur {self.host}:{self.port}")
            
            # Initialiser le client OBS WebSocket
            if self.password:
                self.client = obsws.ReqClient(host=self.host, port=self.port, password=self.password)
            else:
                self.client = obsws.ReqClient(host=self.host, port=self.port)
            
            # Vérifier la connexion
            version = self.client.get_version()
            logger.info(f"Connecté à OBS avec succès")
            logger.debug(f"Version OBS: {version.obs_version}, WebSocket: {version.obs_web_socket_version}")
            
            # Marquer comme connecté avant d'appeler _get_sources
            self.connected = True
            
            # Récupérer les sources disponibles
            self._get_sources()
        
        except Exception as e:
            logger.error(f"Erreur de connexion à OBS: {str(e)}")
            self.connected = False
            self.client = None
    
    def _get_sources(self):
        """Récupère les sources disponibles dans OBS"""
        if not self.connected or not self.client:
            logger.error("Impossible de récupérer les sources: non connecté à OBS")
            return
        
        # Essayer d'abord avec GetSceneList pour obtenir les sources visibles
        try:
            logger.info("Tentative de récupération des scènes via GetSceneList()")
            scene_list = self.client.get_scene_list()
            
            # Vérifier les attributs disponibles dans la réponse
            # (la structure peut varier entre les versions d'OBS WebSocket)
            if hasattr(scene_list, 'current_program_scene_name'):
                current_scene = scene_list.current_program_scene_name
            elif hasattr(scene_list, 'current_program_scene'):
                current_scene = scene_list.current_program_scene
            else:
                # Récupérer l'attribut directement depuis le dictionnaire de données
                response_data = scene_list.__dict__
                logger.debug(f"Structure de GetSceneList: {response_data}")
                
                # Essayer différents noms d'attributs possibles
                if 'current_program_scene_name' in response_data:
                    current_scene = response_data['current_program_scene_name']
                elif 'currentProgramSceneName' in response_data:
                    current_scene = response_data['currentProgramSceneName']
                else:
                    # Mettre une valeur par défaut
                    current_scene = "Unknown current scene"
            
            logger.info(f"Scène actuelle: {current_scene}")
            
            # Lister les scènes
            try:
                # Vérifier comment accéder aux scènes (structure peut varier)
                if hasattr(scene_list, 'scenes'):
                    scenes = scene_list.scenes
                    scene_names = [scene.name if hasattr(scene, 'name') else 
                                  scene.scene_name if hasattr(scene, 'scene_name') else 
                                  str(scene) for scene in scenes]
                else:
                    scene_names = ["Unknown scenes"]
                
                logger.info(f"Scènes disponibles: {scene_names}")
            except Exception as scene_e:
                logger.warning(f"Erreur lors de l'accès aux noms de scènes: {scene_e}")
            
            # Obtenir les sources via GetInputList
            try:
                logger.info("Tentative de récupération des sources via GetInputList()")
                inputs_response = self.client.get_input_list()
                
                # Vérifier la structure de la réponse
                if hasattr(inputs_response, 'inputs'):
                    all_inputs = inputs_response.inputs
                else:
                    logger.debug(f"Structure de GetInputList: {inputs_response.__dict__}")
                    all_inputs = []
                
                # Vérifier et filtrer les sources
                if all_inputs:
                    # Log toutes les sources pour le débogage
                    for input_data in all_inputs:
                        if isinstance(input_data, dict):
                            kind = input_data.get('inputKind', input_data.get('kind', 'unknown'))
                            name = input_data.get('inputName', input_data.get('name', 'unknown'))
                            logger.info(f"Source trouvée: {name} (type: {kind})")
                    
                    # Filtrer les sources vidéo et média
                    video_types = ['dshow_input', 'v4l2_input', 'video_capture_device', 
                                 'av_capture_input', 'game_capture', 'window_capture', 
                                 'screen_capture', 'browser_source', 'image_source']
                    
                    media_types = ['ffmpeg_source', 'vlc_source', 'media_source']
                    
                    self.video_sources = []
                    self.media_sources = []
                    
                    for input_data in all_inputs:
                        if isinstance(input_data, dict):
                            # Les noms des champs peuvent varier selon la version
                            kind = input_data.get('inputKind', input_data.get('kind', ''))
                            name = input_data.get('inputName', input_data.get('name', ''))
                            
                            if kind in video_types:
                                self.video_sources.append(name)
                            elif kind in media_types:
                                self.media_sources.append(name)
                    
                    logger.info(f"Sources vidéo trouvées: {self.video_sources}")
                    logger.info(f"Sources média trouvées: {self.media_sources}")
                else:
                    logger.warning("Aucune source trouvée via GetInputList()")
            except Exception as input_e:
                logger.error(f"Erreur lors de la récupération des inputs: {input_e}")
            
            # Si aucune source n'a été trouvée, utiliser une source de test
            if not self.video_sources:
                logger.warning("Aucune source vidéo trouvée, utilisation d'une source de test")
                self.video_sources = ["Test Source"]
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sources: {str(e)}")
            # Créer une source factice pour les tests
            self.video_sources = ["Test Source"]
    
    def _create_test_image(self, source_name, width=640, height=480):
        """Crée une image de test intéressante
        
        Args:
            source_name (str): Nom de la source
            width (int): Largeur de l'image
            height (int): Hauteur de l'image
            
        Returns:
            PIL.Image.Image: Image de test
        """
        # Incrémenter le compteur pour avoir des images différentes
        self.test_image_counter += 1
        
        # Créer une image colorée
        colors = [
            (255, 0, 0),    # Rouge
            (0, 255, 0),    # Vert
            (0, 0, 255),    # Bleu
            (255, 255, 0),  # Jaune
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
        ]
        
        # Choisir une couleur de fond en fonction du compteur
        bg_color = colors[self.test_image_counter % len(colors)]
        
        # Créer une image avec la couleur de fond
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Dessiner un motif
        for i in range(0, width, 40):
            draw.line([(i, 0), (i, height)], fill=(255, 255, 255), width=1)
        
        for i in range(0, height, 40):
            draw.line([(0, i), (width, i)], fill=(255, 255, 255), width=1)
        
        # Dessiner des rectangles ou cercles
        margin = 20  # Marge pour éviter les problèmes aux bords
        for _ in range(5):
            # Générer des coordonnées valides pour un rectangle
            x1 = random.randint(margin, width - margin)
            y1 = random.randint(margin, height - margin)
            x2 = random.randint(margin, width - margin)
            y2 = random.randint(margin, height - margin)
            
            # Assurer que x1 < x2 et y1 < y2
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
                
            # Assurer que le rectangle a une taille minimale
            if x2 - x1 < 10:
                x2 = x1 + 10
            if y2 - y1 < 10:
                y2 = y1 + 10
            
            # Vérifier que les coordonnées sont dans les limites
            x1 = max(0, min(x1, width-1))
            y1 = max(0, min(y1, height-1))
            x2 = max(0, min(x2, width-1))
            y2 = max(0, min(y2, height-1))
            
            # Vérification finale
            if x1 >= x2 or y1 >= y2:
                logger.warning(f"Coordonnées invalides: [{x1},{y1},{x2},{y2}], utilisation de valeurs par défaut")
                x1, y1, x2, y2 = margin, margin, width-margin, height-margin
            
            shape_color = colors[random.randint(0, len(colors)-1)]
            
            # Rectangle ou cercle
            if random.choice([True, False]):
                draw.rectangle([x1, y1, x2, y2], outline=shape_color, width=3)
            else:
                draw.ellipse([x1, y1, x2, y2], outline=shape_color, width=3)
        
        # Ajouter du texte
        timestamp = time.strftime("%H:%M:%S")
        draw.text((10, 10), f"Source: {source_name}", fill=(255, 255, 255))
        draw.text((10, 30), f"Capture test #{self.test_image_counter}", fill=(255, 255, 255))
        draw.text((10, 50), f"Temps: {timestamp}", fill=(255, 255, 255))
        
        # Ajouter une indication OBS
        draw.text((width-150, 10), "OBS TEST MODE", fill=(255, 255, 255))
        
        return img
    
    def capture_frame(self, source_name=None):
        """Capture une image d'une source OBS
        
        Args:
            source_name (str, optional): Nom de la source à capturer. Par défaut None (utilise la première source disponible).
        
        Returns:
            PIL.Image.Image: Image capturée, ou image de test si échec
        """
        if not self.connected or not self.client:
            logger.error("Impossible de capturer une image: non connecté à OBS")
            if self.use_test_images:
                return self._create_test_image("Non connecté", 640, 480)
            return None
        
        # Si aucune source n'est spécifiée, utiliser la première source vidéo
        if not source_name:
            if self.video_sources:
                source_name = self.video_sources[0]
            else:
                logger.error("Aucune source vidéo disponible")
                if self.use_test_images:
                    return self._create_test_image("Aucune source", 640, 480)
                return None
        
        # Tentative 1: Méthode pour OBS 31.0+ (utilisée dans les logs d'erreur)
        try:
            # Méthode exacte comme vue dans les logs
            from obsws_python import requests as obsreq
            screenshot_request = obsreq.GetSourceScreenshot(
                sourceName=source_name,
                imageFormat="png",
                imageWidth=640,
                imageHeight=480
            )
            screenshot = self.client.call(screenshot_request)
            
            # Extraire l'image
            if hasattr(screenshot, 'imageData'):
                img_data = screenshot.imageData
            else:
                # Si ce n'est pas directement accessible, essayer les autres propriétés
                for attr in ['img_data', 'image_data', 'data']:
                    if hasattr(screenshot, attr):
                        img_data = getattr(screenshot, attr)
                        break
                else:
                    # Si aucun des attributs attendus n'est trouvé
                    logger.debug(f"Structure de la réponse OBS 31.0+: {screenshot.__dict__}")
                    raise ValueError("Structure de réponse inattendue pour OBS 31.0+")
            
            if img_data:
                # Traiter le préfixe data:image/png;base64, si présent
                if isinstance(img_data, str) and ';base64,' in img_data:
                    img_data = img_data.split(';base64,')[1]
                
                # Décoder l'image base64
                img_bytes = base64.b64decode(img_data)
                img = Image.open(io.BytesIO(img_bytes))
                
                # Mettre à jour l'image courante
                with self.frame_lock:
                    self.current_frame = img
                    self.frame_time = time.time()
                
                return img
        except Exception as e:
            logger.debug(f"Méthode OBS 31.0+ échouée: {e}")
        
        # Tentative 2: Méthode alternative pour OBS 30.x
        try:
            screenshot = self.client.get_source_screenshot(
                sourceName=source_name,
                imageFormat="png",
                imageWidth=640,
                imageHeight=480
            )
            
            # Extraction similaire à celle de la tentative 1
            img_data = None
            for attr in ['imageData', 'img_data', 'image_data']:
                if hasattr(screenshot, attr):
                    img_data = getattr(screenshot, attr)
                    break
            
            if not img_data and hasattr(screenshot, '__dict__'):
                # Essayer d'accéder directement aux attributs du dictionnaire
                for key in ['imageData', 'img_data', 'image_data', 'data']:
                    if key in screenshot.__dict__:
                        img_data = screenshot.__dict__[key]
                        break
            
            if img_data:
                # Traiter le préfixe data:image/png;base64, si présent
                if isinstance(img_data, str) and ';base64,' in img_data:
                    img_data = img_data.split(';base64,')[1]
                
                # Décoder l'image base64
                img_bytes = base64.b64decode(img_data)
                img = Image.open(io.BytesIO(img_bytes))
                
                # Mettre à jour l'image courante
                with self.frame_lock:
                    self.current_frame = img
                    self.frame_time = time.time()
                
                return img
        except Exception as e:
            logger.debug(f"Méthode OBS 30.x échouée: {e}")
        
        # Tentative 3: Méthode pour OBS 28.x/29.x
        try:
            screenshot = self.client.get_source_screenshot(
                source_name=source_name,
                img_format="png",
                width=640,
                height=480
            )
            
            # Extraire les données de l'image
            img_data = None
            if hasattr(screenshot, 'img_data'):
                img_data = screenshot.img_data
            elif hasattr(screenshot, '__dict__'):
                # Essayer d'accéder directement aux attributs du dictionnaire
                for key in ['img_data', 'imageData', 'image_data', 'data']:
                    if key in screenshot.__dict__:
                        img_data = screenshot.__dict__[key]
                        break
            
            if img_data:
                # Traiter le préfixe data:image/png;base64, si présent
                if isinstance(img_data, str) and ';base64,' in img_data:
                    img_data = img_data.split(';base64,')[1]
                
                # Décoder l'image base64
                img_bytes = base64.b64decode(img_data)
                img = Image.open(io.BytesIO(img_bytes))
                
                # Mettre à jour l'image courante
                with self.frame_lock:
                    self.current_frame = img
                    self.frame_time = time.time()
                
                return img
        except Exception as e:
            logger.debug(f"Méthode OBS 28.x/29.x échouée: {e}")
        
        # Tentative 4: Approche minimale (dernière tentative)
        try:
            # Essai avec les options minimales
            screenshot = None
            try:
                screenshot = self.client.get_source_screenshot(sourceName=source_name)
            except Exception:
                try:
                    screenshot = self.client.get_source_screenshot(source_name=source_name)
                except Exception:
                    pass
            
            if screenshot:
                # Tenter d'extraire les données d'image
                img_data = None
                
                # Vérifier tous les attributs possibles
                if hasattr(screenshot, '__dict__'):
                    for key in ['imageData', 'img_data', 'image_data', 'data']:
                        if key in screenshot.__dict__:
                            img_data = screenshot.__dict__[key]
                            break
                
                if img_data:
                    # Traiter le préfixe data:image/png;base64, si présent
                    if isinstance(img_data, str) and ';base64,' in img_data:
                        img_data = img_data.split(';base64,')[1]
                    
                    # Décoder l'image base64
                    img_bytes = base64.b64decode(img_data)
                    img = Image.open(io.BytesIO(img_bytes))
                    
                    # Mettre à jour l'image courante
                    with self.frame_lock:
                        self.current_frame = img
                        self.frame_time = time.time()
                    
                    return img
        except Exception as e:
            logger.debug(f"Méthode minimale échouée: {e}")
        
        # Si aucune des méthodes n'a fonctionné
        logger.error(f"Échec de toutes les méthodes de capture pour {source_name}")
        
        if self.use_test_images:
            # Mode fallback activé, retourner une image de test
            logger.info(f"Utilisation d'une image de test pour {source_name}")
            img = self._create_test_image(source_name, 640, 480)
            
            # Mettre à jour l'image courante
            with self.frame_lock:
                self.current_frame = img
                self.frame_time = time.time()
            
            return img
        else:
            # En mode strict, retourner None pour indiquer un échec
            return None
    
    def start_capture(self, source_name=None, interval=0.1):
        """Démarre la capture continue en arrière-plan
        
        Args:
            source_name (str, optional): Source à capturer. Par défaut None.
            interval (float, optional): Intervalle entre les captures (secondes). Par défaut 0.1.
        """
        if self.is_capturing:
            logger.warning("Capture déjà en cours")
            return
        
        # Si aucune source n'est spécifiée, utiliser la première source vidéo
        if not source_name and self.video_sources:
            source_name = self.video_sources[0]
            logger.info(f"Aucune source spécifiée, utilisation de: {source_name}")
        
        if not source_name:
            logger.error("Aucune source vidéo disponible pour la capture continue")
            
            # Tentative de récupération des sources à nouveau
            logger.info("Tentative de récupération des sources vidéo à nouveau...")
            self._get_sources()
            
            if self.video_sources:
                source_name = self.video_sources[0]
                logger.info(f"Source trouvée après nouvelle tentative: {source_name}")
            else:
                # Créer une source factice pour les tests
                source_name = "Test Source"
        
        self.is_capturing = True
        
        # Démarrer le thread de capture
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(source_name, interval),
            daemon=True
        )
        self.capture_thread.start()
        
        logger.info(f"Capture continue démarrée pour {source_name} avec intervalle {interval}s")
    
    def _capture_loop(self, source_name, interval):
        """Boucle de capture continue
        
        Args:
            source_name (str): Source à capturer.
            interval (float): Intervalle entre les captures (secondes).
        """
        while self.is_capturing:
            try:
                self.capture_frame(source_name)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Erreur dans la boucle de capture: {e}")
                time.sleep(1)  # Pause plus longue en cas d'erreur
    
    def stop_capture(self):
        """Arrête la capture continue"""
        self.is_capturing = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
            self.capture_thread = None
        
        logger.info("Capture continue arrêtée")
    
    def get_current_frame(self):
        """Récupère l'image capturée la plus récente
        
        Returns:
            tuple: (PIL.Image.Image, float) Image et timestamp, ou (None, 0) si aucune image
        """
        with self.frame_lock:
            if self.current_frame is None:
                if self.use_test_images:
                    # Créer une image de test si aucune image n'est disponible
                    frame = self._create_test_image("Current Frame", 640, 480)
                    timestamp = time.time()
                    return frame, timestamp
                else:
                    return None, 0
            return self.current_frame, self.frame_time
    
    def get_frame_as_jpeg(self, quality=85):
        """Convertit l'image courante en JPEG
        
        Args:
            quality (int): Qualité JPEG (1-100)
            
        Returns:
            bytes: Données JPEG ou None si pas d'image
        """
        try:
            frame, _ = self.get_current_frame()
            
            if frame is None:
                if self.use_test_images:
                    # Si aucune image n'est disponible, créer une image de test
                    frame = self._create_test_image("JPEG Fallback", 640, 480)
                else:
                    return None
            
            # Convertir en JPEG
            img_buffer = io.BytesIO()
            frame.save(img_buffer, format='JPEG', quality=quality)
            return img_buffer.getvalue()
        except Exception as e:
            logger.error(f"Erreur lors de la conversion en JPEG: {e}")
            
            if self.use_test_images:
                # Créer une image très simple en cas d'erreur
                simple_img = Image.new('RGB', (640, 480), color=(0, 0, 128))
                img_buffer = io.BytesIO()
                simple_img.save(img_buffer, format='JPEG', quality=quality)
                return img_buffer.getvalue()
            else:
                return None
    
    def disconnect(self):
        """Déconnecte du serveur OBS WebSocket"""
        self.stop_capture()
        self.connected = False
        self.client = None
        logger.info("Déconnecté d'OBS WebSocket")
    
    def enable_test_images(self, enable=True):
        """Active ou désactive l'utilisation d'images de test en cas d'échec
        
        Args:
            enable (bool): True pour activer, False pour désactiver
        """
        self.use_test_images = enable
        logger.info(f"Mode d'images de test {'activé' if enable else 'désactivé'}")
