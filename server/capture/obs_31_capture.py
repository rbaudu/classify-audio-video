# -*- coding: utf-8 -*-
"""
Module de capture vidéo via OBS WebSocket 31.0.2
Version simplifiée et optimisée pour OBS 31.0.2+
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

logger = logging.getLogger(__name__)

class OBS31Capture:
    """Classe pour capturer des vidéos depuis OBS 31.0.2+ via WebSocket"""
    
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
            logger.info(f"Version OBS: {version.obs_version}, WebSocket: {version.obs_web_socket_version}")
            
            # Vérifier que la version est 31.0.0 ou plus
            if hasattr(version, 'obs_version'):
                major_version = version.obs_version.split('.')[0]
                if int(major_version) < 31:
                    logger.warning(f"Cette classe est optimisée pour OBS 31.0.0+, mais la version détectée est {version.obs_version}")
            
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
        
        try:
            # Obtenir la liste des inputs (sources)
            inputs_response = self.client.get_input_list()
            
            # Vérifier et filtrer les sources
            if hasattr(inputs_response, 'inputs'):
                all_inputs = inputs_response.inputs
                
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
                logger.debug(f"Structure de GetInputList: {inputs_response.__dict__}")
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sources: {str(e)}")
            self.video_sources = []
            self.media_sources = []
    
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
        
        # Dessiner un motif de grille
        for i in range(0, width, 40):
            draw.line([(i, 0), (i, height)], fill=(255, 255, 255), width=1)
        
        for i in range(0, height, 40):
            draw.line([(0, i), (width, i)], fill=(255, 255, 255), width=1)
        
        # Dessiner des rectangles ou cercles aléatoires
        margin = 20
        for _ in range(5):
            x1 = random.randint(margin, width - margin)
            y1 = random.randint(margin, height - margin)
            x2 = random.randint(margin, width - margin)
            y2 = random.randint(margin, height - margin)
            
            # Assurer que x1 < x2 et y1 < y2
            if x1 > x2: x1, x2 = x2, x1
            if y1 > y2: y1, y2 = y2, y1
            
            # Garantir une taille minimale
            if x2 - x1 < 10: x2 = x1 + 10
            if y2 - y1 < 10: y2 = y1 + 10
            
            # Vérifier les limites
            x1 = max(0, min(x1, width-1))
            y1 = max(0, min(y1, height-1))
            x2 = max(0, min(x2, width-1))
            y2 = max(0, min(y2, height-1))
            
            shape_color = colors[random.randint(0, len(colors)-1)]
            
            # Rectangle ou cercle
            if random.choice([True, False]):
                draw.rectangle([x1, y1, x2, y2], outline=shape_color, width=3)
            else:
                draw.ellipse([x1, y1, x2, y2], outline=shape_color, width=3)
        
        # Ajouter du texte informatif
        timestamp = time.strftime("%H:%M:%S")
        draw.text((10, 10), f"Source: {source_name}", fill=(255, 255, 255))
        draw.text((10, 30), f"Capture test #{self.test_image_counter}", fill=(255, 255, 255))
        draw.text((10, 50), f"Temps: {timestamp}", fill=(255, 255, 255))
        draw.text((width-150, 10), "OBS TEST MODE", fill=(255, 255, 255))
        
        return img
    
    def capture_frame(self, source_name=None):
        """Capture une image d'une source OBS
        
        Args:
            source_name (str, optional): Nom de la source à capturer. Par défaut None (utilise la première source disponible).
        
        Returns:
            PIL.Image.Image: Image capturée, ou image de test si échec et mode test activé, ou None si échec et mode test désactivé
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
        
        # Méthode de capture OBS 31.0.x
        try:
            # Utiliser la méthode get_source_screenshot avec tous les paramètres requis
            # D'après la documentation, la signature est:
            # get_source_screenshot(name, img_format, width, height, quality)
            logger.info(f"Tentative de capture pour {source_name} avec tous les paramètres")
            
            # Préparation des paramètres selon la signature
            name = source_name
            img_format = "png"  # Format d'image
            width = 640        # Largeur
            height = 480       # Hauteur
            quality = 75       # Qualité (0-100)
            
            # Appel de la méthode avec les arguments corrects
            screenshot = self.client.get_source_screenshot(
                name,         # Position 1: name
                img_format,   # Position 2: img_format
                width,        # Position 3: width
                height,       # Position 4: height
                quality       # Position 5: quality
            )
            
            logger.info(f"Réponse de type: {type(screenshot)}")
            
            # Extraction des données d'image
            img_data = None
            if hasattr(screenshot, 'imageData'):
                img_data = screenshot.imageData
                logger.info("Attribut 'imageData' trouvé")
            elif hasattr(screenshot, 'img_data'):
                img_data = screenshot.img_data
                logger.info("Attribut 'img_data' trouvé")
            elif hasattr(screenshot, 'data'):
                img_data = screenshot.data
                logger.info("Attribut 'data' trouvé")
            else:
                # Vérifier directement les attributs disponibles
                if hasattr(screenshot, '__dict__'):
                    logger.info(f"Attributs disponibles dans la réponse: {list(screenshot.__dict__.keys())}")
                    
                    # Parcourir tous les attributs pour trouver des données potentielles d'image
                    for key, value in screenshot.__dict__.items():
                        if isinstance(value, str) and (';base64,' in value or len(value) > 100):
                            logger.info(f"Données potentielles d'image trouvées dans l'attribut '{key}'")
                            img_data = value
                            break
            
            if img_data:
                # Traiter le préfixe data:image/png;base64, si présent
                if isinstance(img_data, str) and ';base64,' in img_data:
                    img_data = img_data.split(';base64,')[1]
                
                # Décoder l'image base64
                try:
                    img_bytes = base64.b64decode(img_data)
                    img = Image.open(io.BytesIO(img_bytes))
                    
                    # Mettre à jour l'image courante
                    with self.frame_lock:
                        self.current_frame = img
                        self.frame_time = time.time()
                    
                    logger.info(f"Capture d'image réussie: {img.size}")
                    return img
                except Exception as decode_err:
                    logger.error(f"Erreur de décodage de l'image: {decode_err}")
            else:
                logger.error("Aucune donnée d'image trouvée dans la réponse OBS")
        
        except Exception as e:
            logger.error(f"Erreur lors de la capture d'écran: {e}")
        
        # Si on arrive ici, c'est que toutes les tentatives ont échoué
        if self.use_test_images:
            logger.info(f"Utilisation d'une image de test pour {source_name}")
            img = self._create_test_image(source_name, 640, 480)
            
            with self.frame_lock:
                self.current_frame = img
                self.frame_time = time.time()
            
            return img
        else:
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
            return
        
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
