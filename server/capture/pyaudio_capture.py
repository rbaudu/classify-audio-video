import logging
import numpy as np
import pyaudio
import threading
import time
import queue

from server import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_FORMAT, AUDIO_CHUNK_SIZE

class PyAudioCapture:
    """
    Classe pour gérer la capture audio directe via PyAudio.
    """
    
    def __init__(self, device_index=None):
        """
        Initialise la capture audio.
        
        Args:
            device_index (int, optional): Indice du périphérique audio à utiliser. 
                                         None pour utiliser le périphérique par défaut.
        """
        self.logger = logging.getLogger(__name__)
        self.device_index = device_index
        self.audio = None
        self.stream = None
        self.is_capturing = False
        self.lock = threading.RLock()
        
        # Buffer circulaire pour stocker les données audio récentes
        self.audio_buffer = queue.Queue(maxsize=100)  # ~6 secondes à 16kHz
        
        # Thread de capture
        self.capture_thread = None
        
        # Initialiser PyAudio
        self.initialize()
    
    def initialize(self):
        """
        Initialise l'objet PyAudio et liste les périphériques disponibles.
        """
        try:
            self.audio = pyaudio.PyAudio()
            
            # Lister les périphériques d'entrée disponibles
            info = self.audio.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            
            # Réinitialiser l'indice si la valeur fournie est invalide
            if self.device_index is not None and (self.device_index < 0 or self.device_index >= numdevices):
                self.logger.warning(f"Indice de périphérique {self.device_index} hors limites. Utilisation du périphérique par défaut.")
                self.device_index = None
            
            # Chercher le premier périphérique d'entrée disponible si aucun indice n'est fourni
            if self.device_index is None:
                for i in range(numdevices):
                    if self.audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
                        dev_info = self.audio.get_device_info_by_host_api_device_index(0, i)
                        self.logger.info(f"Input Device {i}: {dev_info.get('name')}")
            
            total_devices = self.audio.get_device_count()
            self.logger.info(f"PyAudio initialisé avec succès. {total_devices} périphériques trouvés.")
            
            # Si aucun périphérique d'entrée n'est trouvé, utiliser l'indice 0 par défaut
            if self.device_index is None:
                self.device_index = 0
                self.logger.info(f"Utilisation du périphérique d'entrée par défaut (indice {self.device_index})")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation de PyAudio: {str(e)}")
            if self.audio:
                self.audio.terminate()
                self.audio = None
    
    def list_devices(self):
        """
        Liste tous les périphériques audio disponibles.
        
        Returns:
            list: Liste des périphériques avec leurs indices et noms
        """
        if not self.audio:
            self.logger.error("PyAudio non initialisé")
            return []
        
        devices = []
        for i in range(self.audio.get_device_count()):
            try:
                dev_info = self.audio.get_device_info_by_index(i)
                name = dev_info.get('name')
                max_input_channels = dev_info.get('maxInputChannels')
                max_output_channels = dev_info.get('maxOutputChannels')
                
                if max_input_channels > 0:
                    devices.append({
                        'index': i,
                        'name': name,
                        'max_input_channels': max_input_channels,
                        'max_output_channels': max_output_channels,
                        'default_sample_rate': dev_info.get('defaultSampleRate')
                    })
                    
                    self.logger.info(f"Périphérique audio {i}: {name} - {max_input_channels} canaux d'entrée")
            except Exception as e:
                self.logger.warning(f"Erreur lors de la récupération des informations du périphérique {i}: {str(e)}")
        
        return devices
    
    def start_capture(self, device_index=None):
        """
        Démarre la capture audio.
        
        Args:
            device_index (int, optional): Indice du périphérique à utiliser, remplace celui fourni au constructeur.
        
        Returns:
            bool: True si la capture a démarré avec succès, False sinon.
        """
        with self.lock:
            if self.is_capturing:
                self.logger.warning("La capture audio est déjà en cours")
                return True
            
            if device_index is not None:
                self.device_index = device_index
            
            if not self.audio:
                self.initialize()
                if not self.audio:
                    self.logger.error("Impossible de démarrer la capture: PyAudio non initialisé")
                    return False
            
            try:
                # Récupérer les informations du périphérique
                try:
                    device_info = self.audio.get_device_info_by_index(self.device_index)
                    device_name = device_info.get('name', 'Périphérique inconnu')
                    self.logger.info(f"Ouverture du flux audio sur le périphérique {self.device_index}: {device_name}")
                except:
                    self.logger.warning(f"Impossible d'obtenir les informations du périphérique {self.device_index}. Utilisation du périphérique par défaut.")
                    device_name = "périphérique par défaut"
                
                # Ouvrir le flux audio
                self.stream = self.audio.open(
                    format=AUDIO_FORMAT,
                    channels=AUDIO_CHANNELS,
                    rate=AUDIO_SAMPLE_RATE,
                    input=True,
                    input_device_index=self.device_index,
                    frames_per_buffer=AUDIO_CHUNK_SIZE,
                    stream_callback=self._audio_callback
                )
                
                self.is_capturing = True
                self.stream.start_stream()
                self.logger.info(f"Capture audio démarrée avec {device_name}")
                
                # Démarrer un thread pour vider périodiquement le buffer si nécessaire
                self.capture_thread = threading.Thread(target=self._capture_loop)
                self.capture_thread.daemon = True
                self.capture_thread.start()
                
                return True
            except Exception as e:
                self.logger.error(f"Erreur lors du démarrage de la capture audio: {str(e)}")
                
                # Essayer de récupérer plus d'informations sur l'erreur
                try:
                    device_count = self.audio.get_device_count()
                    self.logger.info(f"Nombre total de périphériques: {device_count}")
                    
                    # Tester rapidement chaque périphérique d'entrée
                    working_devices = []
                    for i in range(device_count):
                        try:
                            dev_info = self.audio.get_device_info_by_index(i)
                            if dev_info.get('maxInputChannels') > 0:
                                self.logger.info(f"Test du périphérique {i}: {dev_info.get('name')}")
                                test_stream = self.audio.open(
                                    format=AUDIO_FORMAT,
                                    channels=AUDIO_CHANNELS,
                                    rate=AUDIO_SAMPLE_RATE,
                                    input=True,
                                    input_device_index=i,
                                    frames_per_buffer=AUDIO_CHUNK_SIZE,
                                    start=False
                                )
                                test_stream.close()
                                working_devices.append(i)
                                self.logger.info(f"Périphérique {i} fonctionne")
                        except Exception as test_error:
                            self.logger.warning(f"Périphérique {i} non fonctionnel: {str(test_error)}")
                    
                    # Si d'autres périphériques fonctionnent, suggérer d'utiliser l'un d'entre eux
                    if working_devices:
                        self.logger.info(f"Périphériques fonctionnels: {working_devices}")
                        # Utiliser le premier périphérique fonctionnel
                        alternative_device = working_devices[0]
                        if alternative_device != self.device_index:
                            self.logger.info(f"Tentative avec le périphérique alternatif {alternative_device}")
                            return self.start_capture(alternative_device)
                except Exception as debug_error:
                    self.logger.error(f"Erreur lors du diagnostic des périphériques audio: {str(debug_error)}")
                
                if self.stream:
                    self.stream.close()
                    self.stream = None
                
                self.is_capturing = False
                return False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback appelé par PyAudio quand de nouvelles données audio sont disponibles.
        
        Args:
            in_data (bytes): Données audio brutes
            frame_count (int): Nombre de frames
            time_info (dict): Informations de timing
            status (int): Statut de la capture
        
        Returns:
            tuple: (None, pyaudio.paContinue)
        """
        if status:
            self.logger.warning(f"Statut audio non-zéro: {status}")
        
        try:
            # Ajouter les données au buffer, en supprimant les plus anciennes si nécessaire
            if self.audio_buffer.full():
                try:
                    self.audio_buffer.get_nowait()  # Vider une entrée ancienne
                except queue.Empty:
                    pass  # Rien à vider
            
            self.audio_buffer.put(in_data)
        except Exception as e:
            self.logger.error(f"Erreur dans le callback audio: {str(e)}")
        
        return (None, pyaudio.paContinue)
    
    def _capture_loop(self):
        """
        Boucle de thread pour maintenir la capture active.
        """
        while self.is_capturing:
            # Vérifier si le flux est toujours actif
            if self.stream and not self.stream.is_active():
                self.logger.warning("Le flux audio s'est arrêté de manière inattendue. Tentative de redémarrage.")
                with self.lock:
                    self.stop_capture()
                    self.start_capture()
            
            # Dormir pour éviter de surcharger le CPU
            time.sleep(1)
    
    def stop_capture(self):
        """
        Arrête la capture audio.
        """
        with self.lock:
            if not self.is_capturing:
                return
            
            self.is_capturing = False
            
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception as e:
                    self.logger.error(f"Erreur lors de l'arrêt du flux audio: {str(e)}")
                finally:
                    self.stream = None
            
            # Vider le buffer
            while not self.audio_buffer.empty():
                try:
                    self.audio_buffer.get_nowait()
                except queue.Empty:
                    break
            
            self.logger.info("Capture audio arrêtée")
    
    def get_audio_data(self, duration_ms=1000):
        """
        Récupère les dernières données audio capturées.
        
        Args:
            duration_ms (int): Durée des données audio à récupérer en millisecondes
        
        Returns:
            numpy.ndarray: Données audio au format numpy (int16)
        """
        if not self.is_capturing:
            self.logger.warning("Tentative de récupération de données audio sans capture active")
            return np.zeros(int(AUDIO_SAMPLE_RATE * duration_ms / 1000), dtype=np.int16)
        
        # Calculer combien de chunks correspondent à la durée demandée
        bytes_per_sample = 2  # Pour format paInt16
        samples_per_chunk = AUDIO_CHUNK_SIZE
        chunks_needed = int((AUDIO_SAMPLE_RATE * duration_ms / 1000) / samples_per_chunk) + 1
        
        # Récupérer les chunks du buffer
        audio_chunks = []
        chunk_count = 0
        
        # Copier le buffer pour éviter les problèmes de concurrence
        buffer_copy = []
        while not self.audio_buffer.empty() and chunk_count < chunks_needed:
            try:
                buffer_copy.append(self.audio_buffer.get())
                chunk_count += 1
            except queue.Empty:
                break
        
        # Remettre les chunks dans le buffer
        for chunk in buffer_copy:
            self.audio_buffer.put(chunk)
            audio_chunks.append(chunk)
        
        if not audio_chunks:
            self.logger.warning("Aucune donnée audio disponible")
            return np.zeros(int(AUDIO_SAMPLE_RATE * duration_ms / 1000), dtype=np.int16)
        
        # Convertir les chunks en un tableau numpy
        try:
            # Convertir les bytes en tableau numpy
            audio_data = np.frombuffer(b''.join(audio_chunks), dtype=np.int16)
            
            # Limiter à la durée demandée
            max_samples = int(AUDIO_SAMPLE_RATE * duration_ms / 1000)
            if len(audio_data) > max_samples:
                audio_data = audio_data[-max_samples:]
            
            return audio_data
        except Exception as e:
            self.logger.error(f"Erreur lors de la conversion des données audio: {str(e)}")
            return np.zeros(int(AUDIO_SAMPLE_RATE * duration_ms / 1000), dtype=np.int16)
    
    def analyze_audio_levels(self, duration_ms=1000):
        """
        Analyse les niveaux audio et retourne des métriques.
        
        Args:
            duration_ms (int): Durée des données audio à analyser en millisecondes
        
        Returns:
            dict: Métriques audio (rms, peak, etc.)
        """
        audio_data = self.get_audio_data(duration_ms)
        
        if len(audio_data) == 0:
            return {
                'rms': 0,
                'peak': 0,
                'average': 0,
                'has_audio': False
            }
        
        # Normaliser entre -1 et 1
        audio_normalized = audio_data.astype(np.float32) / 32768.0
        
        # Calculer les métriques
        rms = np.sqrt(np.mean(np.square(audio_normalized)))
        peak = np.max(np.abs(audio_normalized))
        average = np.mean(np.abs(audio_normalized))
        
        # Déterminer s'il y a du son significatif
        has_audio = rms > 0.01  # Seuil arbitraire à ajuster selon les besoins
        
        return {
            'rms': float(rms),
            'peak': float(peak),
            'average': float(average),
            'has_audio': has_audio
        }
    
    def __del__(self):
        """
        Destructeur pour nettoyer les ressources.
        """
        self.stop_capture()
        
        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erreur lors de la terminaison de PyAudio: {str(e)}")
