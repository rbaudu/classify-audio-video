#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyaudio
import numpy as np
import threading
import time
import logging
import queue
from array import array
from datetime import datetime

from server import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_FORMAT, AUDIO_CHUNK_SIZE

logger = logging.getLogger(__name__)

class AudioCapture:
    """
    Classe pour capturer l'audio du microphone en utilisant PyAudio.
    Fonctionne en parallèle avec la capture vidéo d'OBS.
    """
    
    def __init__(self, sample_rate=None, channels=None, audio_format=None, chunk_size=None):
        """
        Initialise le système de capture audio.
        
        Args:
            sample_rate (int, optional): Taux d'échantillonnage audio en Hz. Default à AUDIO_SAMPLE_RATE de la config.
            channels (int, optional): Nombre de canaux audio (1=mono, 2=stéréo). Default à AUDIO_CHANNELS de la config.
            audio_format (int, optional): Format de l'échantillon audio. Default à AUDIO_FORMAT de la config.
            chunk_size (int, optional): Taille des chunks audio. Default à AUDIO_CHUNK_SIZE de la config.
        """
        self.sample_rate = sample_rate or AUDIO_SAMPLE_RATE
        self.channels = channels or AUDIO_CHANNELS
        self.audio_format = audio_format or AUDIO_FORMAT
        self.chunk_size = chunk_size or AUDIO_CHUNK_SIZE
        
        self.py_audio = None
        self.audio_stream = None
        self.is_recording = False
        self.recording_thread = None
        
        # Buffer circulaire pour stocker les données audio récentes
        self.buffer_duration = 2  # Durée en secondes
        self.buffer_size = int(self.buffer_duration * self.sample_rate)
        self.audio_buffer = np.zeros(self.buffer_size, dtype=np.float32)
        self.buffer_position = 0
        
        # File d'attente thread-safe pour transférer les données audio du thread d'enregistrement
        self.audio_queue = queue.Queue()
        
        # Timestamp du dernier échantillon pour la synchronisation
        self.last_sample_time = 0
        
        logger.info(f"AudioCapture initialisé avec: sample_rate={self.sample_rate}, channels={self.channels}, "
                   f"format={self.audio_format}, chunk_size={self.chunk_size}")
    
    def start(self):
        """
        Démarre la capture audio en continu.
        """
        if self.is_recording:
            logger.warning("La capture audio est déjà en cours")
            return
        
        try:
            self.py_audio = pyaudio.PyAudio()
            
            # Ouvrir le flux audio
            self.audio_stream = self.py_audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            
            logger.info("Capture audio démarrée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la capture audio: {str(e)}")
            self.stop()
            return False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback appelé par PyAudio pour chaque chunk audio capturé.
        
        Args:
            in_data (bytes): Données audio brutes
            frame_count (int): Nombre de frames dans ce chunk
            time_info (dict): Informations de timing fournies par PortAudio
            status (int): Statut de PortAudio
            
        Returns:
            tuple: (None, flag) indiquant à PyAudio de continuer
        """
        if status:
            logger.warning(f"Statut PyAudio non nul: {status}")
        
        try:
            # Convertir les bytes en array numpy
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Normaliser les données (-1.0 à 1.0)
            audio_data = audio_data.astype(np.float32) / 32768.0
            
            # Si stéréo, convertir en mono en moyennant les canaux
            if self.channels == 2:
                audio_data = audio_data.reshape(-1, 2).mean(axis=1)
            
            # Mettre à jour le timestamp du dernier échantillon
            self.last_sample_time = time.time()
            
            # Mettre à jour le buffer circulaire
            end_pos = self.buffer_position + len(audio_data)
            
            if end_pos <= self.buffer_size:
                # Cas simple: tout rentre dans le buffer sans enroulement
                self.audio_buffer[self.buffer_position:end_pos] = audio_data
            else:
                # Cas d'enroulement: on remplit la fin du buffer puis on revient au début
                first_part = self.buffer_size - self.buffer_position
                self.audio_buffer[self.buffer_position:] = audio_data[:first_part]
                self.audio_buffer[:end_pos - self.buffer_size] = audio_data[first_part:]
            
            # Mettre à jour la position du buffer
            self.buffer_position = end_pos % self.buffer_size
            
            # Ajouter à la file d'attente avec timestamp pour synchronisation éventuelle
            self.audio_queue.put({
                'data': audio_data.copy(),
                'timestamp': self.last_sample_time
            })
            
        except Exception as e:
            logger.error(f"Erreur dans le callback audio: {str(e)}")
        
        # Continuer l'enregistrement
        return (None, pyaudio.paContinue)
    
    def get_audio_data(self, duration_ms=500):
        """
        Récupère un segment audio de la durée spécifiée depuis le buffer.
        
        Args:
            duration_ms (int): Durée du segment audio en millisecondes
            
        Returns:
            dict: Données audio contenant l'échantillon brut et le timestamp
        """
        if not self.is_recording:
            logger.warning("Tentative de récupération audio alors que l'enregistrement n'est pas actif")
            return None
        
        try:
            # Calculer le nombre d'échantillons correspondant à la durée demandée
            num_samples = int((duration_ms / 1000.0) * self.sample_rate)
            
            # Extraire les données du buffer circulaire
            if self.buffer_position >= num_samples:
                # Cas simple: les données sont contiguës
                audio_segment = self.audio_buffer[self.buffer_position - num_samples:self.buffer_position]
            else:
                # Cas d'enroulement: combiner la fin et le début du buffer
                part1 = self.audio_buffer[self.buffer_size - (num_samples - self.buffer_position):]
                part2 = self.audio_buffer[:self.buffer_position]
                audio_segment = np.concatenate((part1, part2))
            
            # Retourner les données avec timestamp
            return {
                'raw_audio': audio_segment,
                'timestamp': self.last_sample_time,
                'sample_rate': self.sample_rate,
                'channels': 1,  # Toujours mono après traitement
                'duration_ms': duration_ms
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données audio: {str(e)}")
            return None
    
    def analyze_audio(self, audio_data=None, duration_ms=500):
        """
        Analyse les données audio pour extraire des caractéristiques utiles.
        Utilise les données fournies ou récupère les données récentes si non spécifiées.
        
        Args:
            audio_data (dict, optional): Données audio à analyser. 
                                         Si None, récupère automatiquement les données récentes.
            duration_ms (int): Durée du segment audio à analyser en millisecondes
            
        Returns:
            dict: Caractéristiques audio extraites
        """
        # Obtenir les données audio si non fournies
        if audio_data is None:
            audio_data = self.get_audio_data(duration_ms)
            
        if audio_data is None:
            return None
        
        try:
            # Extraire le signal audio brut
            audio_signal = audio_data.get('raw_audio')
            
            if audio_signal is None or len(audio_signal) == 0:
                return None
            
            # Calculer le niveau RMS (Root Mean Square)
            rms_level = np.sqrt(np.mean(audio_signal**2))
            
            # Détection basique de parole par le taux de passage par zéro
            # Un taux élevé indique souvent la présence de parole
            zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_signal)))) / (2 * len(audio_signal))
            
            # Analyse spectrale simple
            if len(audio_signal) > 1:
                # Transformée de Fourier rapide
                spectrum = np.abs(np.fft.rfft(audio_signal))
                freqs = np.fft.rfftfreq(len(audio_signal), 1/self.sample_rate)
                
                # Fréquence dominante
                if len(spectrum) > 0:
                    dominant_freq_idx = np.argmax(spectrum)
                    dominant_frequency = freqs[dominant_freq_idx]
                    
                    # Division du spectre en bandes
                    # Basse (<300Hz), Moyenne (300-3000Hz), Haute (>3000Hz)
                    low_mask = freqs < 300
                    mid_mask = (freqs >= 300) & (freqs <= 3000)
                    high_mask = freqs > 3000
                    
                    # Somme des puissances dans chaque bande
                    low_power = np.sum(spectrum[low_mask])
                    mid_power = np.sum(spectrum[mid_mask])
                    high_power = np.sum(spectrum[high_mask])
                    
                    # Puissance totale
                    total_power = low_power + mid_power + high_power
                    
                    # Ratios (protection contre la division par zéro)
                    if total_power > 0:
                        low_ratio = low_power / total_power
                        mid_ratio = mid_power / total_power
                        high_ratio = high_power / total_power
                    else:
                        low_ratio = mid_ratio = high_ratio = 0
                    
                else:
                    dominant_frequency = 0
                    low_ratio = mid_ratio = high_ratio = 0
            else:
                dominant_frequency = 0
                low_ratio = mid_ratio = high_ratio = 0
            
            # Détection heuristique de parole
            # La parole humaine est généralement entre 300-3000Hz avec taux de passage par zéro élevé
            speech_detected = (mid_ratio > 0.3) and (zero_crossings > 0.05)
            
            # Résultat
            return {
                'rms_level': float(rms_level),
                'zero_crossing_rate': float(zero_crossings),
                'dominant_frequency': float(dominant_frequency),
                'low_freq_ratio': float(low_ratio),
                'mid_freq_ratio': float(mid_ratio),
                'high_freq_ratio': float(high_ratio),
                'speech_detected': bool(speech_detected),
                'timestamp': audio_data.get('timestamp', time.time())
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse audio: {str(e)}")
            return None
    
    def stop(self):
        """
        Arrête la capture audio et libère les ressources.
        """
        self.is_recording = False
        
        # Fermer le flux audio
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture du flux audio: {str(e)}")
            finally:
                self.audio_stream = None
        
        # Fermer PyAudio
        if self.py_audio:
            try:
                self.py_audio.terminate()
            except Exception as e:
                logger.error(f"Erreur lors de la terminaison de PyAudio: {str(e)}")
            finally:
                self.py_audio = None
        
        logger.info("Capture audio arrêtée")
