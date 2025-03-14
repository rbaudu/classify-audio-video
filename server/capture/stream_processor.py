#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import cv2
import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)

class StreamProcessor:
    """
    Classe pour le traitement des flux vidéo et audio avant analyse.
    """
    
    def __init__(self, video_resolution=(224, 224), audio_sample_rate=16000):
        """
        Initialise le processeur de flux.
        
        Args:
            video_resolution (tuple): Résolution cible pour les images vidéo (largeur, hauteur)
            audio_sample_rate (int): Taux d'échantillonnage cible pour l'audio
        """
        self.video_resolution = video_resolution
        self.audio_sample_rate = audio_sample_rate
        
        # Historique des frames pour détection de mouvement
        self.previous_frame = None
        
        logger.info(f"Processeur de flux initialisé avec résolution vidéo {video_resolution} et taux d'échantillonnage audio {audio_sample_rate}")
    
    def process_video(self, frame):
        """
        Traite une image vidéo pour l'analyse.
        
        Ce traitement inclut:
        - Redimensionnement à la taille attendue par le modèle
        - Normalisation des valeurs de pixels
        - Extraction de caractéristiques (mouvements, couleurs dominantes, etc.)
        
        Args:
            frame (numpy.ndarray): Image à traiter
            
        Returns:
            dict: Dictionnaire contenant l'image traitée et des métadonnées extraites
        """
        if frame is None:
            return None
        
        try:
            # Convertir en niveaux de gris pour certaines analyses
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Redimensionner l'image à la taille attendue par le modèle
            resized = cv2.resize(frame, self.video_resolution)
            
            # Normaliser les valeurs de pixels (0-1)
            normalized = resized.astype(np.float32) / 255.0
            
            # Extraction de caractéristiques supplémentaires
            features = {}
            
            # 1. Détection de mouvement (si nous avons une frame précédente)
            if self.previous_frame is not None:
                # Convertir la frame précédente en niveaux de gris si ce n'est pas déjà le cas
                prev_gray = self.previous_frame if len(self.previous_frame.shape) == 2 else cv2.cvtColor(self.previous_frame, cv2.COLOR_BGR2GRAY)
                
                # Redimensionner si nécessaire
                if prev_gray.shape != gray.shape:
                    prev_gray = cv2.resize(prev_gray, (gray.shape[1], gray.shape[0]))
                
                # Calculer la différence absolue entre les frames
                frame_diff = cv2.absdiff(prev_gray, gray)
                
                # Seuillage pour identifier les zones de mouvement significatif
                _, motion_mask = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
                
                # Calculer le pourcentage de pixels en mouvement
                motion_percent = (np.sum(motion_mask) / (motion_mask.shape[0] * motion_mask.shape[1] * 255)) * 100
                features['motion_percent'] = motion_percent
            
            # 2. Analyse des couleurs dominantes
            # Conversion en espace colorimétrique HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Calcul des moyennes pour chaque canal
            h_mean = np.mean(hsv[:, :, 0])
            s_mean = np.mean(hsv[:, :, 1])
            v_mean = np.mean(hsv[:, :, 2])
            
            features['hsv_means'] = (h_mean, s_mean, v_mean)
            
            # 3. Détection de visage (simplifiée - en production, utiliser un détecteur de visage)
            # Pour simplifier, nous utilisons juste un proxy basé sur la couleur de peau
            # Dans un système réel, vous utiliseriez un modèle de détection de visage comme Haar Cascade ou un réseau neuronal
            
            # Plage approximative de couleur de peau en HSV
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            
            # Création d'un masque pour la couleur de peau
            skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
            
            # Pourcentage de pixels correspondant potentiellement à de la peau
            skin_percent = (np.sum(skin_mask) / (skin_mask.shape[0] * skin_mask.shape[1] * 255)) * 100
            features['skin_percent'] = skin_percent
            
            # Mettre à jour la frame précédente
            self.previous_frame = gray
            
            # Résultat sous forme de dictionnaire
            result = {
                'processed_frame': normalized,
                'features': features
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement vidéo: {str(e)}")
            return None
    
    def process_audio(self, audio_data):
        """
        Traite des données audio pour l'analyse.
        
        Ce traitement inclut:
        - Rééchantillonnage si nécessaire
        - Normalisation des amplitudes
        - Extraction de caractéristiques (niveau sonore, fréquences dominantes, etc.)
        
        Args:
            audio_data (numpy.ndarray): Données audio à traiter
            
        Returns:
            dict: Dictionnaire contenant l'audio traité et des métadonnées extraites
        """
        if audio_data is None:
            return None
        
        try:
            # Normalisation de l'amplitude (-1 à 1)
            if np.max(np.abs(audio_data)) > 0:
                normalized = audio_data / np.max(np.abs(audio_data))
            else:
                normalized = audio_data
            
            # Extraction de caractéristiques
            features = {}
            
            # 1. Niveau sonore (RMS)
            rms = np.sqrt(np.mean(normalized**2))
            features['rms_level'] = float(rms)
            
            # 2. Détection de voix/parole (simplifiée)
            # Dans une implémentation réelle, vous utiliseriez un modèle de détection de voix
            # Pour simplifier, nous utilisons une heuristique basée sur l'énergie et le ZCR
            
            # Zero-Crossing Rate (taux de passage par zéro) - indicateur utile pour la parole
            zcr = np.sum(np.abs(np.diff(np.signbit(normalized)))) / (2 * len(normalized))
            features['zero_crossing_rate'] = float(zcr)
            
            # 3. Analyse fréquentielle simple
            if len(normalized) > 0:
                # Transformée de Fourier rapide (FFT)
                fft_result = np.abs(np.fft.rfft(normalized))
                
                # Fréquences correspondantes
                freqs = np.fft.rfftfreq(len(normalized), 1/self.audio_sample_rate)
                
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
            
            # Résultat sous forme de dictionnaire
            result = {
                'processed_audio': normalized,
                'features': features
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement audio: {str(e)}")
            return None
