import logging
import os
import sys
import signal
import time
from flask import Flask

# Configuration de base du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Importer les modules du serveur
from server.capture.sync_manager import SyncManager
from server.analysis.activity_classifier import ActivityClassifier
from server.database.db_manager import DBManager
from server.api.external_service import ExternalServiceClient
from server.utils.error_system import ErrorSystem
from server.routes.web_routes import register_web_routes
from server.routes.api_routes import register_api_routes
from server.routes.video_routes import register_video_routes  # Nouvelle importation

# Créer l'application Flask
app = Flask(__name__, 
           static_folder='../web/static', 
           template_folder='../web/templates')

# Définir le gestionnaire de signal Ctrl+C
def signal_handler(sig, frame):
    print("\nArrêt du serveur...")
    # Nettoyer les ressources
    if hasattr(app, 'sync_manager'):
        logger.info("Arrêt du gestionnaire de synchronisation...")
        app.sync_manager.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def create_app():
    # Configurer les chemins
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    analysis_dir = os.path.join(data_dir, 'analysis')
    
    # Créer les répertoires s'ils n'existent pas
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(analysis_dir, exist_ok=True)
    
    # Initialiser les composants
    db_manager = DBManager()
    external_service = ExternalServiceClient()
    
    # Initialiser le système de capture synchronisée
    app.sync_manager = SyncManager()
    
    # Initialiser le classificateur d'activité
    app.activity_classifier = ActivityClassifier(model_path=None)
    
    # Initialiser le système de gestion d'erreurs
    logger.info("Initialisation du système de gestion d'erreurs")
    app.error_system = ErrorSystem()
    
    # Enregistrer les routes
    register_web_routes(app)
    register_api_routes(app, app.sync_manager, app.activity_classifier, db_manager, analysis_dir)
    register_video_routes(app, app.sync_manager)  # Nouvelle registration des routes vidéo
    
    # Démarrer la capture synchronisée
    app.sync_manager.start_capture()
    
    # Vérifier que la capture a démarré correctement
    time.sleep(0.1)  # Laisser le temps de démarrer
    if app.sync_manager.is_running():
        logger.info("Capture synchronisée démarrée avec succès")
    else:
        logger.error("Échec du démarrage de la capture synchronisée")
    
    # Démarrer l'analyse périodique
    app.activity_classifier.start_periodic_analysis(app.sync_manager)
    
    return app

def run_app():
    logger.info("Démarrage du serveur classify-audio-video...")
    logger.info("Accédez à l'interface via http://localhost:5000")
    logger.info("Appuyez sur Ctrl+C pour arrêter le serveur")
    
    # Utiliser app.run() en mode développement
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    app = create_app()
    run_app()
