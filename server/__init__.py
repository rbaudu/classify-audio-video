# Fichier d'initialisation du package server
# Cela permet d'importer les modules du package server

# Exporter les configurations essentielles pour une utilisation facile
from server.config import Config

# Configuration de base
SECRET_KEY = Config.SECRET_KEY
DEBUG = Config.DEBUG
FLASK_HOST = Config.FLASK_HOST
WEB_PORT = Config.FLASK_PORT

# Configuration OBS
OBS_HOST = Config.OBS_HOST
OBS_PORT = Config.OBS_PORT
OBS_PASSWORD = Config.OBS_PASSWORD

# Configuration des chemins
BASE_DIR = Config.BASE_DIR
DB_PATH = Config.DATABASE_PATH
MODEL_PATH = Config.MODEL_PATH

# Configuration du service externe
EXTERNAL_SERVICE_URL = Config.EXTERNAL_SERVICE_URL
EXTERNAL_SERVICE_API_KEY = Config.EXTERNAL_SERVICE_API_KEY

# Configuration des activités
ACTIVITY_CLASSES = Config.ACTIVITY_CLASSES

# Configuration des paramètres de capture
VIDEO_RESOLUTION = Config.VIDEO_RESOLUTION
AUDIO_SAMPLE_RATE = Config.AUDIO_SAMPLE_RATE
AUDIO_CHANNELS = Config.AUDIO_CHANNELS

# Configuration des intervalles
ANALYSIS_INTERVAL = Config.ANALYSIS_INTERVAL

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

# Variables pour la capture
VIDEO_SOURCE_NAME = 'Default Video Source'
AUDIO_SOURCE_NAME = 'Default Audio Source'
