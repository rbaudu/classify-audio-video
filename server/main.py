# -*- coding: utf-8 -*-
"""
Module principal du serveur
"""

import logging
import os
import threading
from flask import Flask

# Import des modules internes
from server.utils.error_system import ErrorSystem
from server.database.db_manager import DBManager
from server.api.external_service import ExternalServiceClient
from server.capture.pyaudio_capture import PyAudioCapture
from server.capture.stream_processor import StreamProcessor
from server.capture.sync_manager import SyncManager
from server.analysis.activity_classifier import ActivityClassifier
from server.routes.api_routes import register_api_routes
from server.routes.web_routes import register_web_routes
from server.flask_app import create_app
from server.config import Config

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

logger = logging.getLogger(__name__)

def init_app():
    """Initialise l'application Flask et les composants nécessaires"""
    
    # Initialisation du système de gestion d'erreurs
    logger.info("Initialisation du système de gestion d'erreurs")
    error_system = ErrorSystem()
    
    # Initialisation de la base de données
    db_manager = DBManager()
    
    # Initialisation du client de service externe
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
    
    # Initialisation de la capture audio
    pyaudio_capture = PyAudioCapture()
    
    # Initialisation du processeur de flux
    stream_processor = StreamProcessor(
        video_resolution=Config.VIDEO_RESOLUTION,
        audio_sample_rate=Config.AUDIO_SAMPLE_RATE
    )
    
    # Initialisation du gestionnaire de synchronisation
    sync_manager = SyncManager(
        obs_capture=obs_capture,
        pyaudio_capture=pyaudio_capture,
        stream_processor=stream_processor
    )
    
    # Initialisation du classificateur d'activités
    activity_classifier = ActivityClassifier(sync_manager=sync_manager)
    
    # Création de l'app Flask avec notre module dédié
    app = create_app()
    
    # Configuration Flask à partir de Config
    app.debug = Config.DEBUG
    
    # Enregistrement des routes API
    register_api_routes(app, db_manager, sync_manager, activity_classifier)
    
    # Enregistrement des routes Web
    register_web_routes(app)
    
    # Stockage des objets dans le contexte de l'application
    app.config['DB_MANAGER'] = db_manager
    app.config['SYNC_MANAGER'] = sync_manager
    app.config['ACTIVITY_CLASSIFIER'] = activity_classifier
    app.config['ERROR_SYSTEM'] = error_system
    
    return app

def start_app(app):
    """Démarre l'application Flask et la capture"""
    
    # Récupération des objets depuis le contexte de l'application
    sync_manager = app.config['SYNC_MANAGER']
    activity_classifier = app.config['ACTIVITY_CLASSIFIER']
    
    # Démarrage de la capture dans un thread séparé pour ne pas bloquer le serveur Flask
    def start_capture_thread():
        try:
            # Démarrage de la capture
            sync_manager.start()
            
            # Démarrage de l'analyse périodique
            activity_classifier.start_analysis_loop()
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la capture: {e}")
    
    # Créer et démarrer le thread de capture
    capture_thread = threading.Thread(target=start_capture_thread, daemon=True)
    capture_thread.start()
    
    logger.info("Démarrage du serveur classify-audio-video...")
    logger.info(f"Accédez à l'interface via http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    logger.info("Appuyez sur Ctrl+C pour arrêter le serveur")
    
    # Démarrage du serveur Flask
    # NB: N'utilisez pas threaded=True pour les tests, cela peut causer des problèmes de thread
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.DEBUG, use_reloader=False)
