#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import numpy as np
import os
import time
import threading
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
    
    def __init__(self, capture_manager=None, stream_processor=None, db_manager=None, model_path=None):
        """
        Initialise le classificateur d'activité.
        
        Args:
            capture_manager: Instance de SyncManager pour capturer les données audio/vidéo synchronisées
            stream_processor: Instance de StreamProcessor pour traiter les données
            db_manager: Instance de DBManager pour accéder à la base de données
            model_path (str, optional): Chemin vers le modèle de classification pré-entraîné.
                Si None, utilise le chemin défini dans la configuration ou un modèle de règles prédéfinies simple.
        """
        self.capture_manager = capture_manager
        self.stream_processor = stream_processor
        self.db_manager = db_manager
        self.analysis_thread = None
        self.stop_analysis = False
        self.last_activity = None
        self.last_activity_time = 0
        
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
            # Vérifier si les dépendances sont disponibles
            if self.capture_manager is None:
                logger.warning("Gestionnaire de capture non disponible")
                # Simuler des caractéristiques pour les tests ou utiliser la dernière activité connue
                if self.last_activity and time.time() - self.last_activity_time < 60:  # Valide pendant 1 minute
                    logger.info("Utilisation de la dernière activité connue (pas de capture disponible)")
                    return self.last_activity
                
                # Simuler des caractéristiques pour les tests
                video_features = {
                    'features': {
                        'motion_percent': 5,
                        'skin_percent': 20,
                        'hsv_means': (100, 50, 150)
                    }
                }
                
                audio_features = {
                    'features': {
                        'rms_level': 0.3,
                        'zero_crossing_rate': 0.06,
                        'dominant_frequency': 220,
                        'mid_freq_ratio': 0.45
                    }
                }
                
                # Classifier l'activité
                result = self.classify_activity(video_features, audio_features)
                self.last_activity = result
                self.last_activity_time = time.time()
                return result
            
            # Récupérer les données synchronisées
            sync_data = self.capture_manager.get_synchronized_data()
            
            if sync_data is None:
                logger.warning("Impossible de récupérer les données synchronisées")
                # Utiliser la dernière activité connue comme fallback
                if self.last_activity and time.time() - self.last_activity_time < 60:  # Valide pendant 1 minute
                    logger.info("Utilisation de la dernière activité connue (échec de synchronisation)")
                    return self.last_activity
                return None
            
            # Utiliser les données vidéo et audio déjà traitées
            video_features = sync_data.get('video', {}).get('processed')
            audio_features = sync_data.get('audio', {}).get('processed')
            
            if video_features is None and audio_features is None:
                logger.warning("Données vidéo et audio traitées manquantes")
                # Utiliser la dernière activité connue comme fallback
                if self.last_activity and time.time() - self.last_activity_time < 60:
                    logger.info("Utilisation de la dernière activité connue (pas de données)")
                    return self.last_activity
                return None
            
            # Si l'une des caractéristiques est manquante, générer des valeurs par défaut
            if video_features is None:
                logger.warning("Données vidéo manquantes, utilisation de valeurs par défaut")
                video_features = {
                    'features': {
                        'motion_percent': 5,
                        'skin_percent': 0,
                        'hsv_means': (0, 0, 0)
                    }
                }
            
            if audio_features is None:
                logger.warning("Données audio manquantes, utilisation de valeurs par défaut")
                audio_features = {
                    'features': {
                        'rms_level': 0.1,
                        'zero_crossing_rate': 0.01,
                        'dominant_frequency': 0,
                        'mid_freq_ratio': 0.3
                    }
                }
            
            # Classifier l'activité
            result = self.classify_activity(video_features, audio_features)
            
            # Sauvegarder comme dernière activité connue
            if result:
                self.last_activity = result
                self.last_activity_time = time.time()
            
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'activité courante: {str(e)}")
            # Utiliser la dernière activité connue comme fallback en cas d'erreur
            if self.last_activity and time.time() - self.last_activity_time < 60:
                logger.info("Utilisation de la dernière activité connue (suite à une erreur)")
                return self.last_activity
            return None
    
    def start_periodic_analysis(self, sync_manager=None, interval=300):
        """
        Démarre l'analyse périodique en arrière-plan
        
        Args:
            sync_manager: Gestionnaire de synchronisation (si non fourni au constructeur)
            interval: Intervalle entre les analyses (en secondes)
        """
        if sync_manager is not None:
            self.capture_manager = sync_manager
            logger.info(f"SyncManager fourni pour l'analyse périodique: {sync_manager}")
        
        # Arrêter l'analyse en cours si elle existe
        self.stop_analysis = True
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=1.0)
        
        # Réinitialiser et démarrer un nouveau thread
        self.stop_analysis = False
        self.analysis_thread = threading.Thread(
            target=self._analysis_loop,
            args=(interval,),
            daemon=True
        )
        self.analysis_thread.start()
        
        logger.info(f"Boucle d'analyse démarrée avec intervalle de {interval} secondes")
    
    def _analysis_loop(self, interval):
        """
        Boucle d'analyse périodique
        
        Args:
            interval: Intervalle entre les analyses (en secondes)
        """
        logger.info("Démarrage de la boucle d'analyse périodique")
        
        while not self.stop_analysis:
            try:
                # Analyser l'activité actuelle
                result = self.analyze_current_activity()
                
                if result:
                    # Sauvegarder dans la base de données si disponible
                    if self.db_manager:
                        self.db_manager.save_activity(
                            activity=result['activity'],
                            confidence=result['confidence'],
                            metadata=result['features']
                        )
                    
                    logger.info(f"Activité détectée: {result['activity']} (confiance: {result['confidence']:.2f})")
                else:
                    logger.warning("Aucune activité détectée lors de cette analyse")
                
                # Attendre l'intervalle spécifié, mais en vérifiant régulièrement 
                # pour permettre un arrêt plus rapide
                for _ in range(min(interval, 300)):  # Max 5 minutes
                    if self.stop_analysis:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Erreur dans la boucle d'analyse: {str(e)}")
                time.sleep(10)  # Attendre un peu avant de réessayer en cas d'erreur
    
    def stop_periodic_analysis(self):
        """
        Arrête l'analyse périodique
        """
        self.stop_analysis = True
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=2.0)
            logger.info("Analyse périodique arrêtée")
    
    def classify_activity(self, video_features, audio_features):
        """
        Classifie l'activité à partir des caractéristiques vidéo et audio
        
        Args:
            video_features (dict): Caractéristiques vidéo extraites
            audio_features (dict): Caractéristiques audio extraites
            
        Returns:
            dict: Résultat de la classification
        """
        if video_features is None and audio_features is None:
            logger.warning("Caractéristiques vidéo et audio manquantes")
            return None
        
        try:
            # S'assurer que les caractéristiques ont la bonne structure
            if not isinstance(video_features, dict):
                video_features = {'features': {}}
            if 'features' not in video_features:
                video_features['features'] = {}
            
            if not isinstance(audio_features, dict):
                audio_features = {'features': {}}
            if 'features' not in audio_features:
                audio_features['features'] = {}
            
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
            # Mode de secours minimal
            return {
                'activity': 'inactif',
                'confidence': 0.5,
                'confidence_scores': {cls: 0.1 for cls in self.activity_classes},
                'timestamp': int(time.time()),
                'features': {}
            }
    
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
        input_image = np.expand_dims(video_frame, axis=0) if video_frame is not None else None
        
        # Ajout de la dimension de batch pour l'audio
        audio_features = np.expand_dims(audio_features, axis=0)
        
        try:
            # Vérifier si le modèle et les entrées sont valides
            if self.model is None or input_image is None:
                raise ValueError("Modèle ou données d'entrée non disponibles")
            
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
