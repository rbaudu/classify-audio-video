# Fichier d'initialisation du package server
# Cela permet d'importer les modules du package server

# Exporter les configurations essentielles pour une utilisation facile
from server.config import Config

# Configuration OBS exportée au niveau du module
OBS_HOST = Config.OBS_HOST
OBS_PORT = Config.OBS_PORT
OBS_PASSWORD = Config.OBS_PASSWORD

# Autres configurations essentielles
WEB_PORT = Config.FLASK_PORT
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
