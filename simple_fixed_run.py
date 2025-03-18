#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Version simplifiée et directement corrigée du fichier run.py
Utiliser ce fichier au lieu de run.py pour éviter les problèmes
"""

import logging
import sys
import os
import argparse
import signal
import threading
import time
import atexit
from server.main import init_app, start_app
from server.config import Config

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Variable globale pour l'application Flask
app_instance = None
server_thread = None
is_shutting_down = False

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

def shutdown_server():
    """Arrête le serveur de manière propre"""
    global app_instance, is_shutting_down, server_thread
    
    # Éviter les arrêts multiples
    if is_shutting_down:
        return
    
    is_shutting_down = True
    logger.info("Arrêt du serveur en cours...")
    
    # Fermer manuellement toutes les connexions et threads
    if app_instance:
        # Récupérer les objets importants
        try:
            sync_manager = app_instance.config.get('SYNC_MANAGER')
            if sync_manager:
                logger.info("Arrêt du gestionnaire de synchronisation...")
                sync_manager.stop()
            
            activity_classifier = app_instance.config.get('ACTIVITY_CLASSIFIER')
            if activity_classifier and hasattr(activity_classifier, 'stop_analysis_loop'):
                logger.info("Arrêt du classificateur d'activité...")
                activity_classifier.stop_analysis_loop()
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt des composants: {e}")
    
    logger.info("Arrêt du serveur terminé.")
    
    # Utiliser sys.exit au lieu de os._exit pour permettre aux ressources d'être libérées
    sys.exit(0)

def signal_handler(sig, frame):
    """
    Gestionnaire de signal pour CTRL+C (SIGINT) et SIGTERM
    """
    logger.info(f"Signal d'interruption reçu ({sig}). Arrêt du serveur...")
    
    # Permettre l'arrêt même si d'autres threads sont en cours
    if server_thread and server_thread.is_alive():
        logger.info("Attente de la fin du thread serveur...")
    
    # Appeler shutdown_server pour nettoyer et arrêter
    shutdown_server()

def run_flask_app(app):
    """Fonction pour exécuter Flask dans un thread séparé"""
    logger.info(f"Démarrage du serveur Flask sur {Config.FLASK_HOST}:{Config.FLASK_PORT}")
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    try:
        # Enregistrer le gestionnaire de signal pour CTRL+C et SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Enregistrer la fonction de nettoyage à la sortie
        atexit.register(shutdown_server)
        
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
        app_instance = init_app()
        
        # Afficher la configuration des dossiers de Flask
        logger.info(f"Flask static folder: {app_instance.static_folder}")
        logger.info(f"Flask template folder: {app_instance.template_folder}")
        
        # Vérifier si les dossiers existent
        if os.path.exists(app_instance.template_folder):
            logger.info(f"Le dossier de templates configuré dans Flask existe.")
        else:
            logger.error(f"Le dossier de templates configuré dans Flask n'existe pas!")
            
        if os.path.exists(app_instance.static_folder):
            logger.info(f"Le dossier statique configuré dans Flask existe.")
        else:
            logger.error(f"Le dossier statique configuré dans Flask n'existe pas!")
        
        # Démarrer les composants en arrière-plan (capture, synchronisation, etc.)
        logger.info("Démarrage des composants en arrière-plan...")
        start_app(app_instance)
        
        logger.info("Démarrage du serveur classify-audio-video...")
        logger.info(f"Accédez à l'interface via http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
        logger.info("Appuyez sur Ctrl+C pour arrêter le serveur")
        
        # Démarrer le serveur Flask dans un thread séparé - NON DAEMON pour permettre l'arrêt propre
        server_thread = threading.Thread(target=run_flask_app, args=(app_instance,), daemon=False)
        server_thread.start()
        
        # Maintenir le thread principal en vie jusqu'à un CTRL+C ou une erreur
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            # Cette partie sera exécutée si CTRL+C est pressé
            logger.info("Interruption clavier détectée. Arrêt du serveur...")
            shutdown_server()
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {str(e)}")
        # Afficher la trace complète pour le débogage
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
