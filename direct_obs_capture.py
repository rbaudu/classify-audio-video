#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script simple pour capturer directement une image depuis OBS 31.0.2
"""

import logging
import sys
import time
import obsws_python as obsws

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """
    Fonction principale pour capturer une image depuis OBS
    """
    logger.info("Script de capture directe OBS 31.0.2")
    
    try:
        # Connexion à OBS
        client = obsws.ReqClient(host="localhost", port=4455)
        logger.info("Connexion établie à OBS WebSocket")
        
        # Obtenir la version
        version = client.get_version()
        logger.info(f"Version OBS: {version.obs_version}, WebSocket: {version.obs_web_socket_version}")
        
        # Obtenir les sources
        inputs = client.get_input_list()
        video_sources = []
        
        if hasattr(inputs, 'inputs'):
            for source in inputs.inputs:
                kind = source.get('inputKind', source.get('kind', 'unknown'))
                name = source.get('inputName', source.get('name', 'unknown'))
                logger.info(f"Source trouvée: {name} (type: {kind})")
                
                # Filtrer les sources vidéo
                if kind in ['dshow_input', 'v4l2_input', 'video_capture_device']:
                    video_sources.append(name)
        
        if not video_sources:
            logger.error("Aucune source vidéo trouvée")
            return
        
        # Utiliser la première source vidéo
        source_name = video_sources[0]
        logger.info(f"Utilisation de la source: {source_name}")
        
        # Capture d'écran avec les paramètres exacts
        logger.info("Tentative de capture d'écran...")
        
        # Paramètres selon la signature: name, img_format, width, height, quality
        screenshot = client.get_source_screenshot(
            source_name,  # name
            "png",        # img_format
            640,          # width
            480,          # height
            75            # quality
        )
        
        # Vérifier la réponse
        logger.info(f"Type de réponse: {type(screenshot)}")
        
        if hasattr(screenshot, '__dict__'):
            logger.info(f"Attributs disponibles: {list(screenshot.__dict__.keys())}")
            
            # Vérifier dans image_data (basé sur votre log précédent)
            if hasattr(screenshot, 'image_data'):
                img_data = screenshot.image_data
                logger.info(f"Attribut 'image_data' trouvé, type: {type(img_data)}")
                
                # Enregistrer les données (si c'est une chaîne base64)
                if isinstance(img_data, str):
                    logger.info(f"Les premières caractères de l'image: {img_data[:30]}")
                    
                    import base64
                    import io
                    from PIL import Image
                    
                    # Vérifier s'il y a un préfixe base64 à enlever
                    if ';base64,' in img_data:
                        logger.info("Format avec préfixe base64 détecté")
                        img_data = img_data.split(';base64,')[1]
                    
                    # Décoder et sauvegarder
                    try:
                        img_bytes = base64.b64decode(img_data)
                        img = Image.open(io.BytesIO(img_bytes))
                        
                        output_path = f"direct_capture_{source_name}.png"
                        img.save(output_path)
                        logger.info(f"✅ Image enregistrée sous: {output_path}")
                        return True
                    except Exception as e:
                        logger.error(f"Erreur lors du décodage/enregistrement: {e}")
                else:
                    logger.error(f"image_data n'est pas une chaîne mais un {type(img_data)}")
            else:
                # Parcourir tous les attributs à la recherche de données d'image
                for attr_name, attr_value in screenshot.__dict__.items():
                    if isinstance(attr_value, str) and len(attr_value) > 100:
                        logger.info(f"Attribut potentiel d'image trouvé: {attr_name}")
                        # Essayer de décoder
                        try:
                            if ';base64,' in attr_value:
                                attr_value = attr_value.split(';base64,')[1]
                            
                            import base64
                            import io
                            from PIL import Image
                            
                            img_bytes = base64.b64decode(attr_value)
                            img = Image.open(io.BytesIO(img_bytes))
                            
                            output_path = f"direct_capture_{attr_name}_{source_name}.png"
                            img.save(output_path)
                            logger.info(f"✅ Image enregistrée sous: {output_path}")
                            return True
                        except Exception as e:
                            logger.error(f"Erreur de décodage pour l'attribut {attr_name}: {e}")
        
        logger.error("❌ Capture d'écran échouée ou format inattendu")
        return False
        
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
