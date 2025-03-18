#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
import argparse
from server.main import init_app, start_app
from server.config import Config

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,  # Changé à DEBUG pour plus d'informations
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse les arguments de la ligne de commande"""
    parser = argparse.ArgumentParser(description='Serveur de classification d\'activité avec analyse audio/vidéo')
    
    # Options de configuration OBS
    parser.add_argument('--obs-version', choices=['31', 'legacy'], default='31',
                      help='Version d\'OBS à utiliser (31 pour OBS 31.0.2+, legacy pour versions antérieures)')
    
    parser.add_argument('--use-adapter', choices=['true', 'false'], default='true',
                      help='Utiliser l\'adaptateur OBS31Adapter (true) ou directement OBS31Capture (false)')
    
    # Ajout d'options pour l'hôte/port OBS
    parser.add_argument('--obs-host', default=Config.OBS_HOST,
                      help=f'Hôte OBS WebSocket (défaut: {Config.OBS_HOST})')
    
    parser.add_argument('--obs-port', type=int, default=Config.OBS_PORT,
                      help=f'Port OBS WebSocket (défaut: {Config.OBS_PORT})')
    
    # Options de configuration Flask
    parser.add_argument('--flask-host', default=Config.FLASK_HOST,
                      help=f'Hôte du serveur Flask (défaut: {Config.FLASK_HOST})')
    
    parser.add_argument('--flask-port', type=int, default=Config.FLASK_PORT,
                      help=f'Port du serveur Flask (défaut: {Config.FLASK_PORT})')
    
    return parser.parse_args()

if __name__ == "__main__":
    try:
        # Analyser les arguments de la ligne de commande
        args = parse_arguments()
        
        # Mettre à jour la configuration selon les arguments
        os.environ['USE_OBS_31'] = 'true' if args.obs_version == '31' else 'false'
        os.environ['USE_OBS_ADAPTER'] = args.use_adapter
        os.environ['OBS_HOST'] = args.obs_host
        os.environ['OBS_PORT'] = str(args.obs_port)
        os.environ['FLASK_HOST'] = args.flask_host
        os.environ['FLASK_PORT'] = str(args.flask_port)
        
        # Afficher la configuration OBS
        logger.info(f"Configuration OBS: version={args.obs_version}, adapter={args.use_adapter}, host={args.obs_host}, port={args.obs_port}")
        
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
