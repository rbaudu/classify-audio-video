#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier la capture d'image OBS
"""

import sys
import os
import time
import logging
import cv2
import numpy as np

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Importer la classe OBSCapture
from server.capture.obs_capture import OBSCapture

def test_obs_connection():
    """
    Teste la connexion à OBS
    """
    obs = OBSCapture()
    
    if obs.is_connected():
        logger.info("✅ Connexion à OBS réussie")
    else:
        logger.error("❌ Échec de la connexion à OBS")
        return False
    
    return True

def test_video_sources():
    """
    Teste la détection des sources vidéo
    """
    obs = OBSCapture()
    
    # Attendre que la connexion s'établisse
    time.sleep(1)
    
    if not obs.video_sources:
        logger.error("❌ Aucune source vidéo détectée")
        return False
    
    logger.info(f"✅ Sources vidéo détectées : {[s['name'] for s in obs.video_sources]}")
    return True

def test_capture_image():
    """
    Teste la capture d'image
    """
    obs = OBSCapture()
    
    # Attendre que la connexion s'établisse
    time.sleep(1)
    
    # Trouver les sources vidéo disponibles
    sources = [s['name'] for s in obs.video_sources]
    
    if not sources:
        logger.error("❌ Aucune source vidéo disponible pour capturer une image")
        return False
    
    success = False
    for source in sources:
        logger.info(f"Tentative de capture de la source '{source}'...")
        
        # Essayer de capturer l'image
        frame = obs.get_video_frame(source)
        
        if frame is None or (isinstance(frame, np.ndarray) and np.all(frame == 0)):
            logger.warning(f"❌ Source '{source}' : Aucune image capturée ou image noire")
            continue
        
        # Afficher les informations de l'image
        if isinstance(frame, np.ndarray):
            logger.info(f"✅ Image capturée de la source '{source}' : {frame.shape}")
            
            # Enregistrer l'image pour inspection
            output_path = f"test_capture_{source.replace(' ', '_')}.png"
            cv2.imwrite(output_path, frame)
            logger.info(f"✅ Image enregistrée sous '{output_path}'")
            
            success = True
        else:
            logger.warning(f"❌ Source '{source}' : Type d'image inattendu : {type(frame)}")
    
    return success

def test_file_capture():
    """
    Teste la nouvelle méthode de capture par fichier
    """
    from server.capture.obs_sources import OBSSourcesMixin
    
    class TestCapture(OBSSourcesMixin):
        def __init__(self):
            self.logger = logging.getLogger("TestCapture")
            self._initialize_capture_state()
            self.connected = True
            self.ws_lock = type('DummyLock', (), {'__enter__': lambda x: None, '__exit__': lambda x, *args: None})()
            self.consecutive_capture_errors = 0
            self.last_successful_frame = None
    
    obs = OBSCapture()
    
    # Attendre que la connexion s'établisse
    time.sleep(1)
    
    # Trouver les sources vidéo disponibles
    sources = [s['name'] for s in obs.video_sources]
    
    if not sources:
        logger.error("❌ Aucune source vidéo disponible pour capturer une image")
        return False
    
    test_source = sources[0]
    logger.info(f"Test de capture vers fichier pour '{test_source}'...")
    
    # Test de la méthode de capture vers fichier
    result = obs._capture_to_file(test_source)
    
    if result:
        logger.info(f"✅ Capture vers fichier réussie pour '{test_source}'")
        
        # Vérifier que le fichier existe
        if os.path.exists(obs.temp_image_path):
            logger.info(f"✅ Fichier temporaire créé : {obs.temp_image_path}")
            
            # Charger l'image
            image = cv2.imread(obs.temp_image_path)
            
            if image is not None:
                logger.info(f"✅ Image chargée avec succès : {image.shape}")
                return True
            else:
                logger.error("❌ Impossible de charger l'image à partir du fichier")
        else:
            logger.error(f"❌ Fichier temporaire non trouvé : {obs.temp_image_path}")
    else:
        logger.error(f"❌ Échec de la capture vers fichier pour '{test_source}'")
    
    return False

def run_all_tests():
    """
    Exécute tous les tests
    """
    tests = [
        ("Connexion à OBS", test_obs_connection),
        ("Détection des sources vidéo", test_video_sources),
        ("Capture d'image", test_capture_image),
        ("Capture vers fichier", test_file_capture)
    ]
    
    results = []
    
    for name, func in tests:
        logger.info(f"\n=== Test : {name} ===")
        try:
            success = func()
            results.append((name, success))
        except Exception as e:
            logger.exception(f"Exception pendant le test '{name}' : {e}")
            results.append((name, False))
    
    # Afficher le résumé
    logger.info("\n=== Résumé des tests ===")
    
    all_success = True
    for name, success in results:
        status = "✅ Réussi" if success else "❌ Échoué"
        logger.info(f"{status} : {name}")
        all_success = all_success and success
    
    return all_success

if __name__ == "__main__":
    logger.info("Démarrage des tests de capture OBS...")
    
    success = run_all_tests()
    
    if success:
        logger.info("✅ Tous les tests ont réussi !")
        sys.exit(0)
    else:
        logger.error("❌ Certains tests ont échoué.")
        sys.exit(1)
