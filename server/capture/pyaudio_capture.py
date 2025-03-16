#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import threading
import numpy as np
import pyaudio
import wave
import os
from collections import deque

# Import de la configuration
from server import (
    AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_FORMAT, AUDIO_CHUNK_SIZE,
    AUDIO_VIDEO_SYNC_BUFFER_SIZE
)

class PyAudioCapture:
    """
    Classe pour capturer l'audio directement via PyAudio.
    Permet de capturer l'audio depuis le microphone par défaut ou spécifié.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.p = None  # Instance PyAudio
        self.stream = None  # Stream audio
        
        # État de la capture
        self.is_recording = False
        self.recording_thread = None
        
        # Buffer circulaire pour stocker les dernières données audio capturées
        # Taille calculée pour contenir AUDIO_VIDEO_SYNC_BUFFER_SIZE secondes d'audio
        buffer_size = int(AUDIO_SAMPLE_RATE * AUDIO_VIDEO_SYNC_BUFFER_SIZE)
        self.audio_buffer = deque(maxlen=buffer_size)
        
        # Métadonnées du dernier audio capturé
        self.current_audio = None
        
        # Horodatage pour la synchronisation
        self.last_capture_time = 0
        
        # Tentative d'initialisation de PyAudio
        self.initialize()
    
    def initialize(self):
        """
        Initialise PyAudio et liste les périphériques disponibles
        """
        try:
            self.p = pyaudio.PyAudio()
            
            # Lister les périphériques audio disponibles
            info = []
            for i in range(self.p.get_device_count()):
                dev_info = self.p.get_device_info_by_index(i)
                info.append(dev_info)
                if dev_info['maxInputChannels'] > 0:  # C'est un périphérique d'entrée
                    self.logger.info(f"Input Device {i}: {dev_info['name']}")
            
            self.logger.info(f"PyAudio initialisé avec succès. {len(info)} périphériques trouvés.")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation de PyAudio: {str(e)}")
            return False
    
    def check_device(self):
        """
        Vérifie si au moins un périphérique audio d'entrée est disponible
        
        Returns:
            bool: True si au moins un périphérique est disponible, False sinon
        """
        try:
            if not self.p:
                if not self.initialize():
                    return False
            
            # Vérifier si au moins un périphérique d'entrée est disponible
            devices = self.get_devices()
            if not devices:
                self.logger.warning("Aucun périphérique audio d'entrée disponible")
                return False
            
            # Si la capture est en cours, vérifier si le stream est actif
            if self.is_recording and self.stream:
                return self.stream.is_active()
            
            # Sinon, simplement confirmer qu'il y a des périphériques disponibles
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du périphérique audio: {str(e)}")
            return False
    
    def start_capture(self, device_index=None):
        """
        Démarre la capture audio en continu
        
        Args:
            device_index (int, optional): Indice du périphérique à utiliser. None = périphérique par défaut.
        
        Returns:
            bool: True si la capture a démarré avec succès, False sinon
        """
        if self.is_recording:
            self.logger.warning("La capture audio est déjà en cours.")
            return True
        
        if not self.p:
            self.initialize()
        
        try:
            # Ouvrir le stream audio
            self.stream = self.p.open(
                format=AUDIO_FORMAT,
                channels=AUDIO_CHANNELS,
                rate=AUDIO_SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=AUDIO_CHUNK_SIZE,
                stream_callback=self._audio_callback
            )
            
            # Démarrer le stream
            self.stream.start_stream()
            self.is_recording = True
            self.last_capture_time = time.time()
            
            self.logger.info(f"Capture audio démarrée avec périphérique {device_index if device_index is not None else 'par défaut'}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage de la capture audio: {str(e)}")
            return False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback appelé par PyAudio lorsque des données audio sont disponibles
        
        Args:
            in_data (bytes): Données audio brutes
            frame_count (int): Nombre de frames dans les données
            time_info (dict): Informations de timing
            status (int): Statut de la capture
            
        Returns:
            tuple: (None, pyaudio.paContinue)
        """
        try:
            # Convertir les données audio en tableau numpy
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Ajouter au buffer
            self.audio_buffer.extend(audio_data)
            
            # Mettre à jour l'horodatage
            self.last_capture_time = time.time()
            
            # Générer des métadonnées audio (analyse simple)
            self._analyze_audio_data(audio_data)
            
            return (None, pyaudio.paContinue)
        except Exception as e:
            self.logger.error(f"Erreur dans le callback audio: {str(e)}")
            return (None, pyaudio.paContinue)
    
    def _analyze_audio_data(self, audio_data):
        """
        Analyse simple des données audio pour extraire des caractéristiques
        
        Args:
            audio_data (numpy.ndarray): Données audio à analyser
        """
        if len(audio_data) == 0:
            return
        
        try:
            # Normaliser l'audio entre -1 et 1 pour l'analyse
            normalized = audio_data.astype(np.float32) / 32768.0
            
            # Calculer le niveau moyen
            average_level = np.mean(np.abs(normalized)) * 100
            
            # Calculer le niveau de crête
            peak_level = np.max(np.abs(normalized)) * 100
            
            # Détection simple de parole basée sur le niveau et le Zero-Crossing Rate
            zcr = np.sum(np.abs(np.diff(np.signbit(normalized)))) / (2 * len(normalized))
            speech_detected = (average_level > 5) and (zcr > 0.05)
            
            # Analyse spectrale très simplifiée (pour des métriques basiques)
            if len(normalized) > AUDIO_CHUNK_SIZE // 2:
                # FFT rapide
                fft_result = np.abs(np.fft.rfft(normalized[:AUDIO_CHUNK_SIZE]))
                freqs = np.fft.rfftfreq(AUDIO_CHUNK_SIZE, 1/AUDIO_SAMPLE_RATE)
                
                # Trouver quelques fréquences dominantes
                n_peaks = min(10, len(fft_result)//10)
                peak_indices = np.argpartition(fft_result, -n_peaks)[-n_peaks:]
                frequencies = freqs[peak_indices]
                amplitudes = fft_result[peak_indices]
            else:
                frequencies = np.array([0])
                amplitudes = np.array([0])
            
            # Stocker les métadonnées
            self.current_audio = {
                'frequencies': frequencies,
                'amplitudes': amplitudes,
                'average_level': average_level,
                'peak_level': peak_level,
                'speech_detected': speech_detected,
                'timestamp': self.last_capture_time
            }
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse audio: {str(e)}")
    
    def stop_capture(self):
        """
        Arrête la capture audio
        
        Returns:
            bool: True si l'arrêt a réussi, False sinon
        """
        if not self.is_recording:
            return True
        
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            self.is_recording = False
            self.logger.info("Capture audio arrêtée")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt de la capture audio: {str(e)}")
            return False
    
    def close(self):
        """
        Ferme PyAudio et libère les ressources
        """
        self.stop_capture()
        
        if self.p:
            try:
                self.p.terminate()
                self.p = None
                self.logger.info("PyAudio terminé et ressources libérées")
            except Exception as e:
                self.logger.error(f"Erreur lors de la fermeture de PyAudio: {str(e)}")
    
    def get_audio_data(self, duration_ms=500):
        """
        Récupère les dernières données audio capturées
        
        Args:
            duration_ms (int, optional): Durée de l'audio à récupérer en millisecondes. Défaut à 500.
        
        Returns:
            dict: Données audio (métadonnées) et tableau numpy des échantillons audio
        """
        if not self.is_recording or not self.current_audio:
            return None
        
        # Calculer le nombre d'échantillons correspondant à la durée demandée
        n_samples = int(AUDIO_SAMPLE_RATE * duration_ms / 1000)
        
        # Récupérer les derniers échantillons du buffer
        buffer_list = list(self.audio_buffer)
        samples = buffer_list[-min(n_samples, len(buffer_list)):]
        
        # Si le buffer ne contient pas assez d'échantillons, compléter avec des zéros
        if len(samples) < n_samples:
            samples = [0] * (n_samples - len(samples)) + samples
        
        # Convertir en tableau numpy
        audio_samples = np.array(samples, dtype=np.int16)
        
        # Combiner avec les métadonnées
        result = self.current_audio.copy()
        result['samples'] = audio_samples
        
        return result
    
    def save_audio_to_file(self, filename, duration_seconds=5):
        """
        Sauvegarde les dernières secondes d'audio capturé dans un fichier WAV
        
        Args:
            filename (str): Chemin du fichier de sortie
            duration_seconds (int, optional): Nombre de secondes à sauvegarder. Défaut à 5.
        
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        if not self.is_recording:
            self.logger.warning("Impossible de sauvegarder: pas de capture audio en cours")
            return False
        
        try:
            # Calculer le nombre d'échantillons
            n_samples = int(AUDIO_SAMPLE_RATE * duration_seconds)
            
            # Récupérer les derniers échantillons du buffer
            buffer_list = list(self.audio_buffer)
            samples = buffer_list[-min(n_samples, len(buffer_list)):]
            
            # Convertir en tableau numpy puis en bytes
            audio_samples = np.array(samples, dtype=np.int16)
            audio_bytes = audio_samples.tobytes()
            
            # Créer le répertoire de sortie si nécessaire
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Sauvegarder en WAV
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(AUDIO_CHANNELS)
                wf.setsampwidth(self.p.get_sample_size(AUDIO_FORMAT))
                wf.setframerate(AUDIO_SAMPLE_RATE)
                wf.writeframes(audio_bytes)
            
            self.logger.info(f"Audio sauvegardé dans {filename} ({len(samples)/AUDIO_SAMPLE_RATE:.2f} secondes)")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde audio: {str(e)}")
            return False
    
    def get_devices(self):
        """
        Récupère la liste des périphériques audio d'entrée disponibles
        
        Returns:
            list: Liste des périphériques audio d'entrée
        """
        devices = []
        
        if not self.p:
            self.initialize()
        
        try:
            for i in range(self.p.get_device_count()):
                dev_info = self.p.get_device_info_by_index(i)
                if dev_info['maxInputChannels'] > 0:  # C'est un périphérique d'entrée
                    devices.append({
                        'index': i,
                        'name': dev_info['name'],
                        'channels': dev_info['maxInputChannels'],
                        'default': (i == self.p.get_default_input_device_info()['index'])
                    })
            
            return devices
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des périphériques: {str(e)}")
            return []
