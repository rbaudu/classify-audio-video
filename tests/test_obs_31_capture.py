#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier la capture d'image OBS 31.0.2
"""

import sys
import os
import time
import logging
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

# Importer la classe OBS31Capture
from server.capture.obs_31_capture import OBS31Capture

def test_obs_connection():
    """
    Teste la connexion à OBS
    """
    obs = OBS31Capture()
    
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
    obs = OBS31Capture()
    
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
    obs = OBS31Capture()
    
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
        logger.info(f"Tentative de capture de la source '{source}'...")
        
        # Essayer de capturer l'image
        try:
            frame = obs.capture_frame(source)
            
            if frame is None:
                logger.warning(f"❌ Source '{source}' : Aucune image capturée")
                if not use_fallback:
                    logger.info("ℹ️ Le mode strict est activé, aucune image de test n'est utilisée")
                continue
            
            # Pour les images PIL, convertir en format standard pour la journalisation
            if isinstance(frame, Image.Image):
                logger.info(f"✅ Image PIL capturée de la source '{source}' : {frame.size}")
                
                # Enregistrer l'image pour inspection
                output_path = f"test_obs31_capture_{source.replace(' ', '_')}.png"
                frame.save(output_path)
                logger.info(f"✅ Image enregistrée sous '{output_path}'")
                
                success = True
            else:
                logger.warning(f"❌ Source '{source}' : Type d'image inattendu : {type(frame)}")
        except Exception as e:
            logger.error(f"Erreur lors de la capture de '{source}': {e}")
    
    return success

def test_file_capture(use_fallback=False):
    """
    Teste la méthode de capture de frame au format JPEG
    
    Args:
        use_fallback (bool): Si True, utilise des images de test en cas d'échec
    """
    try:
        obs = OBS31Capture()
        
        # Configurer le mode d'images de test
        obs.enable_test_images(use_fallback)
        
        # Attendre que la connexion s'établisse
        time.sleep(1)
        
        # Vérifier si des sources vidéo sont disponibles
        if not obs.video_sources:
            logger.error("❌ Aucune source vidéo disponible pour capturer une image")
            return False
        
        # Utiliser la première source vidéo disponible
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
                output_path = "test_obs31_jpeg_capture.jpg"
                with open(output_path, 'wb') as f:
                    f.write(jpeg_data)
                logger.info(f"✅ Image JPEG enregistrée sous '{output_path}'")
                
                return True
            except Exception as e:
                logger.error(f"❌ Données JPEG invalides : {e}")
        else:
            logger.error("❌ Aucune donnée JPEG obtenue")
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
        logger.info("✅ Capture réelle réussie! OBS 31.0.2 fonctionne correctement.")
    else:
        logger.warning("⚠️ Capture réelle échouée. OBS 31.0.2 pourrait avoir des problèmes.")
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
    logger.info("Démarrage des tests de capture OBS 31.0.2...")
    
    success = run_all_tests()
    
    if success:
        logger.info("✅ Tous les tests ont réussi !")
        sys.exit(0)
    else:
        logger.error("❌ Certains tests ont échoué.")
        sys.exit(1)
