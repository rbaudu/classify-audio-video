#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script d'installation des dépendances requises pour classify-audio-video
"""

import subprocess
import sys
import os

def install_dependencies():
    """
    Installe les dépendances requises
    """
    print("Installation des dépendances pour classify-audio-video...")
    
    # Dépendances principales
    dependencies = [
        'pillow',            # Traitement d'images
        'numpy',             # Traitement numérique
        'obsws-python>=1.4.0'  # Client OBS WebSocket compatible avec OBS 31.0.2
    ]
    
    # Installer les dépendances avec pip
    try:
        pip_command = [sys.executable, '-m', 'pip', 'install', '--upgrade']
        pip_command.extend(dependencies)
        
        print(f"Exécution de: {' '.join(pip_command)}")
        result = subprocess.run(pip_command, check=True)
        
        if result.returncode == 0:
            print("✅ Dépendances installées avec succès!")
        else:
            print("⚠️ Des erreurs se sont produites lors de l'installation des dépendances.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation des dépendances: {e}")
        sys.exit(1)
    
    # Vérifier la version de obsws-python
    try:
        import obsws_python
        print(f"Version de obsws-python installée: {obsws_python.__version__}")
        
        # Imprimer des informations sur le package pour aider au débogage
        print("\nInformation sur les fonctionnalités disponibles dans obsws-python:")
        
        # Vérifier si le module requests existe
        has_requests = hasattr(obsws_python, 'requests')
        print(f"- Module 'requests' disponible: {'✅' if has_requests else '❌'}")
        
        # Si 'requests' est disponible, vérifier GetSourceScreenshot
        if has_requests:
            has_screenshot = hasattr(obsws_python.requests, 'GetSourceScreenshot')
            print(f"- Classe 'GetSourceScreenshot' disponible: {'✅' if has_screenshot else '❌'}")
    except ImportError:
        print("❌ Impossible d'importer obsws-python")
    
    print("\nPour utiliser la classe OBS31Capture avec OBS 31.0.2+, exécutez:")
    print("  python tests/test_obs_31_api.py  # Pour explorer l'API disponible")
    print("  python tests/test_obs_31_capture.py  # Pour tester la capture d'image")

if __name__ == "__main__":
    install_dependencies()
