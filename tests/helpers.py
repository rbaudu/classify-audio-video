"""
Utilitaires pour les tests unitaires
"""
import os
import json
import tempfile
import numpy as np

# Classes de mock pour simuler les différents composants
class MockDBManager:
    """Mock pour le gestionnaire de base de données"""
    
    def __init__(self, test_data=None):
        self.activities = []
        self.video_analyses = {}
        self.test_data = test_data or {}
    
    def add_activity(self, activity, confidence, timestamp, metadata):
        activity_id = len(self.activities) + 1
        self.activities.append({
            'id': activity_id,
            'activity': activity,
            'confidence': confidence,
            'timestamp': timestamp,
            'metadata': metadata
        })
        return activity_id
    
    def get_latest_activity(self):
        if not self.activities:
            return None
        return self.activities[-1]
    
    def get_activities(self, start=None, end=None, limit=100, offset=0):
        filtered = self.activities
        
        if start is not None:
            filtered = [a for a in filtered if a['timestamp'] >= start]
        
        if end is not None:
            filtered = [a for a in filtered if a['timestamp'] <= end]
        
        # Appliquer limit et offset
        filtered = filtered[offset:offset+limit]
        
        return filtered
    
    def save_video_analysis(self, analysis_id, source_name, results):
        self.video_analyses[analysis_id] = {
            'source_name': source_name,
            'timestamp': 1614556800,  # 2021-03-01 pour les tests
            'results': results
        }
        return True
    
    def get_video_analysis(self, analysis_id):
        return self.video_analyses.get(analysis_id)


class MockOBSCapture:
    """Mock pour la capture OBS"""
    
    def __init__(self, test_data=None):
        self.connected = True
        self.frame_data = np.zeros((480, 640, 3), dtype=np.uint8)  # Frame vide par défaut
        self.sources = ["Source 1", "Source 2", "Test Video"]
        self.current_source = "Source 1"
        self.media_properties = {
            "Test Video": {
                "duration": 60.0,
                "status": "playing",
                "position": 0.0
            }
        }
        self.test_data = test_data or {}
    
    def connect(self):
        self.connected = True
        return True
    
    def disconnect(self):
        self.connected = False
        return True
    
    def is_connected(self):
        return self.connected
    
    def get_current_frame(self):
        return self.frame_data
    
    def get_media_sources(self):
        return self.sources
    
    def select_media_source(self, source_name):
        if source_name in self.sources:
            self.current_source = source_name
            return True
        return False
    
    def get_media_properties(self, source_name):
        return self.media_properties.get(source_name, {})
    
    def control_media(self, source_name, action, position=None):
        if source_name not in self.media_properties:
            return False
        
        if action == 'play':
            self.media_properties[source_name]['status'] = 'playing'
        elif action == 'pause':
            self.media_properties[source_name]['status'] = 'paused'
        elif action == 'restart':
            self.media_properties[source_name]['position'] = 0.0
        elif action == 'seek' and position is not None:
            self.media_properties[source_name]['position'] = position
        
        return True
    
    def get_media_time(self, source_name):
        if source_name not in self.media_properties:
            return None
        
        return {
            'position': self.media_properties[source_name]['position'],
            'duration': self.media_properties[source_name]['duration']
        }


class MockPyAudioCapture:
    """Mock pour la capture PyAudio"""
    
    def __init__(self, test_data=None):
        self.started = False
        self.devices = [
            {"index": 0, "name": "Default Input Device"},
            {"index": 1, "name": "Microphone (High Definition Audio)"},
            {"index": 2, "name": "Line In (High Definition Audio)"}
        ]
        self.current_device = 0
        self.audio_data = np.zeros(1024, dtype=np.int16)  # Données audio vides par défaut
        self.test_data = test_data or {}
    
    def start(self):
        self.started = True
        return True
    
    def stop(self):
        self.started = False
        return True
    
    def is_running(self):
        return self.started
    
    def get_devices(self):
        return self.devices
    
    def set_device(self, device_index):
        if any(d['index'] == device_index for d in self.devices):
            self.current_device = device_index
            return True
        return False
    
    def get_audio_data(self, duration_ms=500):
        # Simuler la récupération de données audio
        return self.audio_data


