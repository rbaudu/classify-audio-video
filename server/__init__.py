# Fichier d'initialisation du package server
# Cela permet d'importer les modules du package server

# Importer toutes les configurations depuis le fichier config.py
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
VIDEO_SOURCE_NAME = Config.VIDEO_SOURCE_NAME
AUDIO_SOURCE_NAME = Config.AUDIO_SOURCE_NAME

# Configuration de reconnexion OBS WebSocket
OBS_RECONNECT_INTERVAL = Config.OBS_RECONNECT_INTERVAL
OBS_MAX_RECONNECT_INTERVAL = Config.OBS_MAX_RECONNECT_INTERVAL
OBS_MAX_RECONNECT_ATTEMPTS = Config.OBS_MAX_RECONNECT_ATTEMPTS

# Configuration des chemins
BASE_DIR = Config.BASE_DIR
DB_PATH = Config.DATABASE_PATH
MODEL_PATH = Config.MODEL_PATH
DATA_DIR = Config.DATA_DIR

# Configuration du service externe
EXTERNAL_SERVICE_URL = Config.EXTERNAL_SERVICE_URL
EXTERNAL_SERVICE_API_KEY = Config.EXTERNAL_SERVICE_API_KEY

# Configuration des activités
ACTIVITY_CLASSES = Config.ACTIVITY_CLASSES

# Configuration des paramètres de capture vidéo
VIDEO_RESOLUTION = Config.VIDEO_RESOLUTION

# Configuration des paramètres de capture audio
AUDIO_SAMPLE_RATE = Config.AUDIO_SAMPLE_RATE
AUDIO_CHANNELS = Config.AUDIO_CHANNELS
AUDIO_FORMAT = Config.AUDIO_FORMAT
AUDIO_CHUNK_SIZE = Config.AUDIO_CHUNK_SIZE

# Configuration audio/vidéo
USE_DIRECT_AUDIO_CAPTURE = Config.USE_DIRECT_AUDIO_CAPTURE
AUDIO_VIDEO_SYNC_BUFFER_SIZE = Config.AUDIO_VIDEO_SYNC_BUFFER_SIZE

# Configuration des intervalles
ANALYSIS_INTERVAL = Config.ANALYSIS_INTERVAL

# Variables pour l'interface
ACTIVITY_ICONS = Config.ACTIVITY_ICONS
ACTIVITY_COLORS = Config.ACTIVITY_COLORS
