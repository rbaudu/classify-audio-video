#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import cv2
import numpy as np
from obswebsocket import obsws, requests
import time

logger = logging.getLogger(__name__)

class OBSCapture:
    """
    Classe pour la capture des flux vidéo et audio depuis OBS Studio via websocket.
    """
    
    def __init__(self, host, port, password):
        """
        Initialise la connexion avec OBS Studio.
        
        Args:
            host (str): Hôte du serveur websocket OBS (localhost par défaut)
            port (int): Port du serveur websocket OBS (4444 par défaut)
            password (str): Mot de passe pour la connexion (vide par défaut)
        """
        self.host = host
        self.port = port
        self.password = password
        self.obs_socket = None
        self.connected = False
        self.current_scene = None
        self.available_sources = []
        
        # Tentative de connexion à OBS
        self._connect()
    
    def _connect(self):
        """Établit la connexion avec OBS Studio."""
        try:
            self.obs_socket = obsws(self.host, self.port, self.password)
            self.obs_socket.connect()
            self.connected = True
            
            # Récupération des informations sur la scène actuelle
            scene_data = self.obs_socket.call(requests.GetCurrentScene())
            self.current_scene = scene_data.getName()
            self.available_sources = [source['name'] for source in scene_data.getSources()]
            
            logger.info(f"Connecté à OBS sur {self.host}:{self.port}")
            logger.info(f"Scène actuelle: {self.current_scene}")
            logger.info(f"Sources disponibles: {', '.join(self.available_sources)}")
            
        except Exception as e:
            self.connected = False
            logger.error(f"Erreur lors de la connexion à OBS: {str(e)}")
    
    def reconnect(self):
        """Tentative de reconnexion à OBS."""
        if not self.connected:
            logger.info("Tentative de reconnexion à OBS...")
            self._connect()
            return self.connected
        return True
    
    def get_video_frame(self, source_name=None):
        """
        Capture une image depuis une source vidéo OBS.
        
        Args:
            source_name (str, optional): Nom de la source. Si None, utilise la première source vidéo disponible.
            
        Returns:
            numpy.ndarray: Image capturée ou None si échec
        """
        if not self.connected and not self.reconnect():
            return None
        
        try:
            # Si aucune source n'est spécifiée, utiliser la première source vidéo disponible
            if source_name is None and self.available_sources:
                # Filtrer pour trouver les sources de type vidéo
                for source in self.available_sources:
                    source_info = self.obs_socket.call(requests.GetSourceSettings(sourceName=source))
                    if source_info.getSourceType() in ['dshow_input', 'v4l2_input', 'video_capture_source']:
                        source_name = source
                        break
            
            if not source_name:
                logger.warning("Aucune source vidéo trouvée")
                return None
            
            # Capture d'image via OBS
            # Note: Cette méthode est simplifiée car l'API obs-websocket n'a pas de méthode
            # directe pour obtenir une image. En pratique, on pourrait utiliser
            # TakeSourceScreenshot ou une solution personnalisée.
            
            # Simulation de capture d'image (à remplacer par l'implémentation réelle)
            # Dans un système réel, on pourrait utiliser une API comme FFmpeg ou
            # configurer OBS pour enregistrer des images dans un dossier
            
            # Pour les besoins de l'exemple, on crée une image noire
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Ici, vous implémenteriez la véritable méthode de capture
            # Cela pourrait impliquer TakeSourceScreenshot et la lecture d'un fichier,
            # ou un autre mécanisme de capture de flux vidéo
            
            return frame
            
        except Exception as e:
            logger.error(f"Erreur lors de la capture vidéo: {str(e)}")
            self.connected = False
            return None
    
    def get_audio_data(self, source_name=None, duration=1.0):
        """
        Capture des données audio depuis une source OBS.
        
        Args:
            source_name (str, optional): Nom de la source. Si None, utilise la première source audio disponible.
            duration (float): Durée de l'enregistrement audio en secondes
            
        Returns:
            numpy.ndarray: Données audio capturées ou None si échec
        """
        if not self.connected and not self.reconnect():
            return None
        
        try:
            # Si aucune source n'est spécifiée, utiliser la première source audio disponible
            if source_name is None and self.available_sources:
                # Filtrer pour trouver les sources de type audio
                for source in self.available_sources:
                    source_info = self.obs_socket.call(requests.GetSourceSettings(sourceName=source))
                    if source_info.getSourceType() in ['wasapi_input_capture', 'pulse_input_capture', 'audio_capture_source']:
                        source_name = source
                        break
            
            if not source_name:
                logger.warning("Aucune source audio trouvée")
                return None
            
            # Capture audio via OBS
            # Note: Cette méthode est simplifiée car l'API obs-websocket n'a pas de méthode
            # directe pour obtenir un flux audio. En pratique, on pourrait utiliser
            # une solution personnalisée pour capturer l'audio.
            
            # Simulation de capture audio (à remplacer par l'implémentation réelle)
            # Dans un système réel, on pourrait utiliser une API comme PyAudio ou
            # configurer OBS pour enregistrer des segments audio dans un dossier
            
            # Pour les besoins de l'exemple, on crée un tableau de zéros (silence)
            sample_rate = 16000  # 16 kHz
            channels = 1  # Mono
            audio_data = np.zeros(int(sample_rate * duration), dtype=np.float32)
            
            # Ici, vous implémenteriez la véritable méthode de capture audio
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la capture audio: {str(e)}")
            self.connected = False
            return None
    
    def close(self):
        """Ferme la connexion avec OBS."""
        if self.connected and self.obs_socket:
            try:
                self.obs_socket.disconnect()
                logger.info("Déconnexion d'OBS réussie")
            except Exception as e:
                logger.error(f"Erreur lors de la déconnexion d'OBS: {str(e)}")
            finally:
                self.connected = False
