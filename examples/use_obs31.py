#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exemple d'utilisation de OBS31Capture pour la capture d'images depuis OBS 31.0.2+
"""

import sys
import os
import time
import logging
from PIL import Image, ImageDraw

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Importer les classes pour OBS 31.0.2+
from server.capture.obs_31_capture import OBS31Capture
from server.capture.obs_31_adapter import OBS31Adapter

def example_simple_capture():
    """
    Exemple simple de capture d'une image depuis OBS
    """
    print("\n=== Exemple 1: Capture simple avec OBS31Capture ===")
    
    # Créer une instance de OBS31Capture
    obs = OBS31Capture()
    
    # Activer le mode de test (images alternatives en cas d'échec)
    obs.enable_test_images(True)
    
    # Attendre que la connexion s'établisse
    time.sleep(1)
    
    # Afficher les sources vidéo disponibles
    print(f"Sources vidéo disponibles: {obs.video_sources}")
    
    # Capturer une image
    if obs.video_sources:
        print(f"Tentative de capture de la source '{obs.video_sources[0]}'...")
        frame = obs.capture_frame(obs.video_sources[0])
        
        if frame:
            print(f"Image capturée: {frame.size}")
            
            # Enregistrer l'image pour vérification
            output_path = "example_obs31_capture.png"
            frame.save(output_path)
            print(f"Image enregistrée sous '{output_path}'")
        else:
            print("Échec de la capture d'image")
    else:
        print("Aucune source vidéo disponible")
    
    # Déconnecter
    obs.disconnect()

def example_continuous_capture():
    """
    Exemple de capture continue d'images depuis OBS
    """
    print("\n=== Exemple 2: Capture continue avec OBS31Capture ===")
    
    # Créer une instance de OBS31Capture
    obs = OBS31Capture()
    
    # Activer le mode de test (images alternatives en cas d'échec)
    obs.enable_test_images(True)
    
    # Attendre que la connexion s'établisse
    time.sleep(1)
    
    # Vérifier si des sources vidéo sont disponibles
    if not obs.video_sources:
        print("Aucune source vidéo disponible")
        return
    
    # Sélectionner la première source
    source_name = obs.video_sources[0]
    print(f"Utilisation de la source: {source_name}")
    
    # Démarrer la capture continue
    print("Démarrage de la capture continue...")
    obs.start_capture(source_name, interval=0.5)  # Capture toutes les 0.5 secondes
    
    try:
        # Capturer 5 images
        for i in range(5):
            time.sleep(1)  # Attendre 1 seconde
            
            # Récupérer l'image actuelle
            frame, timestamp = obs.get_current_frame()
            
            if frame:
                # Ajouter un texte avec le numéro de frame
                draw = ImageDraw.Draw(frame)
                draw.text((10, 10), f"Frame #{i+1}", fill=(255, 0, 0))
                
                # Enregistrer l'image
                output_path = f"example_obs31_continuous_{i+1}.jpg"
                frame.save(output_path)
                print(f"Image {i+1} enregistrée sous '{output_path}'")
            else:
                print(f"Échec de la récupération de l'image {i+1}")
    
    finally:
        # Arrêter la capture continue
        print("Arrêt de la capture continue...")
        obs.stop_capture()
        
        # Déconnecter
        obs.disconnect()

def example_adapter_usage():
    """
    Exemple d'utilisation de l'adaptateur OBS31
    """
    print("\n=== Exemple 3: Utilisation de OBS31Adapter ===")
    
    # Créer une instance de OBS31Adapter
    adapter = OBS31Adapter()
    
    # Activer le mode de test
    adapter.enable_test_images(True)
    
    # Attendre que la connexion s'établisse
    time.sleep(1)
    
    # Afficher les sources disponibles
    print(f"Sources vidéo: {adapter.video_sources}")
    print(f"Sources média: {adapter.media_sources}")
    
    # Capturer une image
    if adapter.video_sources:
        print(f"Tentative de capture de la source '{adapter.video_sources[0]}'...")
        frame = adapter.capture_frame(adapter.video_sources[0])
        
        if frame:
            print(f"Image capturée: {frame.size}")
            
            # Convertir en JPEG
            jpeg_data = adapter.get_frame_as_jpeg()
            if jpeg_data:
                # Enregistrer l'image JPEG
                output_path = "example_obs31_adapter.jpg"
                with open(output_path, 'wb') as f:
                    f.write(jpeg_data)
                print(f"Image JPEG enregistrée sous '{output_path}'")
        else:
            print("Échec de la capture d'image")
    
    # Si des sources média sont disponibles, récupérer leurs propriétés
    if adapter.media_sources:
        print("\nSources média disponibles:")
        for source in adapter.media_sources:
            print(f"  - {source}")
            
            # Récupérer les propriétés du média
            properties = adapter.get_media_properties(source)
            if properties:
                print(f"    Durée: {properties.get('duration', 'N/A')}")
                print(f"    Lecture en cours: {properties.get('playing', False)}")
    
    # Déconnecter
    adapter.disconnect()

if __name__ == "__main__":
    print("Démo d'utilisation de OBS31Capture pour OBS 31.0.2+")
    
    # Exécuter les exemples
    example_simple_capture()
    example_continuous_capture()
    example_adapter_usage()
    
    print("\nDémo terminée!")
