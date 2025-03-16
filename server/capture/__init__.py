# Fichier d'initialisation du package capture

# Exposer les classes principales pour faciliter l'importation
from server.capture.obs_capture import OBSCapture
from server.capture.pyaudio_capture import PyAudioCapture
from server.capture.stream_processor import StreamProcessor
from server.capture.sync_manager import SyncManager

# Système de capture à utiliser par défaut
DEFAULT_CAPTURE_SYSTEM = SyncManager
