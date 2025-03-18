#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test dédié à l'exploration de l'API OBS 31.0.2
"""

import sys
import os
import logging
import base64
import io
import time
from PIL import Image
import inspect

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Importer la bibliothèque OBS WebSocket
import obsws_python as obsws

def inspect_obs_client():
    """
    Inspecte la bibliothèque OBS WebSocket pour trouver les méthodes disponibles
    """
    logger.info("=== Inspection du client OBS WebSocket ===")
    
    try:
        # Créer un client de test
        client = obsws.ReqClient(host="localhost", port=4455)
        
        # Obtenir la version
        version = client.get_version()
        logger.info(f"Connecté à OBS version {version.obs_version}, WebSocket: {version.obs_web_socket_version}")
        
        # Lister toutes les méthodes disponibles
        logger.info("\n=== Méthodes disponibles dans ReqClient ===")
        methods = [method for method in dir(client) if callable(getattr(client, method)) and not method.startswith('_')]
        
        for method in sorted(methods):
            try:
                # Obtenir la signature de la méthode
                fn = getattr(client, method)
                signature = inspect.signature(fn)
                logger.info(f"{method}{signature}")
            except Exception as e:
                logger.info(f"{method} - Erreur d'introspection: {e}")
        
        # Focus sur la méthode get_source_screenshot
        if 'get_source_screenshot' in methods:
            logger.info("\n=== Détails de get_source_screenshot ===")
            screenshot_method = getattr(client, 'get_source_screenshot')
            
            # Afficher la documentation
            if screenshot_method.__doc__:
                logger.info(f"Documentation:\n{screenshot_method.__doc__}")
            else:
                logger.info("Pas de documentation disponible.")
            
            # Afficher les paramètres
            sig = inspect.signature(screenshot_method)
            logger.info(f"Signature: {sig}")
            
            for param_name, param in sig.parameters.items():
                logger.info(f"  - {param_name}: {param.default if param.default != param.empty else 'Required'} ({param.kind})")
        
        # Tester GetInputList pour avoir la liste des sources
        inputs = client.get_input_list()
        logger.info("\n=== Sources disponibles ===")
        
        if hasattr(inputs, 'inputs'):
            for source in inputs.inputs:
                name = source.get('inputName', source.get('name', 'Unknown'))
                kind = source.get('inputKind', source.get('kind', 'Unknown'))
                logger.info(f"Source: {name} (type: {kind})")
        
            # Tester spécifiquement la méthode get_source_screenshot
            if 'get_source_screenshot' in methods:
                logger.info("\n=== Test de capture d'image ===")
                
                # Obtenir une source vidéo
                video_sources = []
                
                for source in inputs.inputs:
                    kind = source.get('inputKind', source.get('kind', ''))
                    name = source.get('inputName', source.get('name', ''))
                    
                    if kind in ['dshow_input', 'v4l2_input', 'video_capture_device']:
                        video_sources.append(name)
                
                if video_sources:
                    source_name = video_sources[0]
                    logger.info(f"Tentative de capture pour la source: {source_name}")
                    
                    # Essayer différentes variantes d'appel
                    try_screenshot_methods(client, source_name)
                else:
                    logger.warning("Aucune source vidéo trouvée pour tester la capture d'image")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'inspection du client OBS: {e}")

def try_screenshot_methods(client, source_name):
    """
    Essaie différentes variantes d'appel à get_source_screenshot
    
    Args:
        client: Client OBS WebSocket
        source_name: Nom de la source à capturer
    """
    # Variante 1: Essayer input_name
    logger.info("=== Méthode 1: input_name ===")
    try:
        screenshot = client.get_source_screenshot(
            input_name=source_name,
            image_format="png",
            width=640,
            height=480
        )
        logger.info(f"Réponse de type: {type(screenshot)}")
        if hasattr(screenshot, '__dict__'):
            logger.info(f"Attributs: {screenshot.__dict__.keys()}")
            
            # Tester si une image a été capturée
            process_screenshot_response(screenshot, "input_name")
    except Exception as e:
        logger.error(f"Erreur avec input_name: {e}")
    
    # Variante 2: Utiliser source au lieu de source_name/sourceName
    logger.info("=== Méthode 2: source ===")
    try:
        screenshot = client.get_source_screenshot(
            source=source_name,
            image_format="png",
            width=640,
            height=480
        )
        logger.info(f"Réponse de type: {type(screenshot)}")
        if hasattr(screenshot, '__dict__'):
            logger.info(f"Attributs: {screenshot.__dict__.keys()}")
            
            process_screenshot_response(screenshot, "source")
    except Exception as e:
        logger.error(f"Erreur avec source: {e}")
    
    # Variante 3: Utiliser des arguments positionnels
    logger.info("=== Méthode 3: Arguments positionnels ===")
    try:
        # Essayer avec la syntaxe source, format, width, height
        screenshot = client.get_source_screenshot(source_name, "png", 640, 480)
        logger.info(f"Réponse de type: {type(screenshot)}")
        if hasattr(screenshot, '__dict__'):
            logger.info(f"Attributs: {screenshot.__dict__.keys()}")
            
            process_screenshot_response(screenshot, "positional")
    except Exception as e:
        logger.error(f"Erreur avec arguments positionnels: {e}")
    
    # Variante 4: Appel direct de call()
    logger.info("=== Méthode 4: Appel direct de call() ===")
    try:
        from obsws_python.reqs.requests import GetSourceScreenshot
        screenshot_request = GetSourceScreenshot(
            sourceName=source_name,
            imageFormat="png",
            imageWidth=640,
            imageHeight=480
        )
        screenshot = client.call(screenshot_request)
        logger.info(f"Réponse de type: {type(screenshot)}")
        if hasattr(screenshot, '__dict__'):
            logger.info(f"Attributs: {screenshot.__dict__.keys()}")
            
            process_screenshot_response(screenshot, "call_direct")
    except Exception as e:
        logger.error(f"Erreur avec call() direct: {e}")

def process_screenshot_response(response, method_name):
    """
    Traite la réponse d'une capture d'écran
    
    Args:
        response: Réponse de get_source_screenshot
        method_name: Nom de la méthode utilisée
    """
    # Parcourir tous les attributs possibles contenant des données d'image
    for attr_name in ['img', 'img_data', 'image', 'image_data', 'imageData', 'data']:
        if hasattr(response, attr_name):
            img_data = getattr(response, attr_name)
            logger.info(f"Attribut d'image trouvé: {attr_name}")
            
            try:
                # Si c'est une chaîne base64, essayer de la décoder
                if isinstance(img_data, str):
                    # Supprimer le préfixe data:image/png;base64, si présent
                    if ';base64,' in img_data:
                        img_data = img_data.split(';base64,')[1]
                    
                    try:
                        # Décoder la base64
                        img_bytes = base64.b64decode(img_data)
                        
                        # Essayer d'ouvrir comme image
                        img = Image.open(io.BytesIO(img_bytes))
                        logger.info(f"✅ Méthode {method_name}: Image décodée avec succès! Taille: {img.size}")
                        
                        # Sauvegarder l'image pour vérification
                        output_path = f"test_{method_name}_capture.png"
                        img.save(output_path)
                        logger.info(f"Image enregistrée sous '{output_path}'")
                        return
                    except Exception as e:
                        logger.error(f"Erreur lors du décodage de l'image: {e}")
            except Exception as e:
                logger.error(f"Erreur lors du traitement de l'attribut {attr_name}: {e}")
    
    # Si on arrive ici, c'est qu'aucun attribut standard n'a été trouvé
    # Parcourir tous les attributs de la réponse
    if hasattr(response, '__dict__'):
        for key, value in response.__dict__.items():
            if isinstance(value, str) and len(value) > 100:
                logger.info(f"Attribut potentiel d'image trouvé: {key} (longueur: {len(value)})")
                if value.startswith(('data:', 'iVBOR', '/9j/')):
                    logger.info(f"Contenu semble être une image base64")

if __name__ == "__main__":
    logger.info("Démarrage du test de l'API OBS 31.0.2...")
    inspect_obs_client()
