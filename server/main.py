import os
import time
import logging
import signal
import atexit
import threading
import sys
import traceback
from flask import Flask, jsonify, request

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
from server.utils.error_handling import (
    AppError, ErrorCode, CaptureError, DatabaseError, 
    log_exception, handle_exceptions
)

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

# Événement global pour la gestion de l'arrêt
stop_event = threading.Event()

# Initialisation de l'application Flask
app = Flask(__name__, 
           static_folder='../web/static',
           template_folder='../web/templates')

# Initialisation des classes principales (avec gestion d'erreurs)
try:
    sync_manager = SyncManager(stop_event=stop_event)
    stream_processor = StreamProcessor()
    db_manager = DBManager()
    activity_classifier = ActivityClassifier(sync_manager, stream_processor, db_manager)
    external_service = ExternalServiceClient()
except Exception as e:
    logger.critical("Erreur lors de l'initialisation des composants principaux de l'application")
    log_exception(e)
    sys.exit(1)

# Répertoire pour les analyses temporaires
ANALYSIS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'analyses')
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# Variable de contrôle pour l'arrêt du serveur
server_shutdown_requested = False

# Gestionnaires d'erreurs Flask globaux
@app.errorhandler(404)
def not_found(error):
    """Gestionnaire pour les erreurs 404 Not Found"""
    if request.path.startswith('/api/'):
        # Format JSON pour les routes API
        error_data = {
            'error': True,
            'code': ErrorCode.FILE_NOT_FOUND_ERROR.value,
            'code_name': ErrorCode.FILE_NOT_FOUND_ERROR.name,
            'message': f"Ressource non trouvée: {request.path}"
        }
        logger.warning(f"API 404: {request.path}")
        return jsonify(error_data), 404
    else:
        # Format HTML pour les routes web
        logger.warning(f"Web 404: {request.path}")
        return app.send_static_file('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Gestionnaire pour les erreurs 500 Internal Server Error"""
    logger.error(f"Erreur serveur 500: {str(error)}")
    log_exception(error)
    
    if request.path.startswith('/api/'):
        # Format JSON pour les routes API
        error_data = {
            'error': True,
            'code': ErrorCode.UNKNOWN_ERROR.value,
            'code_name': ErrorCode.UNKNOWN_ERROR.name,
            'message': "Erreur interne du serveur"
        }
        return jsonify(error_data), 500
    else:
        # Format HTML pour les routes web
        return app.send_static_file('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Gestionnaire pour toutes les exceptions non gérées"""
    logger.error(f"Exception non gérée: {str(e)}")
    log_exception(e)
    
    if request.path.startswith('/api/'):
        # Format JSON pour les routes API
        error_data = {
            'error': True,
            'code': ErrorCode.UNKNOWN_ERROR.value,
            'code_name': ErrorCode.UNKNOWN_ERROR.name,
            'message': "Une exception non gérée s'est produite",
            'details': {
                'exception_type': type(e).__name__,
                'exception_message': str(e)
            }
        }
        return jsonify(error_data), 500
    else:
        # Format HTML pour les routes web
        return app.send_static_file('500.html'), 500

# Fonction pour arrêter proprement Flask
def shutdown_flask():
    """Fonction pour arrêter le serveur Flask depuis un gestionnaire de signal"""
    global server_shutdown_requested
    
    if server_shutdown_requested:
        return  # Éviter les appels multiples
    
    server_shutdown_requested = True
    
    # Utiliser le signal SIGTERM pour forcer l'arrêt de Flask après un délai si nécessaire
    def emergency_shutdown():
        time.sleep(5)  # Attendre 5 secondes pour l'arrêt propre
        if not stop_event.is_set():
            logger.critical("Arrêt d'urgence du serveur après délai d'attente")
            os.kill(os.getpid(), signal.SIGKILL)  # Force l'arrêt
    
    # Démarrer un thread d'arrêt d'urgence
    emergency = threading.Thread(target=emergency_shutdown)
    emergency.daemon = True
    emergency.start()
    
    logger.info("Demande d'arrêt du serveur Flask initiée")
    try:
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Non exécuté avec le serveur de développement Werkzeug')
        func()
        logger.info("Serveur Flask arrêté")
    except Exception as e:
        logger.error(f"Impossible d'arrêter proprement Flask: {e}")

@handle_exceptions
def shutdown_server():
    """
    Fonction de nettoyage pour l'arrêt du serveur
    """
    logger.info("Arrêt du serveur en cours...")
    
    # Signaler l'arrêt à tous les composants
    stop_event.set()
    
    try:
        # Arrêter la boucle d'analyse
        logger.info("Arrêt de la boucle d'analyse...")
        stop_analysis_loop(timeout=3.0)
    except Exception as e:
        logger.error("Erreur lors de l'arrêt de la boucle d'analyse")
        log_exception(e)
    
    try:
        # Arrêter la capture synchronisée
        logger.info("Arrêt de la capture synchronisée...")
        sync_manager.stop(timeout=3.0)
    except Exception as e:
        logger.error("Erreur lors de l'arrêt de la capture synchronisée")
        log_exception(e)
    
    logger.info("Serveur arrêté avec succès")

def handle_signals(signum, frame):
    """
    Gère les signaux SIGINT et SIGTERM pour un arrêt propre
    """
    logger.info(f"Signal {signum} reçu, arrêt en cours...")
    
    # Définir un timeout pour l'arrêt
    MAX_SHUTDOWN_TIME = 10  # secondes
    
    # Démarrer un timer pour forcer l'arrêt si nécessaire
    def force_exit():
        logger.critical("Délai d'arrêt dépassé, arrêt forcé")
        os._exit(1)  # Sortie forcée sans nettoyage
    
    timer = threading.Timer(MAX_SHUTDOWN_TIME, force_exit)
    timer.daemon = True
    timer.start()
    
    try:
        # Signaler l'arrêt global
        stop_event.set()
        
        # Arrêter le serveur Flask
        shutdown_flask()
        
        # Arrêter proprement les composants
        shutdown_server()
        
        # Annuler le timer si tout s'est bien passé
        timer.cancel()
    except Exception as e:
        logger.critical("Erreur lors de l'arrêt propre du serveur")
        log_exception(e)
    
    # Sortir après l'arrêt propre
    sys.exit(0)

@handle_exceptions
def start_server():
    """
    Démarre le serveur Flask et la boucle d'analyse
    """
    # Réinitialiser l'événement d'arrêt
    stop_event.clear()
    
    # Enregistrer les gestionnaires de signaux
    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)
    
    # Enregistrer la fonction de nettoyage
    atexit.register(shutdown_server)
    
    # Démarrer la capture synchronisée
    try:
        if not sync_manager.start():
            error = CaptureError(
                ErrorCode.SYNC_ERROR,
                "Impossible de démarrer la capture synchronisée",
                details={"component": "sync_manager"}
            )
            error.log()
            return False
        logger.info("Capture synchronisée démarrée avec succès")
    except Exception as e:
        error = CaptureError(
            ErrorCode.INITIALIZATION_ERROR, 
            "Erreur lors du démarrage de la capture synchronisée",
            details={"component": "sync_manager"},
            original_exception=e
        )
        error.log(logging.CRITICAL)
        return False
    
    # Démarrer la boucle d'analyse dans un thread
    try:
        start_analysis_loop(activity_classifier, db_manager, external_service)
    except Exception as e:
        error = AppError(
            ErrorCode.INITIALIZATION_ERROR,
            "Erreur lors du démarrage de la boucle d'analyse",
            details={"component": "analysis_loop"},
            original_exception=e
        )
        error.log(logging.CRITICAL)
        return False
    
    # Enregistrer les routes
    try:
        register_web_routes(app)
        register_api_routes(app, sync_manager, activity_classifier, db_manager, ANALYSIS_DIR)
    except Exception as e:
        error = AppError(
            ErrorCode.INITIALIZATION_ERROR,
            "Erreur lors de l'enregistrement des routes",
            details={"component": "routes"},
            original_exception=e
        )
        error.log(logging.CRITICAL)
        return False
    
    # Démarrer le serveur Flask
    try:
        app.run(host='0.0.0.0', port=WEB_PORT, debug=False)
    except Exception as e:
        error = AppError(
            ErrorCode.INITIALIZATION_ERROR,
            "Erreur lors du démarrage du serveur Flask",
            details={"host": "0.0.0.0", "port": WEB_PORT},
            original_exception=e
        )
        error.log(logging.CRITICAL)
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = start_server()
        if not success:
            logger.critical("Échec du démarrage du serveur")
            sys.exit(1)
    except Exception as e:
        logger.critical("Exception non gérée lors du démarrage du serveur")
        log_exception(e)
        sys.exit(1)
