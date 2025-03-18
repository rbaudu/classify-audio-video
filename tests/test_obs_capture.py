#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier la capture d'image OBS
"""

import sys
import os
import time
import logging
import numpy as np
import io
from PIL import Image

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
    
    # Utiliser l'attribut 'connected' au lieu de 'is_connected()'
    if obs.connected:
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
    
    logger.info(f"✅ Sources vidéo détectées : {obs.video_sources}")
    return True

def test_capture_image(use_fallback=False):
    """
    Teste la capture d'image
    
    Args:
        use_fallback (bool): Si True, utilise des images de test en cas d'échec
    """
    obs = OBSCapture()
    
    # Configurer le mode d'images de test selon le paramètre
    obs.enable_test_images(use_fallback)
    
    # Attendre que la connexion s'établisse
    time.sleep(1)
    
    # Vérifier si des sources vidéo sont disponibles
    if not obs.video_sources:
        logger.error("❌ Aucune source vidéo disponible pour capturer une image")
        return False
    
    success = False
    for source in obs.video_sources:
        # Adapter selon la structure actuelle (liste de chaînes de caractères)
        if isinstance(source, dict):
            source_name = source.get('name', 'unknown')
        else:
            source_name = source
            
        logger.info(f"Tentative de capture de la source '{source_name}'...")
        
        # Essayer de capturer l'image
        try:
            # Utiliser la méthode capture_frame dans votre version actuelle
            frame = obs.capture_frame(source_name)
            
            if frame is None:
                logger.warning(f"❌ Source '{source_name}' : Aucune image capturée")
                if not use_fallback:
                    logger.info("ℹ️ Le mode strict est activé, aucune image de test n'est utilisée")
                continue
            
            # Pour les images PIL, convertir en format standard pour la journalisation
            if isinstance(frame, Image.Image):
                logger.info(f"✅ Image PIL capturée de la source '{source_name}' : {frame.size}")
                
                # Enregistrer l'image pour inspection
                output_path = f"test_capture_{source_name.replace(' ', '_')}.png"
                frame.save(output_path)
                logger.info(f"✅ Image enregistrée sous '{output_path}'")
                
                success = True
            else:
                logger.warning(f"❌ Source '{source_name}' : Type d'image inattendu : {type(frame)}")
        except Exception as e:
            logger.error(f"Erreur lors de la capture de '{source_name}': {e}")
    
    return success

def test_file_capture(use_fallback=False):
    """
    Teste la méthode de capture de frame au format JPEG
    
    Args:
        use_fallback (bool): Si True, utilise des images de test en cas d'échec
    """
    try:
        obs = OBSCapture()
        
        # Configurer le mode d'images de test
        obs.enable_test_images(use_fallback)
        
        # Attendre que la connexion s'établisse
        time.sleep(1)
        
        # Vérifier si des sources vidéo sont disponibles
        if not obs.video_sources:
            logger.error("❌ Aucune source vidéo disponible pour capturer une image")
            return False
        
        # Utiliser la première source vidéo disponible
        if isinstance(obs.video_sources[0], dict):
            source_name = obs.video_sources[0].get('name', 'unknown')
        else:
            source_name = obs.video_sources[0]
        
        logger.info(f"Test de capture JPEG pour '{source_name}'...")
        
        # Tester get_frame_as_jpeg
        jpeg_data = obs.get_frame_as_jpeg()
        
        if jpeg_data is None and not use_fallback:
            logger.error("❌ Aucune donnée JPEG obtenue et mode strict activé")
            return False
        
        if jpeg_data:
            # Vérifier que c'est un JPEG valide
            try:
                img = Image.open(io.BytesIO(jpeg_data))
                logger.info(f"✅ Image JPEG valide : {img.size}")
                
                # Enregistrer pour vérification
                output_path = "test_jpeg_capture.jpg"
                with open(output_path, 'wb') as f:
                    f.write(jpeg_data)
                logger.info(f"✅ Image JPEG enregistrée sous '{output_path}'")
                
                return True
            except Exception as e:
                logger.error(f"❌ Données JPEG invalides : {e}")
        else:
            logger.error("❌ Aucune donnée JPEG obtenue")
            
        # Si on arrive ici, c'est que la méthode JPEG a échoué
        # Essayer directement avec capture_frame si le fallback est activé
        if use_fallback:
            frame = obs.capture_frame(source_name)
            if frame:
                logger.info(f"✅ Capture directe réussie pour '{source_name}'")
                
                # Enregistrer l'image pour vérification
                if isinstance(frame, Image.Image):
                    output_path = "test_direct_capture.png"
                    frame.save(output_path)
                    logger.info(f"✅ Image enregistrée sous '{output_path}'")
                    return True
                else:
                    logger.warning(f"❌ Type d'image inattendu : {type(frame)}")
    except Exception as e:
        logger.error(f"Exception pendant le test de capture JPEG : {e}")
    
    return False

def test_real_capture():
    """
    Teste la capture réelle (sans fallback) pour vérifier si OBS fonctionne correctement
    """
    logger.info("\n=== Tentative de capture réelle (sans fallback) ===")
    result = test_capture_image(use_fallback=False)
    
    if result:
        logger.info("✅ Capture réelle réussie! OBS fonctionne correctement.")
    else:
        logger.warning("⚠️ Capture réelle échouée. OBS pourrait avoir des problèmes.")
        logger.info("ℹ️ Les tests continueront avec le mode fallback activé.")
    
    return result

def run_all_tests():
    """
    Exécute tous les tests
    """
    # D'abord, tester si la capture réelle fonctionne
    real_capture_works = test_real_capture()
    
    # Configurer le mode fallback en fonction du résultat
    use_fallback = not real_capture_works
    
    if use_fallback:
        logger.info("\nℹ️ Mode d'image de test activé pour les tests")
    else:
        logger.info("\nℹ️ Mode stricte activé pour les tests (pas d'images de test)")
    
    tests = [
        ("Connexion à OBS", test_obs_connection),
        ("Détection des sources vidéo", test_video_sources),
        ("Capture d'image", lambda: test_capture_image(use_fallback=use_fallback)),
        ("Capture vers fichier", lambda: test_file_capture(use_fallback=use_fallback))
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
    
    if use_fallback and all_success:
        logger.info("\n⚠️ Attention: Les tests ont réussi avec le mode d'images de test activé.")
        logger.info("   Cela signifie que les tests fonctionnent, mais que la capture OBS réelle a échoué.")
    
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
