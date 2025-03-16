import os
import time
import logging
import signal
import atexit
import threading
from flask import Flask

# Import des modules du projet
from server import WEB_PORT
from server.capture import SyncManager
from server.capture.stream_processor import StreamProcessor
from server.analysis.activity_classifier import ActivityClassifier
from server.database.db_manager import DBManager
from server.api.external_service import ExternalServiceClient
from server.routes.web_routes import register_web_routes
from server.routes.api_routes import register_api_routes
from server.analysis.analysis_manager import start_analysis_loop, stop_analysis_loop

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

# Initialisation de l'application Flask
app = Flask(__name__, 
           static_folder='../web/static',
           template_folder='../web/templates')

# Initialisation des classes principales
sync_manager = SyncManager()
stream_processor = StreamProcessor()
db_manager = DBManager()
activity_classifier = ActivityClassifier(sync_manager, stream_processor, db_manager)
external_service = ExternalServiceClient()

# Répertoire pour les analyses temporaires
ANALYSIS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'analyses')
os.makedirs(ANALYSIS_DIR, exist_ok=True)

def shutdown_server():
    """
    Fonction de nettoyage pour l'arrêt du serveur
    """
    logger.info("Arrêt du serveur en cours...")
    
    # Arrêter la boucle d'analyse
    stop_analysis_loop()
    
    # Arrêter la capture synchronisée
    sync_manager.stop()
    
    logger.info("Serveur arrêté avec succès")

def handle_signals(signum, frame):
    """
    Gère les signaux SIGINT et SIGTERM pour un arrêt propre
    """
    logger.info(f"Signal {signum} reçu, arrêt en cours...")
    shutdown_server()
    exit(0)

def start_server():
    """
    Démarre le serveur Flask et la boucle d'analyse
    """
    # Enregistrer les gestionnaires de signaux
    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)
    
    # Enregistrer la fonction de nettoyage
    atexit.register(shutdown_server)
    
    # Démarrer la capture synchronisée
    if not sync_manager.start():
        logger.error("Impossible de démarrer la capture synchronisée")
        return False
    else:
        logger.info("Capture synchronisée démarrée avec succès")
    
    # Démarrer la boucle d'analyse dans un thread
    start_analysis_loop(activity_classifier, db_manager, external_service)
    
    # Enregistrer les routes
    register_web_routes(app)
    register_api_routes(app, sync_manager, activity_classifier, db_manager, ANALYSIS_DIR)
    
    # Démarrer le serveur Flask
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False)
    
    return True

if __name__ == "__main__":
    start_server()
