#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de serveur combiné pour classify-audio-video.
Ce script fusionne la capture OBS avec le serveur Flask et résout les problèmes
de conflit de routes et d'interruption CTRL+C.
"""

import os
import sys
import logging
import signal
import threading
import time
import webbrowser
import argparse
from urllib.request import urlopen
from urllib.error import URLError

# Import des modules du projet
from server.config import Config
from server.database.db_manager import DBManager
from server.utils.error_system import ErrorSystem
from server.api.external_service import ExternalServiceClient
from server.capture.stream_processor import StreamProcessor
from server.capture.sync_manager import SyncManager
from server.analysis.activity_classifier import ActivityClassifier

# Import conditionnel des modules OBS selon la configuration
if Config.USE_OBS_31:
    # Utiliser OBS31 (compatible avec OBS 31.0.2+)
    if Config.USE_OBS_ADAPTER:
        # Approche avec adaptateur (recommandée)
        from server.capture.obs_31_adapter import OBS31Adapter as OBSHandler
    else:
        # Approche directe avec OBS31Capture
        from server.capture.obs_31_capture import OBS31Capture as OBSHandler
else:
    # Utiliser l'ancienne OBSCapture (pour compatibilité avec anciennes versions OBS)
    from server.capture.obs_capture import OBSCapture as OBSHandler

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("combined_server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Variables globales
app_instance = None
sync_manager = None
activity_classifier = None
flask_thread = None
server_ready = False
shutting_down = False

def parse_arguments():
    """Parse les arguments de la ligne de commande"""
    parser = argparse.ArgumentParser(description='Serveur combiné pour classify-audio-video')
    
    # Options de configuration OBS
    parser.add_argument('--obs-version', choices=['31', 'legacy'], default='31',
                      help='Version d\'OBS à utiliser (31 pour OBS 31.0.2+, legacy pour versions antérieures)')
    
    parser.add_argument('--use-adapter', choices=['true', 'false'], default='true',
                      help='Utiliser l\'adaptateur OBS31Adapter (true) ou directement OBS31Capture (false)')
    
    # Options pour l'hôte/port OBS
    parser.add_argument('--obs-host', default=Config.OBS_HOST,
                      help=f'Hôte OBS WebSocket (défaut: {Config.OBS_HOST})')
    
    parser.add_argument('--obs-port', type=int, default=Config.OBS_PORT,
                      help=f'Port OBS WebSocket (défaut: {Config.OBS_PORT})')
    
    # Options de configuration Flask
    parser.add_argument('--flask-host', default=Config.FLASK_HOST,
                      help=f'Hôte du serveur Flask (défaut: {Config.FLASK_HOST})')
    
    parser.add_argument('--flask-port', type=int, default=Config.FLASK_PORT,
                      help=f'Port du serveur Flask (défaut: {Config.FLASK_PORT})')
    
    # Option pour ouvrir automatiquement le navigateur
    parser.add_argument('--open-browser', action='store_true', 
                      help='Ouvrir automatiquement le navigateur')
    
    return parser.parse_args()

def signal_handler(sig, frame):
    """Gestionnaire de signal pour CTRL+C et SIGTERM"""
    global shutting_down
    
    if shutting_down:
        return
    
    shutting_down = True
    logger.info(f"Signal {sig} reçu. Arrêt propre du serveur...")
    
    # Arrêter les composants dans l'ordre inverse de leur démarrage
    shutdown_server()
    
    sys.exit(0)

def shutdown_server():
    """Arrête le serveur et tous ses composants"""
    global sync_manager, activity_classifier
    
    logger.info("Arrêt des composants...")
    
    # Arrêter le classificateur d'activité
    if activity_classifier:
        logger.info("Arrêt du classificateur d'activité...")
        try:
            if hasattr(activity_classifier, 'stop_analysis_loop'):
                activity_classifier.stop_analysis_loop()
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du classificateur: {e}")
    
    # Arrêter le gestionnaire de synchronisation
    if sync_manager:
        logger.info("Arrêt du gestionnaire de synchronisation...")
        try:
            sync_manager.stop()
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du gestionnaire de synchronisation: {e}")
    
    logger.info("Tous les composants ont été arrêtés")

def check_server_status(host, port, max_wait=30):
    """Vérifie si le serveur Flask est prêt à recevoir des connexions"""
    global server_ready
    
    # Déterminer l'URL à vérifier (utiliser localhost si host est 0.0.0.0)
    check_host = "localhost" if host == "0.0.0.0" else host
    url = f"http://{check_host}:{port}"
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = urlopen(url)
            if response.getcode() == 200:
                server_ready = True
                logger.info(f"Serveur prêt à l'adresse {url}")
                return True
        except URLError:
            # Serveur pas encore prêt
            time.sleep(0.5)
    
    logger.warning(f"Impossible de confirmer que le serveur est prêt après {max_wait} secondes.")
    return False

def open_browser_when_ready(host, port, max_wait=30):
    """Ouvre le navigateur une fois que le serveur est prêt"""
    global server_ready
    
    # Déterminer l'URL à ouvrir (utiliser localhost si host est 0.0.0.0)
    browser_host = "localhost" if host == "0.0.0.0" else host
    url = f"http://{browser_host}:{port}"
    
    # Vérifier si le serveur est prêt
    check_thread = threading.Thread(target=check_server_status, args=(host, port, max_wait), daemon=True)
    check_thread.start()
    
    # Attendre que le serveur soit prêt ou un délai maximum
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if server_ready:
            logger.info(f"Ouverture du navigateur à l'adresse {url}")
            webbrowser.open(url)
            return
        time.sleep(0.5)
    
    # Ouvrir le navigateur même si le serveur n'est pas confirmé comme prêt
    logger.warning("Ouverture du navigateur même si le serveur n'a pas confirmé être prêt")
    webbrowser.open(url)

def init_flask_app():
    """Initialise l'application Flask sans conflits de routes"""
    from flask import Flask, render_template
    
    # Déterminer les chemins des répertoires
    root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    templates_dir = os.path.join(root_dir, 'web', 'templates')
    static_dir = os.path.join(root_dir, 'web', 'static')
    
    # Créer l'application Flask
    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir
    )
    
    # Configuration de l'application
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Route principale - définition unique pour éviter les conflits
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Routes standard
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')
    
    @app.route('/statistics')
    def statistics():
        return render_template('statistics.html')
    
    @app.route('/history')
    def history():
        return render_template('history.html')
    
    @app.route('/model_testing')
    def model_testing():
        return render_template('model_testing.html')
    
    @app.route('/settings')
    def settings():
        return render_template('settings.html')
    
    # Gestion des erreurs
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Erreur 500: {e}")
        return render_template('500.html'), 500
    
    # Stocker les composants dans l'application
    app.config['DB_MANAGER'] = None
    app.config['SYNC_MANAGER'] = None
    app.config['ACTIVITY_CLASSIFIER'] = None
    
    logger.info("Application Flask initialisée avec succès")
    
    return app

