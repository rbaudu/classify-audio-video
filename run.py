#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

# Ajout du chemin du projet au sys.path pour résoudre les problèmes d'importation
project_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_path)

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("activity_classifier.log")
    ]
)
logger = logging.getLogger(__name__)

# Affichage des informations de débogage
logger.debug(f"Chemin du projet ajouté: {project_path}")
logger.debug(f"sys.path contient maintenant: {sys.path}")

# Importation du système de gestion d'erreurs avancé
from server.utils.error_system import init_error_system, error_boundary
from server.utils.error_handling import AppError, ErrorCode

# Importation et exécution de l'application Flask avec la fonction start_server
from server.main import start_server

if __name__ == "__main__":
    try:
        # Initialiser le système de gestion d'erreurs
        logger.info("Initialisation du système de gestion d'erreurs")
        init_error_system()
        
        # Démarrer le serveur dans un boundary d'erreur
        with error_boundary("server-startup", 
                          error_code=ErrorCode.INITIALIZATION_ERROR, 
                          log_level=logging.CRITICAL):
            logger.info("Démarrage du serveur classify-audio-video...")
            logger.info("Accédez à l'interface via http://localhost:5000")
            logger.info("Appuyez sur Ctrl+C pour arrêter le serveur")
            
            # Appel de la fonction start_server au lieu de lancer directement app.run
            # Cela permet de démarrer le gestionnaire de synchronisation audio/vidéo
            success = start_server()
            
            if not success:
                logger.critical("Échec du démarrage du serveur")
                sys.exit(1)
    except Exception as e:
        logger.critical(f"Exception non gérée lors du démarrage: {e}")
        sys.exit(1)
