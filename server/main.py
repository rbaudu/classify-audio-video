import logging
import os
import sys
import signal
import time
import threading
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
from server.utils.error_system import init_error_system
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
    try:
        # Configurer les chemins
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        analysis_dir = os.path.join(data_dir, 'analysis')
        
        # Créer les répertoires s'ils n'existent pas
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(analysis_dir, exist_ok=True)
        
        # Initialiser le système de gestion d'erreurs
        logger.info("Initialisation du système de gestion d'erreurs")
        init_error_system()
        
        # Initialiser les composants dans l'ordre
        db_manager = DBManager()
        
        # Vérifier que la base de données est prête
        if not db_manager.check_connection():
            raise Exception("Impossible de se connecter à la base de données")
        
        external_service = ExternalServiceClient()
        
        # Initialiser le système de capture synchronisée
        app.sync_manager = SyncManager()
        
        # Attendre que la capture soit initialisée
        time.sleep(0.1)
        
        # Obtenir une référence à OBS Capture depuis SyncManager
        obs_capture = app.sync_manager.obs_capture
        
        # Initialiser le classificateur d'activité avec le SyncManager
        app.activity_classifier = ActivityClassifier(capture_manager=app.sync_manager)
        
        # Enregistrer les routes
        register_web_routes(app)
        register_api_routes(app, app.sync_manager, app.activity_classifier, db_manager, analysis_dir)
        register_video_routes(app, app.sync_manager)
        
        # Démarrer la capture synchronisée
        app.sync_manager.start_capture()
        
        # Vérifier que la capture a démarré correctement
        time.sleep(0.1)  # Laisser le temps de démarrer
        # Vérification modifiée pour éviter l'erreur
        if app.sync_manager._is_running:
            logger.info("Capture synchronisée démarrée avec succès")
        else:
            logger.error("Échec du démarrage de la capture synchronisée")
        
        # Démarrer l'analyse périodique avec le sync_manager correctement associé
        app.activity_classifier.start_periodic_analysis(sync_manager=app.sync_manager, interval=60)
        
        return app
        
    except Exception as e:
        logger.critical(f"Exception non gérée lors du démarrage: {str(e)}")
        raise

def run_app():
    logger.info("Démarrage du serveur classify-audio-video...")
    logger.info("Accédez à l'interface via http://localhost:5000")
    logger.info("Appuyez sur Ctrl+C pour arrêter le serveur")
    
    # Utiliser app.run() en mode développement
    app.run(host='0.0.0.0', port=5000)

def start_server():
    """Fonction de démarrage du serveur attendue par run.py"""
    try:
        global app
        app = create_app()
        # Lancer le serveur Flask dans un thread séparé pour pouvoir continuer l'exécution
        server_thread = threading.Thread(target=run_app)
        server_thread.daemon = True
        server_thread.start()
        return True
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur: {str(e)}")
        return False

if __name__ == '__main__':
    try:
        app = create_app()
        run_app()
    except Exception as e:
        logger.critical(f"Erreur fatale lors du démarrage: {str(e)}")
        sys.exit(1)
