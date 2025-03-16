#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pyaudio

class Config:
    # Configuration de l'application Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'une-cle-secrete-tres-difficile-a-deviner'
    DEBUG = os.environ.get('FLASK_DEBUG') or False
    FLASK_HOST = os.environ.get('FLASK_HOST') or '0.0.0.0'
    FLASK_PORT = int(os.environ.get('FLASK_PORT') or 5000)
    
    # Configuration OBS
    OBS_HOST = os.environ.get('OBS_HOST') or 'localhost'
    OBS_PORT = int(os.environ.get('OBS_PORT') or 4455)
    OBS_PASSWORD = os.environ.get('OBS_PASSWORD') or 'Me2Fai800h1VwthV'
    
    # Configuration des sources OBS
    VIDEO_SOURCE_NAME = os.environ.get('VIDEO_SOURCE_NAME') or 'acméra'  # Modifié par défaut pour correspondre à votre source actuelle
    AUDIO_SOURCE_NAME = os.environ.get('AUDIO_SOURCE_NAME') or 'Default Audio Source'
    
    # Configuration des chemins
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, '..', 'data', 'activity.db')
    MODEL_PATH = os.path.join(BASE_DIR, '..', 'models', 'activity_classifier.h5')
    DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
    
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
    
    # Variables pour l'interface
    ACTIVITY_ICONS = {
        'endormi': 'moon',
        'à table': 'utensils',
        'lisant': 'book-open',
        'au téléphone': 'phone',
        'en conversation': 'users',
        'occupé': 'briefcase',
        'inactif': 'pause-circle'
    }
    
    ACTIVITY_COLORS = {
        'endormi': 'indigo',
        'à table': 'orange',
        'lisant': 'teal',
        'au téléphone': 'purple',
        'en conversation': 'blue',
        'occupé': 'red',
        'inactif': 'gray'
    }
    
    # Configuration des paramètres de capture vidéo
    VIDEO_RESOLUTION = (640, 480)
    
    # Configuration des paramètres de capture audio via PyAudio
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    AUDIO_FORMAT = pyaudio.paInt16  # Format 16-bit pour l'audio
    AUDIO_CHUNK_SIZE = 1024         # Taille des chunks audio
    
    # Activation de la capture audio directe (PyAudio) vs OBS
    USE_DIRECT_AUDIO_CAPTURE = True  # True = PyAudio, False = OBS (simulated)
    
    # Configuration de la synchronisation audio/vidéo
    AUDIO_VIDEO_SYNC_BUFFER_SIZE = 5  # Nombre de secondes dans le buffer de synchronisation
    
    # Configuration des intervalles de temps (en secondes)
    ANALYSIS_INTERVAL = 300  # 5 minutes
    
    # Configuration de reconnexion OBS WebSocket
    OBS_RECONNECT_INTERVAL = 5      # Intervalle initial entre les tentatives de reconnexion (secondes)
    OBS_MAX_RECONNECT_INTERVAL = 60  # Intervalle maximum entre les tentatives (secondes)
    OBS_MAX_RECONNECT_ATTEMPTS = 0   # Nombre maximum de tentatives (0 = illimité)