def setup_api_routes(app, db_manager, sync_manager, activity_classifier):
    """Configure les routes API pour l'application Flask"""
    from server.routes.api_routes import register_api_routes
    
    try:
        register_api_routes(app, db_manager, sync_manager, activity_classifier)
        logger.info("Routes API enregistrées avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement des routes API: {e}")

def run_flask_app(app, host, port):
    """Exécute l'application Flask dans un thread principal"""
    try:
        logger.info(f"Démarrage du serveur Flask sur {host}:{port}")
        app.run(host=host, port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de Flask: {e}")
        import traceback
        logger.error(traceback.format_exc())

def initialize_components():
    """Initialise tous les composants du système"""
    global sync_manager, activity_classifier
    
    # Initialisation du système de gestion d'erreurs
    logger.info("Initialisation du système de gestion d'erreurs")
    error_system = ErrorSystem()
    
    # Initialisation de la base de données
    logger.info("Initialisation de la base de données")
    db_manager = DBManager()
    
    # Initialisation du client de service externe
    logger.info("Initialisation du client de service externe")
    external_service = ExternalServiceClient(url=Config.EXTERNAL_SERVICE_URL)
    
    # Initialisation de la capture OBS (selon la configuration)
    obs_version = "31" if Config.USE_OBS_31 else "legacy"
    adapter_mode = "avec adaptateur" if Config.USE_OBS_ADAPTER and Config.USE_OBS_31 else "direct"
    logger.info(f"Initialisation de la capture OBS version {obs_version} {adapter_mode}")
    
    obs_capture = OBSHandler(
        host=Config.OBS_HOST, 
        port=Config.OBS_PORT, 
        password=Config.OBS_PASSWORD
    )
    
    # Activer le mode de test pour les images alternatives en cas d'échec
    if hasattr(obs_capture, 'enable_test_images'):
        obs_capture.enable_test_images(True)
    
    # Initialisation du processeur de flux
    logger.info("Initialisation du processeur de flux")
    stream_processor = StreamProcessor(
        video_resolution=Config.VIDEO_RESOLUTION,
        audio_sample_rate=Config.AUDIO_SAMPLE_RATE
    )
    
    # Initialisation du gestionnaire de synchronisation
    logger.info("Initialisation du gestionnaire de synchronisation")
    sync_manager = SyncManager(
        obs_capture=obs_capture,
        pyaudio_capture=None,  # On n'utilise pas PyAudio pour simplifier
        stream_processor=stream_processor
    )
    
    # Initialisation du classificateur d'activités
    logger.info("Initialisation du classificateur d'activités")
    activity_classifier = ActivityClassifier(sync_manager=sync_manager)
    
    return {
        'error_system': error_system,
        'db_manager': db_manager,
        'external_service': external_service,
        'obs_capture': obs_capture,
        'stream_processor': stream_processor,
        'sync_manager': sync_manager,
        'activity_classifier': activity_classifier
    }

def main():
    """Fonction principale"""
    global app_instance, sync_manager, activity_classifier, flask_thread
    
    try:
        # Installer le gestionnaire de signal pour CTRL+C et SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Analyser les arguments
        args = parse_arguments()
        
        # Mettre à jour la configuration selon les arguments
        Config.OBS_HOST = args.obs_host
        Config.OBS_PORT = args.obs_port
        Config.FLASK_HOST = args.flask_host
        Config.FLASK_PORT = args.flask_port
        Config.USE_OBS_31 = args.obs_version == '31'
        Config.USE_OBS_ADAPTER = args.use_adapter == 'true'
        
        # Afficher la bannière
        print("="*70)
        print("          SERVEUR COMBINÉ - CLASSIFY AUDIO VIDEO")
        print("="*70)
        print("")
        print("Ce script démarre la capture OBS et le serveur Flask dans un seul processus.")
        print("Surveillez les logs pour les informations de démarrage.")
        print("")
        print("Appuyez sur Ctrl+C pour arrêter proprement le serveur.")
        print("="*70)
        print("")
        
        # Initialiser l'application Flask sans conflits de routes
        logger.info("Initialisation de l'application Flask")
        app_instance = init_flask_app()
        
        # Initialiser et démarrer les composants
        logger.info("Initialisation des composants...")
        components = initialize_components()
        
        # Récupérer les composants
        sync_manager = components['sync_manager']
        activity_classifier = components['activity_classifier']
        db_manager = components['db_manager']
        
        # Intégrer les composants à l'application Flask
        app_instance.config['DB_MANAGER'] = db_manager
        app_instance.config['SYNC_MANAGER'] = sync_manager
        app_instance.config['ACTIVITY_CLASSIFIER'] = activity_classifier
        
        # Configurer les routes API
        setup_api_routes(app_instance, db_manager, sync_manager, activity_classifier)
        
        # Démarrer la capture et l'analyse
        logger.info("Démarrage du gestionnaire de synchronisation...")
        sync_manager.start()
        
        logger.info("Démarrage du classificateur d'activité...")
        activity_classifier.start_analysis_loop()
        
        # Ouvrir le navigateur si demandé
        if args.open_browser:
            logger.info("Le navigateur s'ouvrira automatiquement quand le serveur sera prêt")
            browser_thread = threading.Thread(
                target=open_browser_when_ready, 
                args=(args.flask_host, args.flask_port, 15),
                daemon=True
            )
            browser_thread.start()
        
        # Démarrer Flask (cette fonction bloque jusqu'à ce que le serveur s'arrête)
        logger.info(f"Démarrage du serveur Flask sur {args.flask_host}:{args.flask_port}")
        run_flask_app(app_instance, args.flask_host, args.flask_port)
        
    except KeyboardInterrupt:
        # Cette partie ne devrait pas être atteinte grâce au gestionnaire de signal,
        # mais c'est une précaution supplémentaire
        logger.info("Interruption clavier détectée. Arrêt du serveur...")
        shutdown_server()
        
    except Exception as e:
        logger.error(f"Erreur globale: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
