#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import numpy as np
import os
import time
import tensorflow as tf
from tensorflow.keras.models import load_model
import cv2

# Import de la configuration
from server import ACTIVITY_CLASSES, MODEL_PATH

logger = logging.getLogger(__name__)

class ActivityClassifier:
    """
    Classe pour la classification de l'activité basée sur l'analyse des flux audio et vidéo.
    Utilise un modèle de deep learning pour identifier l'activité parmi les catégories prédéfinies.
    """
    
    def __init__(self, obs_capture, stream_processor, db_manager, model_path=None):
        """
        Initialise le classificateur d'activité.
        
        Args:
            obs_capture: Instance de OBSCapture pour capturer les images et l'audio
            stream_processor: Instance de StreamProcessor pour traiter les données
            db_manager: Instance de DBManager pour accéder à la base de données
            model_path (str, optional): Chemin vers le modèle de classification pré-entraîné.
                Si None, utilise le chemin défini dans la configuration ou un modèle de règles prédéfinies simple.
        """
        self.obs_capture = obs_capture
        self.stream_processor = stream_processor
        self.db_manager = db_manager
        
        # Utiliser le model_path passé ou celui de la configuration
        self.model_path = model_path or MODEL_PATH
        self.model = None
        self.rule_based = False
        
        # Liste des catégories d'activité
        self.activity_classes = ACTIVITY_CLASSES
        
        # Chargement du modèle s'il est spécifié
        if self.model_path and os.path.exists(self.model_path):
            try:
                self.model = load_model(self.model_path)
                logger.info(f"Modèle de classification chargé depuis {self.model_path}")
            except Exception as e:
                logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
                self.rule_based = True
                logger.info("Utilisation du classificateur basé sur des règles prédéfinies")
        else:
            self.rule_based = True
            logger.info("Modèle non spécifié ou introuvable. Utilisation du classificateur basé sur des règles prédéfinies")
    
    def analyze_current_activity(self):
        """
        Capture et analyse l'activité courante
        
        Returns:
            dict: Résultat de la classification ou None en cas d'erreur
        """
        try:
            # Capturer une image
            frame = self.obs_capture.get_current_frame()
            
            # Capturer l'audio
            audio_data = self.obs_capture.get_current_audio()
            
            if frame is None or audio_data is None:
                logger.warning("Impossible de capturer l'image ou l'audio")
                return None
            
            # Traiter les données
            video_features = self.stream_processor.process_video(frame)
            audio_features = self.stream_processor.process_audio(audio_data)
            
            # Classifier l'activité
            result = self.classify_activity(video_features, audio_features)
            
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'activité courante: {str(e)}")
            return None
    
    def classify_activity(self, video_features, audio_features):
        """
        Classifie l'activité à partir des caractéristiques vidéo et audio
        
        Args:
            video_features (dict): Caractéristiques vidéo extraites
            audio_features (dict): Caractéristiques audio extraites
            
        Returns:
            dict: Résultat de la classification
        """
        if video_features is None or audio_features is None:
            logger.warning("Caractéristiques vidéo ou audio manquantes")
            return None
        
        try:
            # Détermination de l'activité
            if self.rule_based:
                activity = self._rule_based_classification(video_features, audio_features)
                confidence = 0.7  # Confiance fixe pour la méthode basée sur les règles
                confidence_scores = {cls: 0.1 for cls in self.activity_classes}
                confidence_scores[activity] = confidence
            else:
                activity, confidence, confidence_scores = self._model_based_classification(video_features, audio_features)
            
            # Résultat sous forme de dictionnaire
            result = {
                'activity': activity,
                'confidence': confidence,
                'confidence_scores': confidence_scores,
                'timestamp': int(time.time()),
                'features': {
                    'video': video_features.get('features', {}),
                    'audio': audio_features.get('features', {})
                }
            }
            
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la classification: {str(e)}")
            return None
    
    def _rule_based_classification(self, video_data, audio_data):
        """
        Classification basée sur des règles prédéfinies simples.
        Utilisée comme solution de repli si le modèle de deep learning n'est pas disponible.
        
        Args:
            video_data (dict): Données vidéo traitées
            audio_data (dict): Données audio traitées
            
        Returns:
            str: Catégorie d'activité détectée
        """
        # Extraire les caractéristiques
        video_features = video_data.get('features', {})
        audio_features = audio_data.get('features', {})
        
        # Niveau de mouvement
        motion_percent = video_features.get('motion_percent', 0)
        
        # Niveau sonore
        audio_level = audio_features.get('rms_level', 0)
        
        # Caractéristiques de parole
        zcr = audio_features.get('zero_crossing_rate', 0)
        mid_freq_ratio = audio_features.get('mid_freq_ratio', 0)
        
        # Détection de visage/personne (simplifiée)
        skin_percent = video_features.get('skin_percent', 0)
        
        # Logique de classification basée sur des heuristiques
        
        # 1. "endormi" - très peu de mouvement, peu ou pas de son
        if motion_percent < 2 and audio_level < 0.1:
            return 'endormi'
        
        # 2. "à table" - mouvement modéré, posture assise (proxy simplifié)
        hsv_means = video_features.get('hsv_means', (0, 0, 0))
        # Des surfaces horizontales comme une table pourraient avoir des caractéristiques spécifiques
        # Ce proxy est très simplifié et devrait être amélioré
        if 5 < motion_percent < 15 and hsv_means[2] > 100:  # Valeur de luminosité plus élevée
            return 'à table'
        
        # 3. "lisant" - peu de mouvement, position statique, orientation de la tête baissée
        # Difficile à détecter avec des règles simples, mais on peut faire une approximation
        if 2 < motion_percent < 10 and audio_level < 0.2:
            return 'lisant'
        
        # 4. "au téléphone" - profil spécifique de parole, posture caractéristique
        # Marqué par la parole avec peu de mouvement
        if audio_level > 0.3 and zcr > 0.05 and mid_freq_ratio > 0.4 and motion_percent < 10:
            return 'au téléphone'
        
        # 5. "en conversation" - parole active, plus de mouvement que "au téléphone"
        if audio_level > 0.25 and zcr > 0.05 and mid_freq_ratio > 0.4 and motion_percent > 10:
            return 'en conversation'
        
        # 6. "occupé" - beaucoup de mouvement mais pas nécessairement de la parole
        if motion_percent > 20:
            return 'occupé'
        
        # 7. "inactif" - peu de mouvement, peu de son, cas par défaut
        return 'inactif'
    
    def _model_based_classification(self, video_data, audio_data):
        """
        Classification basée sur le modèle de deep learning.
        
        Args:
            video_data (dict): Données vidéo traitées
            audio_data (dict): Données audio traitées
            
        Returns:
            tuple: (activité détectée, niveau de confiance, scores pour toutes les classes)
        """
        # Préparation des données pour le modèle
        video_frame = video_data.get('processed_frame')
        
        # Extraction et préparation des caractéristiques audio importantes
        audio_features = []
        for feature in ['rms_level', 'zero_crossing_rate', 'dominant_frequency',
                       'low_freq_ratio', 'mid_freq_ratio', 'high_freq_ratio']:
            value = audio_data.get('features', {}).get(feature, 0)
            audio_features.append(value)
        
        # Normalisation des caractéristiques audio (exemple simplifié)
        audio_features = np.array(audio_features, dtype=np.float32)
        
        # Préparation de l'image (ajout de la dimension de batch)
        input_image = np.expand_dims(video_frame, axis=0)
        
        # Ajout de la dimension de batch pour l'audio
        audio_features = np.expand_dims(audio_features, axis=0)
        
        try:
            # Prédiction avec le modèle
            predictions = self.model.predict([input_image, audio_features])
            
            # Obtention de la classe prédite
            predicted_class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_idx])
            
            # Vérification que l'index est valide
            if 0 <= predicted_class_idx < len(self.activity_classes):
                activity = self.activity_classes[predicted_class_idx]
            else:
                logger.warning(f"Index de classe prédit invalide: {predicted_class_idx}")
                activity = 'inactif'
                confidence = 0.5
            
            # Conversion des scores en dictionnaire
            all_scores = {self.activity_classes[i]: float(score) for i, score in enumerate(predictions[0]) if i < len(self.activity_classes)}
            
            return activity, confidence, all_scores
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification par modèle: {str(e)}")
            # Fallback sur la méthode basée sur des règles
            activity = self._rule_based_classification(video_data, audio_data)
            confidence = 0.5  # Confiance réduite puisque c'est une solution de repli
            all_scores = {cls: 0.1 for cls in self.activity_classes}
            all_scores[activity] = confidence
            
            return activity, confidence, all_scores
    
    def train(self, training_data, epochs=10, batch_size=32, validation_split=0.2, save_path=None):
        """
        Entraîne ou met à jour le modèle de classification.
        
        Args:
            training_data (dict): Données d'entraînement contenant 'X_video', 'X_audio' et 'y'
            epochs (int): Nombre d'époques d'entraînement
            batch_size (int): Taille du batch pour l'entraînement
            validation_split (float): Fraction des données à utiliser pour la validation
            save_path (str, optional): Chemin où sauvegarder le modèle entraîné
            
        Returns:
            dict: Historique d'entraînement
        """
        # Cette méthode est incluse pour montrer comment le modèle pourrait être entraîné,
        # mais l'implémentation détaillée dépend de l'architecture spécifique et des données
        
        if self.model is None:
            logger.error("Pas de modèle disponible pour l'entraînement")
            return None
        
        try:
            # Extraction des données d'entraînement
            X_video = training_data.get('X_video')
            X_audio = training_data.get('X_audio')
            y = training_data.get('y')
            
            if X_video is None or X_audio is None or y is None:
                logger.error("Données d'entraînement incomplètes")
                return None
            
            # Entraînement du modèle
            history = self.model.fit(
                [X_video, X_audio], y,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split
            )
            
            # Sauvegarde du modèle si demandé
            if save_path:
                self.model.save(save_path)
                logger.info(f"Modèle entraîné sauvegardé à {save_path}")
            
            return history.history
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle: {str(e)}")
            return None