class MockSyncManager:
    """Mock pour le gestionnaire de synchronisation"""
    
    def __init__(self, test_data=None):
        self.started = False
        self.obs_capture = MockOBSCapture(test_data)
        self.pyaudio_capture = MockPyAudioCapture(test_data)
        self.test_data = test_data or {}
    
    def start(self):
        self.started = True
        return True
    
    def stop(self):
        self.started = False
        return True
    
    def is_running(self):
        return self.started
    
    def get_audio_devices(self):
        return self.pyaudio_capture.get_devices()
    
    def set_audio_device(self, device_index):
        return self.pyaudio_capture.set_device(device_index)
    
    def get_synchronized_data(self):
        # Données synchronisées simulées
        return {
            'video': {
                'raw': self.obs_capture.get_current_frame(),
                'processed': {
                    'features': {
                        'movement': 0.2,
                        'brightness': 0.7,
                        'scene_change': 0.1,
                        'pose_confidence': 0.85
                    }
                }
            },
            'audio': {
                'raw': self.pyaudio_capture.get_audio_data(),
                'processed': {
                    'features': {
                        'volume': 0.3,
                        'frequency': 220.0,
                        'is_speech': True,
                        'pitch': 0.5
                    }
                }
            },
            'timestamp': 1614556800  # 2021-03-01 pour les tests
        }
    
    def save_synchronized_clip(self, duration=5, prefix="clip"):
        clip_id = f"{prefix}_{1614556800}"
        return {
            'success': True,
            'clip_id': clip_id,
            'video_path': f"/tmp/{clip_id}.mp4",
            'audio_path': f"/tmp/{clip_id}.wav",
            'duration': duration
        }


class MockStreamProcessor:
    """Mock pour le processeur de flux"""
    
    def __init__(self, test_data=None):
        self.test_data = test_data or {}
    
    def process_video_frame(self, frame):
        return {
            'features': {
                'movement': 0.2,
                'brightness': 0.7,
                'scene_change': 0.1,
                'pose_confidence': 0.85
            }
        }
    
    def process_audio_data(self, audio_data):
        return {
            'features': {
                'volume': 0.3,
                'frequency': 220.0,
                'is_speech': True,
                'pitch': 0.5
            }
        }


class MockActivityClassifier:
    """Mock pour le classificateur d'activité"""
    
    def __init__(self, sync_manager=None, stream_processor=None, db_manager=None, test_data=None):
        self.sync_manager = sync_manager or MockSyncManager()
        self.stream_processor = stream_processor or MockStreamProcessor()
        self.db_manager = db_manager or MockDBManager()
        self.test_data = test_data or {}
    
    def classify_activity(self, video_data, audio_data):
        return {
            'activity': 'reading',
            'confidence': 0.85,
            'confidence_scores': {
                'reading': 0.85,
                'talking': 0.05,
                'eating': 0.03,
                'working': 0.04,
                'sleeping': 0.01,
                'on_phone': 0.01,
                'inactive': 0.01
            },
            'timestamp': 1614556800  # 2021-03-01 pour les tests
        }
    
    def analyze_current_activity(self):
        data = self.sync_manager.get_synchronized_data()
        
        if not data:
            return None
        
        classification = self.classify_activity(
            data['video']['processed'],
            data['audio']['processed']
        )
        
        # Ajouter les caractéristiques
        classification['features'] = {
            'video': data['video']['processed'].get('features', {}),
            'audio': data['audio']['processed'].get('features', {})
        }
        
        return classification


class MockExternalServiceClient:
    """Mock pour le client de service externe"""
    
    def __init__(self, test_data=None):
        self.sent_activities = []
        self.test_data = test_data or {}
    
    def send_activity(self, activity_data):
        self.sent_activities.append(activity_data)
        return {
            'success': True,
            'message': 'Activity data received',
            'timestamp': 1614556800  # 2021-03-01 pour les tests
        }


# Utilitaires pour les tests de fichiers
def create_temp_file(content, suffix=".txt"):
    """Crée un fichier temporaire avec le contenu spécifié"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    
    if isinstance(content, str):
        temp_file.write(content.encode('utf-8'))
    elif isinstance(content, dict) or isinstance(content, list):
        temp_file.write(json.dumps(content).encode('utf-8'))
    else:
        temp_file.write(content)
    
    temp_file.close()
    return temp_file.name


def create_temp_directory():
    """Crée un répertoire temporaire"""
    return tempfile.mkdtemp()


def cleanup_temp_file(file_path):
    """Supprime un fichier temporaire"""
    if os.path.exists(file_path):
        os.unlink(file_path)


def cleanup_temp_directory(dir_path):
    """Supprime un répertoire temporaire"""
    if os.path.exists(dir_path):
        # Supprime les fichiers dans le répertoire
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        
        # Supprime le répertoire
        os.rmdir(dir_path)
