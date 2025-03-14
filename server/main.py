#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
from flask import Flask, request, jsonify, render_template
from config import Config
from capture.obs_capture import OBSCapture
from capture.stream_processor import StreamProcessor
from analysis.activity_classifier import ActivityClassifier
from database.db_manager import DBManager
from api.external_service import ExternalServiceClient

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__, 
    static_folder='../web/static',
    template_folder='../web/templates')

# Chargement de la configuration
config = Config()
app.config.from_object(config)

# Initialisation des composants
obs_capture = OBSCapture(config.OBS_HOST, config.OBS_PORT, config.OBS_PASSWORD)
stream_processor = StreamProcessor()
db_manager = DBManager(config.DATABASE_PATH)
activity_classifier = ActivityClassifier(model_path=config.MODEL_PATH)
external_service = ExternalServiceClient(config.EXTERNAL_SERVICE_URL, 
                                        config.EXTERNAL_SERVICE_API_KEY)

# Initialisation de la base de données
db_manager.init_db()

# Routes pour l'interface web
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/model-testing')
def model_testing():
    return render_template('model_testing.html')

# Routes API
@app.route('/api/activities', methods=['GET'])
def get_activities():
    start_time = request.args.get('start', type=int)
    end_time = request.args.get('end', type=int)
    activities = db_manager.get_activities(start_time, end_time)
    return jsonify(activities)

@app.route('/api/current-activity', methods=['GET'])
def get_current_activity():
    activity = db_manager.get_latest_activity()
    return jsonify(activity)

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    period = request.args.get('period', 'day')
    stats = db_manager.get_statistics(period)
    return jsonify(stats)

def start_activity_monitoring():
    """Démarrer la surveillance d'activité en continu"""
    logger.info("Démarrage de la surveillance d'activité")
    
    last_classification_time = 0
    
    while True:
        try:
            # Capture des flux OBS
            video_frame = obs_capture.get_video_frame()
            audio_data = obs_capture.get_audio_data()
            
            current_time = int(time.time())
            
            if video_frame is not None and audio_data is not None:
                # Traitement des flux
                processed_video = stream_processor.process_video(video_frame)
                processed_audio = stream_processor.process_audio(audio_data)
                
                # Classification toutes les 5 minutes
                if current_time - last_classification_time >= config.ANALYSIS_INTERVAL:
                    # Classification de l'activité
                    activity = activity_classifier.classify(processed_video, processed_audio)
                    
                    # Enregistrement en base de données
                    db_manager.save_activity(current_time, activity)
                    
                    # Envoi vers le service externe
                    logger.info(f"Activité détectée: {activity}")
                    external_service.send_activity(current_time, activity)
                    
                    # Mise à jour du temps de dernière classification
                    last_classification_time = current_time
            
            # Pause pour éviter une utilisation excessive des ressources
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Erreur pendant la surveillance: {str(e)}")
            time.sleep(5)  # Pause plus longue en cas d'erreur

if __name__ == "__main__":
    # Démarrage de l'application Flask dans un thread
    import threading
    flask_thread = threading.Thread(target=app.run, 
                                   kwargs={
                                       'host': config.FLASK_HOST,
                                       'port': config.FLASK_PORT,
                                       'debug': config.DEBUG,
                                       'use_reloader': False
                                   })
    flask_thread.daemon = True
    flask_thread.start()
    
    # Démarrage de la surveillance d'activité
    start_activity_monitoring()
