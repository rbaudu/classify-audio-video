#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
from server.main import init_app, start_app

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,  # Changé à DEBUG pour plus d'informations
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Affichage du chemin de travail actuel pour le débogage
        current_dir = os.path.abspath(os.getcwd())
        logger.info(f"Répertoire de travail actuel: {current_dir}")
        
        # Liste des dossiers et fichiers importants
        web_templates_dir = os.path.join(current_dir, 'web', 'templates')
        logger.info(f"Chemin des templates: {web_templates_dir}")
        
        # Vérification si le dossier de templates existe
        if os.path.exists(web_templates_dir):
            logger.info(f"Le dossier des templates existe: {web_templates_dir}")
            # Liste des fichiers dans le dossier des templates
            template_files = os.listdir(web_templates_dir)
            logger.info(f"Fichiers dans le dossier des templates: {template_files}")
        else:
            logger.error(f"Le dossier des templates n'existe pas: {web_templates_dir}")
        
        logger.info("Initialisation de l'application...")
        app = init_app()
        
        # Afficher la configuration des dossiers de Flask
        logger.info(f"Flask static folder: {app.static_folder}")
        logger.info(f"Flask template folder: {app.template_folder}")
        
        # Vérifier si les dossiers existent
        if os.path.exists(app.template_folder):
            logger.info(f"Le dossier de templates configuré dans Flask existe.")
        else:
            logger.error(f"Le dossier de templates configuré dans Flask n'existe pas!")
            
        if os.path.exists(app.static_folder):
            logger.info(f"Le dossier statique configuré dans Flask existe.")
        else:
            logger.error(f"Le dossier statique configuré dans Flask n'existe pas!")
            
        start_app(app)
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {str(e)}")
        # Afficher la trace complète pour le débogage
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
