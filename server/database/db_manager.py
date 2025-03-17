#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sqlite3
import json
import time
import os
import threading
import random
from datetime import datetime, timedelta

# Import de la configuration
from server import BASE_DIR

logger = logging.getLogger(__name__)

class DBManager:
    """
    Gestionnaire de base de données pour l'application.
    Gère la connexion à la base de données et les opérations CRUD.
    """
    
    def __init__(self, db_path=None):
        """
        Initialise le gestionnaire de base de données.
        
        Args:
            db_path (str, optional): Chemin vers le fichier de base de données.
                Si None, utilise le chemin par défaut dans le répertoire data.
        """
        # Définir le chemin par défaut si non spécifié
        if db_path is None:
            self.db_path = os.path.join(BASE_DIR, '..', 'data', 'activity.db')
        else:
            self.db_path = db_path
        
        # S'assurer que le répertoire parent existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Verrou pour éviter les accès concurrents
        self.lock = threading.RLock()
        
        # Initialiser la base de données
        self._init_db()
        
        # Créer des données factices pour les tests si la base est vide
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM activities")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count == 0:
                logger.info("Base de données vide, création de données factices pour les tests")
                self._create_fake_data()
            
        logger.info("Base de données initialisée avec succès")
    
    def _init_db(self):
        """
        Initialise la structure de la base de données.
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Créer les tables si elles n'existent pas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp INTEGER NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # Index pour optimiser les requêtes par timestamp
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities (timestamp)
            ''')
            
            conn.commit()
            conn.close()
    
    def save_activity(self, activity, confidence, metadata=None, timestamp=None):
        """
        Sauvegarde une activité détectée dans la base de données.
        
        Args:
            activity (str): Nom de l'activité détectée
            confidence (float): Niveau de confiance de la détection (0.0 à 1.0)
            metadata (dict, optional): Métadonnées supplémentaires (caractéristiques utilisées, etc.)
            timestamp (int, optional): Horodatage Unix. Si None, utilise le timestamp actuel.
            
        Returns:
            int: ID de l'activité enregistrée ou None en cas d'erreur
        """
        try:
            # Utiliser le timestamp actuel si non spécifié
            if timestamp is None:
                timestamp = int(time.time())
            
            # Convertir les métadonnées en JSON si présentes
            metadata_json = json.dumps(metadata) if metadata else None
            
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute(
                    "INSERT INTO activities (activity, confidence, timestamp, metadata) VALUES (?, ?, ?, ?)",
                    (activity, confidence, timestamp, metadata_json)
                )
                
                activity_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return activity_id
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'activité: {str(e)}")
            return None
    
    def get_activity_by_id(self, activity_id):
        """
        Récupère une activité par son ID.
        
        Args:
            activity_id (int): ID de l'activité à récupérer
            
        Returns:
            dict: Données de l'activité ou None si non trouvée
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
                row = cursor.fetchone()
                
                if row:
                    activity = dict(row)
                    
                    # Convertir les métadonnées JSON en dict si présentes
                    if activity['metadata']:
                        activity['metadata'] = json.loads(activity['metadata'])
                    
                    conn.close()
                    return activity
                
                conn.close()
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'activité: {str(e)}")
            return None
    
    def get_current_activity(self):
        """
        Récupère l'activité la plus récente.
        
        Returns:
            dict: Données de l'activité la plus récente ou None si aucune
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM activities ORDER BY timestamp DESC LIMIT 1")
                row = cursor.fetchone()
                
                if row:
                    activity = dict(row)
                    
                    # Convertir les métadonnées JSON en dict si présentes
                    if activity['metadata']:
                        activity['metadata'] = json.loads(activity['metadata'])
                    
                    conn.close()
                    return activity
                
                conn.close()
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'activité actuelle: {str(e)}")
            return None
    
    def get_activities(self, start_time=None, end_time=None, limit=1000):
        """
        Récupère les activités dans une plage de temps.
        
        Args:
            start_time (int, optional): Timestamp de début (Unix)
            end_time (int, optional): Timestamp de fin (Unix)
            limit (int, optional): Nombre maximum d'activités à récupérer
            
        Returns:
            list: Liste des activités ou liste vide en cas d'erreur
        """
        try:
            # Utiliser une plage par défaut si non spécifiée
            if end_time is None:
                end_time = int(time.time())
            if start_time is None:
                start_time = end_time - 86400  # 24 heures avant
            
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM activities WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp DESC LIMIT ?",
                    (start_time, end_time, limit)
                )
                
                rows = cursor.fetchall()
                
                activities = []
                for row in rows:
                    activity = dict(row)
                    
                    # Convertir les métadonnées JSON en dict si présentes
                    if activity['metadata']:
                        activity['metadata'] = json.loads(activity['metadata'])
                    
                    activities.append(activity)
                
                conn.close()
                return activities
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des activités: {str(e)}")
            return []
    
    def get_activity_statistics(self, period='day'):
        """
        Calcule les statistiques d'activité pour une période donnée.
        
        Args:
            period (str): Période ('day', 'week', 'month', 'year')
            
        Returns:
            dict: Statistiques d'activité ou None en cas d'erreur
        """
        try:
            # Définir la plage de temps en fonction de la période
            end_time = int(time.time())
            
            if period == 'day':
                start_time = end_time - 86400  # 24 heures
            elif period == 'week':
                start_time = end_time - 604800  # 7 jours
            elif period == 'month':
                start_time = end_time - 2592000  # 30 jours
            elif period == 'year':
                start_time = end_time - 31536000  # 365 jours
            else:
                start_time = end_time - 86400  # Par défaut: 24 heures
            
            # Récupérer les activités pour la période
            activities = self.get_activities(start_time, end_time)
            
            if not activities:
                # Générer des données factices si aucune activité
                logger.warning(f"Aucune activité trouvée pour la période {period}. Génération de données factices.")
                activities = self._generate_fake_activities(start_time, end_time)
            
            # Initialiser les compteurs
            activity_counts = {}
            activity_durations = {}
            
            # Traiter les activités
            prev_activity = None
            prev_timestamp = None
            total_classifications = 0
            
            for activity in activities:
                activity_name = activity['activity']
                timestamp = activity['timestamp']
                
                # Incrémenter le compteur pour cette activité
                activity_counts[activity_name] = activity_counts.get(activity_name, 0) + 1
                total_classifications += 1
                
                # Calculer la durée (approximative)
                if prev_activity == activity_name and prev_timestamp:
                    duration = timestamp - prev_timestamp
                    if duration < 3600:  # Ignorer les durées suspicieusement longues (> 1h)
                        activity_durations[activity_name] = activity_durations.get(activity_name, 0) + duration
                
                prev_activity = activity_name
                prev_timestamp = timestamp
            
            # Créer la structure de données pour les tendances
            trends = self._calculate_trends(activities, period)
            
            # Créer la structure de données pour la distribution horaire
            hourly_distribution = self._calculate_hourly_distribution(activities)
            
            # Retourner les statistiques
            statistics = {
                'period': period,
                'start_time': start_time,
                'end_time': end_time,
                'activity_counts': activity_counts,
                'activity_durations': activity_durations,
                'total_classifications': total_classifications,
                'trends': trends,
                'hourly_distribution': hourly_distribution
            }
            
            return statistics
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return None
    
    def _calculate_trends(self, activities, period):
        """
        Calcule les tendances d'activité pour une période donnée.
        
        Args:
            activities (list): Liste des activités
            period (str): Période ('day', 'week', 'month', 'year')
            
        Returns:
            list: Liste des points de tendance
        """
        try:
            if not activities:
                return []
            
            # Définir les paramètres en fonction de la période
            if period == 'day':
                interval = 3600  # 1 heure
                format_string = '%H:00'
            elif period == 'week':
                interval = 86400  # 1 jour
                format_string = '%a'
            elif period == 'month':
                interval = 86400 * 2  # 2 jours
                format_string = 'Jour %d'
            elif period == 'year':
                interval = 86400 * 30  # 30 jours
                format_string = '%b'
            else:
                interval = 3600  # Par défaut: 1 heure
                format_string = '%H:00'
            
            # Trier les activités par horodatage
            sorted_activities = sorted(activities, key=lambda x: x['timestamp'])
            
            # Regrouper les activités par intervalle
            trends = []
            current_interval = {}
            
            if sorted_activities:
                start_time = sorted_activities[0]['timestamp']
                end_time = sorted_activities[-1]['timestamp']
                
                # Créer des intervalles
                for interval_start in range(start_time, end_time + interval, interval):
                    interval_end = interval_start + interval
                    interval_activities = {}
                    
                    # Compter les activités dans cet intervalle
                    for activity in sorted_activities:
                        if interval_start <= activity['timestamp'] < interval_end:
                            activity_name = activity['activity']
                            interval_activities[activity_name] = interval_activities.get(activity_name, 0) + 1
                    
                    # Formater la date pour l'affichage
                    if period == 'month':
                        # Pour le format 'Jour X'
                        day_num = ((interval_start - start_time) // 86400) * 2 + 1
                        date_label = format_string % day_num
                    else:
                        date_label = datetime.fromtimestamp(interval_start).strftime(format_string)
                    
                    trends.append({
                        'date': date_label,
                        'timestamp': interval_start,
                        'activities': interval_activities
                    })
            
            return trends
        except Exception as e:
            logger.error(f"Erreur lors du calcul des tendances: {str(e)}")
            return []
    
    def _calculate_hourly_distribution(self, activities):
        """
        Calcule la distribution horaire des activités.
        
        Args:
            activities (list): Liste des activités
            
        Returns:
            list: Distribution horaire des activités
        """
        try:
            # Initialiser la distribution pour chaque heure
            hourly_distribution = []
            for hour in range(24):
                hourly_distribution.append({
                    'hour': hour,
                    'activities': {}
                })
            
            # Compter les activités par heure
            for activity in activities:
                timestamp = activity['timestamp']
                activity_name = activity['activity']
                
                hour = datetime.fromtimestamp(timestamp).hour
                
                hour_data = hourly_distribution[hour]
                hour_data['activities'][activity_name] = hour_data['activities'].get(activity_name, 0) + 1
            
            return hourly_distribution
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la distribution horaire: {str(e)}")
            return []
    
    def delete_activity(self, activity_id):
        """
        Supprime une activité de la base de données.
        
        Args:
            activity_id (int): ID de l'activité à supprimer
            
        Returns:
            bool: True si succès, False si échec
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
                
                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                
                return success
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'activité: {str(e)}")
            return False
    
    def delete_old_activities(self, older_than_days=30):
        """
        Supprime les anciennes activités de la base de données.
        
        Args:
            older_than_days (int): Supprimer les activités plus anciennes que ce nombre de jours
            
        Returns:
            int: Nombre d'activités supprimées
        """
        try:
            # Calculer le timestamp limite
            limit_timestamp = int(time.time()) - (older_than_days * 86400)
            
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM activities WHERE timestamp < ?", (limit_timestamp,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                logger.info(f"Suppression de {deleted_count} anciennes activités")
                return deleted_count
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des anciennes activités: {str(e)}")
            return 0
    
    def _generate_fake_activities(self, start_time, end_time):
        """
        Génère une liste d'activités fictives pour la période spécifiée.
        
        Args:
            start_time (int): Timestamp de début (Unix)
            end_time (int): Timestamp de fin (Unix)
            
        Returns:
            list: Liste d'activités fictives
        """
        # Liste des activités possibles
        activities = ['endormi', 'à table', 'lisant', 'au téléphone', 'en conversation', 'occupé', 'inactif']
        
        fake_activities = []
        
        # Déterminer l'intervalle entre les activités
        total_duration = end_time - start_time
        
        # Généralement une activité toutes les 15 minutes en moyenne
        interval = 900
        
        # Nombre approximatif d'activités à générer
        num_activities = total_duration // interval
        
        for i in range(num_activities):
            # Horodatage entre start_time et end_time
            timestamp = start_time + (i * interval) + random.randint(-60, 60)
            
            # Déterminer l'activité en fonction de l'heure de la journée
            hour = datetime.fromtimestamp(timestamp).hour
            
            # Probabilités différentes selon l'heure
            if 0 <= hour < 6:  # Nuit
                weights = [0.7, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]
            elif 6 <= hour < 8:  # Matin
                weights = [0.05, 0.6, 0.05, 0.05, 0.1, 0.1, 0.05]
            elif 8 <= hour < 12:  # Avant-midi
                weights = [0.05, 0.05, 0.1, 0.1, 0.1, 0.5, 0.1]
            elif 12 <= hour < 14:  # Midi
                weights = [0.05, 0.5, 0.1, 0.1, 0.1, 0.1, 0.05]
            elif 14 <= hour < 18:  # Après-midi
                weights = [0.05, 0.05, 0.1, 0.1, 0.1, 0.5, 0.1]
            elif 18 <= hour < 20:  # Soirée
                weights = [0.05, 0.4, 0.1, 0.1, 0.2, 0.1, 0.05]
            elif 20 <= hour < 22:  # Fin de soirée
                weights = [0.05, 0.05, 0.4, 0.1, 0.1, 0.1, 0.2]
            else:  # Nuit
                weights = [0.4, 0.05, 0.1, 0.05, 0.05, 0.05, 0.3]
            
            # Choisir une activité selon les probabilités
            activity = random.choices(activities, weights=weights)[0]
            
            # Niveau de confiance (entre 0.7 et 0.95)
            confidence = random.uniform(0.7, 0.95)
            
            # Métadonnées factices
            metadata = {
                'features': {
                    'video': {
                        'motion_percent': random.uniform(5, 30),
                        'skin_percent': random.uniform(0, 20),
                        'hsv_means': (
                            random.uniform(0, 180),  # H
                            random.uniform(0, 255),  # S
                            random.uniform(50, 200)   # V
                        )
                    },
                    'audio': {
                        'rms_level': random.uniform(0.1, 0.6),
                        'zero_crossing_rate': random.uniform(0.01, 0.1),
                        'dominant_frequency': random.uniform(100, 1000),
                        'mid_freq_ratio': random.uniform(0.3, 0.7)
                    }
                }
            }
            
            # Ajouter l'activité fictive
            fake_activities.append({
                'id': -1 * (i + 1),  # IDs négatifs pour indiquer qu'ils sont fictifs
                'activity': activity,
                'confidence': confidence,
                'timestamp': timestamp,
                'metadata': metadata
            })
        
        # Trier par horodatage
        fake_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Sauvegarder ces activités fictives dans la base de données pour une utilisation future
        self._save_fake_activities(fake_activities)
        
        return fake_activities
    
    def _save_fake_activities(self, fake_activities):
        """
        Sauvegarde les activités fictives dans la base de données.
        
        Args:
            fake_activities (list): Liste d'activités fictives
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Utiliser une transaction pour accélérer l'insertion
                conn.execute("BEGIN TRANSACTION")
                
                for activity in fake_activities:
                    # Convertir les métadonnées en JSON
                    metadata_json = json.dumps(activity['metadata'])
                    
                    cursor.execute(
                        "INSERT INTO activities (activity, confidence, timestamp, metadata) VALUES (?, ?, ?, ?)",
                        (activity['activity'], activity['confidence'], activity['timestamp'], metadata_json)
                    )
                
                conn.commit()
                conn.close()
                
                logger.info(f"Sauvegarde de {len(fake_activities)} activités fictives dans la base de données")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des activités fictives: {str(e)}")
    
    def _create_fake_data(self):
        """
        Crée des données factices pour les tests et la démonstration.
        """
        # Générer des données pour la semaine passée
        end_time = int(time.time())
        start_time = end_time - (7 * 24 * 3600)  # 7 jours
        
        # Générer et sauvegarder les activités fictives
        self._generate_fake_activities(start_time, end_time)
        
        logger.info("Création de données factices terminée")
