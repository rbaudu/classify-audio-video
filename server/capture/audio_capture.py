#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import numpy as np
import threading
import time
import queue
import pyaudio
from scipy import signal

# Import de la configuration
from server import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS

logger = logging.getLogger(__name__)

class AudioCapture:
    """
    Classe pour capturer l'audio directement depuis le microphone en utilisant PyAudio.
    Fonctionne en parallèle de la capture vidéo OBS.
    """
    
    def __init__(self, sample_rate=None, channels=None, chunk_size=1024, format=pyaudio.paInt16):
        """
        Initialise le captureur audio.
        
        Args:
            sample_rate (int, optional): Taux d'échantillonnage en Hz.
                Si None, utilise la valeur depuis la configuration.
            channels (int, optional): Nombre de canaux audio (1=mono, 2=stéréo).
                Si None, utilise la valeur depuis la configuration.
            chunk_size (int, optional): Taille du buffer pour la capture audio.
            format (int, optional): Format du son (pyaudio.paInt16, etc.).
        """
        self.sample_rate = sample_rate or AUDIO_SAMPLE_RATE
        self.channels = channels or AUDIO_CHANNELS
        self.chunk_size = chunk_size
        self.format = format
        
        self.pyaudio = None
        self.stream = None
        self.is_recording = False
        self.recording_thread = None
        
        # Buffer circulaire pour stocker les dernières secondes d'audio
        self.audio_buffer = queue.Queue(maxsize=50)  # ~5 secondes d'audio à 44.1kHz
        
        # Horodatage pour la synchronisation avec la vidéo
        self.last_capture_time = 0
        
        # Initialisation de PyAudio
        try:
            self.pyaudio = pyaudio.PyAudio()
            logger.info("PyAudio initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de PyAudio: {str(e)}")
    
    def start_recording(self):
        """
        Démarre l'enregistrement audio en continu dans un thread séparé.
        """
        if self.is_recording:
            logger.warning("L'enregistrement est déjà en cours")
            return False
        
        try:
            # Ouvrir le flux audio
            self.stream = self.pyaudio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            # Démarrer l'enregistrement dans un thread séparé
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_loop)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            logger.info(f"Enregistrement audio démarré (sample_rate={self.sample_rate}, channels={self.channels})")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de l'enregistrement: {str(e)}")
            return False
    
    def stop_recording(self):
        """
        Arrête l'enregistrement audio.
        """
        if not self.is_recording:
            logger.warning("Aucun enregistrement en cours")
            return
        
        # Signaler l'arrêt de l'enregistrement
        self.is_recording = False
        
        # Attendre la fin du thread d'enregistrement
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        # Fermer le flux audio
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture du flux audio: {str(e)}")
        
        logger.info("Enregistrement audio arrêté")
    
    def _record_loop(self):
        """
        Boucle d'enregistrement exécutée dans un thread séparé.
        Capture continuellement l'audio et le stocke dans le buffer.
        """
        while self.is_recording and self.stream:
            try:
                # Lire un chunk d'audio
                audio_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Convertir les données binaires en tableau numpy
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Mettre à jour l'horodatage
                self.last_capture_time = time.time()
                
                # Ajouter au buffer (supprimer le plus ancien si plein)
                if self.audio_buffer.full():
                    try:
                        self.audio_buffer.get_nowait()
                    except queue.Empty:
                        pass
                
                self.audio_buffer.put(audio_array)
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle d'enregistrement: {str(e)}")
                time.sleep(0.1)  # Pause pour éviter une boucle d'erreur trop rapide
    
    def get_audio_data(self, duration_ms=500):
        """
        Récupère les dernières données audio enregistrées.
        
        Args:
            duration_ms (int, optional): Durée des données audio à récupérer en millisecondes.
                Défaut à 500ms.
        
        Returns:
            dict: Données audio traitées avec caractéristiques extraites.
        """
        if not self.is_recording or self.audio_buffer.empty():
            logger.warning("Aucune donnée audio disponible")
            return None
        
        try:
            # Calculer le nombre de chunks nécessaires pour la durée demandée
            chunks_needed = int((duration_ms / 1000.0) * self.sample_rate / self.chunk_size)
            chunks_needed = max(1, min(chunks_needed, self.audio_buffer.qsize()))
            
            # Récupérer les derniers chunks d'audio (sans les supprimer du buffer)
            audio_chunks = []
            queue_list = list(self.audio_buffer.queue)
            for i in range(max(0, len(queue_list) - chunks_needed), len(queue_list)):
                audio_chunks.append(queue_list[i])
            
            # Concaténer les chunks
            if audio_chunks:
                audio_array = np.concatenate(audio_chunks)
            else:
                logger.warning("Pas assez de chunks audio disponibles")
                return None
            
            # Normaliser les données (-1.0 à 1.0)
            audio_normalized = audio_array.astype(np.float32) / 32768.0  # Pour Int16
            
            # Extraire des caractéristiques audio
            features = self._extract_audio_features(audio_normalized)
            
            # Résultat sous forme de dictionnaire
            result = {
                'timestamp': self.last_capture_time,
                'duration_ms': duration_ms,
                'raw_audio': audio_normalized,
                'sample_rate': self.sample_rate,
                'channels': self.channels,
                'features': features
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données audio: {str(e)}")
            return None
    
    def _extract_audio_features(self, audio_normalized):
        """
        Extrait des caractéristiques pertinentes du signal audio.
        
        Args:
            audio_normalized (numpy.ndarray): Signal audio normalisé.
        
        Returns:
            dict: Caractéristiques extraites du signal audio.
        """
        features = {}
        
        try:
            # 1. Niveau sonore (RMS)
            rms = np.sqrt(np.mean(audio_normalized**2))
            features['rms_level'] = float(rms)
            
            # 2. Zero-Crossing Rate (taux de passage par zéro)
            zcr = np.sum(np.abs(np.diff(np.signbit(audio_normalized)))) / (2 * len(audio_normalized))
            features['zero_crossing_rate'] = float(zcr)
            
            # 3. Analyse fréquentielle (FFT)
            if len(audio_normalized) > 0:
                # Transformée de Fourier rapide (FFT)
                fft_result = np.abs(np.fft.rfft(audio_normalized))
                
                # Fréquences correspondantes
                freqs = np.fft.rfftfreq(len(audio_normalized), 1/self.sample_rate)
                
                # Trouver la fréquence dominante
                if len(fft_result) > 0:
                    dominant_freq_idx = np.argmax(fft_result)
                    dominant_freq = freqs[dominant_freq_idx]
                    features['dominant_frequency'] = float(dominant_freq)
                    
                    # Distribution de puissance dans différentes bandes de fréquence
                    # Basse fréquence (< 300 Hz)
                    low_freq_mask = freqs < 300
                    low_freq_power = np.sum(fft_result[low_freq_mask])
                    
                    # Fréquences moyennes (300-3000 Hz, typiques pour la voix)
                    mid_freq_mask = (freqs >= 300) & (freqs <= 3000)
                    mid_freq_power = np.sum(fft_result[mid_freq_mask])
                    
                    # Hautes fréquences (> 3000 Hz)
                    high_freq_mask = freqs > 3000
                    high_freq_power = np.sum(fft_result[high_freq_mask])
                    
                    # Normalisation des puissances
                    total_power = low_freq_power + mid_freq_power + high_freq_power
                    if total_power > 0:
                        features['low_freq_ratio'] = float(low_freq_power / total_power)
                        features['mid_freq_ratio'] = float(mid_freq_power / total_power)
                        features['high_freq_ratio'] = float(high_freq_power / total_power)
            
            # 4. Détection de parole simplifiée
            # La parole se caractérise généralement par :
            # - Un ZCR relativement élevé
            # - Une prédominance des fréquences moyennes (300-3000 Hz)
            # - Des variations d'amplitude importantes
            
            speech_confidence = 0.0
            
            # Si le ZCR est dans la plage typique pour la parole
            if 0.01 < zcr < 0.1:
                speech_confidence += 0.3
            
            # Si les fréquences moyennes sont dominantes (typique de la voix)
            if features.get('mid_freq_ratio', 0) > 0.4:
                speech_confidence += 0.4
            
            # Si le niveau sonore est suffisant
            if rms > 0.05:
                speech_confidence += 0.3
            
            features['speech_detected'] = speech_confidence > 0.5
            features['speech_confidence'] = float(speech_confidence)
            
            return features
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des caractéristiques audio: {str(e)}")
            return features
    
    def __del__(self):
        """
        Nettoyage lors de la destruction de l'objet.
        """
        self.stop_recording()
        
        if self.pyaudio:
            try:
                self.pyaudio.terminate()
            except Exception as e:
                logger.error(f"Erreur lors de la terminaison de PyAudio: {str(e)}")
