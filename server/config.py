#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

class Config:
    # Configuration de l'application Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'une-cle-secrete-tres-difficile-a-deviner'
    DEBUG = os.environ.get('FLASK_DEBUG') or False
    FLASK_HOST = os.environ.get('FLASK_HOST') or '0.0.0.0'
    FLASK_PORT = int(os.environ.get('FLASK_PORT') or 5000)
    
    # Configuration OBS
    OBS_HOST = os.environ.get('OBS_HOST') or 'localhost'
    OBS_PORT = int(os.environ.get('OBS_PORT') or 4444)
    OBS_PASSWORD = os.environ.get('OBS_PASSWORD') or ''
    
    # Configuration des chemins
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, '..', 'data', 'activity.db')
    MODEL_PATH = os.path.join(BASE_DIR, '..', 'models', 'activity_classifier.h5')
    
    # Configuration du service externe
    EXTERNAL_SERVICE_URL = os.environ.get('EXTERNAL_SERVICE_URL') or 'https://api.exemple.com/activity'
    EXTERNAL_SERVICE_API_KEY = os.environ.get('EXTERNAL_SERVICE_API_KEY') or 'votre-cle-api'
    
    # Configuration des activités
    ACTIVITY_CLASSES = [
        'endormi',
        'à table',
        'lisant',
        'au téléphone',
        'en conversation',
        'occupé',
        'inactif'
    ]
    
    # Configuration des paramètres de capture
    VIDEO_RESOLUTION = (640, 480)
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    
    # Configuration des intervalles de temps (en secondes)
    ANALYSIS_INTERVAL = 300  # 5 minutes
