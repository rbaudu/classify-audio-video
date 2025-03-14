#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sqlite3
import os
import time
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DBManager:
    """
    Classe pour la gestion de la base de données des activités détectées.
    """
    
    def __init__(self, db_path):
        """
        Initialise le gestionnaire de base de données.
        
        Args:
            db_path (str): Chemin vers le fichier de base de données SQLite
        """
        self.db_path = db_path
        
        # Création du dossier parent si nécessaire
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        logger.info(f"Gestionnaire de base de données initialisé avec {db_path}")
    
    def get_connection(self):
        """
        Établit une connexion à la base de données.
        
        Returns:
            sqlite3.Connection: Connexion à la base de données
        """
        conn = sqlite3.connect(self.db_path)
        # Configuration pour récupérer les résultats sous forme de dictionnaires
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """
        Initialise la structure de la base de données si elle n'existe pas déjà.
        
        Returns:
            bool: True si l'initialisation a réussi, False sinon
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Création de la table des activités
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    date_time TEXT NOT NULL,
                    activity TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    metadata TEXT
                )
            ''')
            
            # Création d'index pour des requêtes optimisées
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON activities(timestamp)')
            
            conn.commit()
            logger.info("Base de données initialisée avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def save_activity(self, timestamp, activity, confidence=1.0, metadata=None):
        """
        Enregistre une activité détectée dans la base de données.
        
        Args:
            timestamp (int): Horodatage Unix de l'activité
            activity (str): Type d'activité détectée
            confidence (float, optional): Niveau de confiance de la détection (0-1)
            metadata (dict, optional): Métadonnées supplémentaires
            
        Returns:
            int: ID de l'enregistrement créé
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Conversion de l'horodatage en date/heure lisible
            date_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            # Conversion des métadonnées en JSON si nécessaire
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Insertion de l'activité
            cursor.execute('''
                INSERT INTO activities (timestamp, date_time, activity, confidence, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, date_time, activity, confidence, metadata_json))
            
            conn.commit()
            activity_id = cursor.lastrowid
            
            logger.info(f"Activité '{activity}' enregistrée à {date_time} (ID: {activity_id})")
            return activity_id
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement d'une activité: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_latest_activity(self):
        """
        Récupère l'activité la plus récente.
        
        Returns:
            dict: Informations sur l'activité la plus récente
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM activities
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            
            if result:
                # Conversion en dictionnaire
                activity = dict(result)
                
                # Décodage des métadonnées si présentes
                if activity.get('metadata'):
                    activity['metadata'] = json.loads(activity['metadata'])
                
                return activity
            else:
                logger.warning("Aucune activité trouvée")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'activité récente: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_activities(self, start_time=None, end_time=None, limit=100):
        """
        Récupère les activités dans un intervalle de temps donné.
        
        Args:
            start_time (int, optional): Horodatage de début
            end_time (int, optional): Horodatage de fin
            limit (int, optional): Nombre maximum d'activités à récupérer
            
        Returns:
            list: Liste des activités correspondantes
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM activities"
            params = []
            
            # Construction de la clause WHERE en fonction des paramètres
            where_clauses = []
            
            if start_time is not None:
                where_clauses.append("timestamp >= ?")
                params.append(start_time)
            
            if end_time is not None:
                where_clauses.append("timestamp <= ?")
                params.append(end_time)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Ajout du tri et de la limite
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = cursor.fetchall()
            
            # Conversion des résultats en liste de dictionnaires
            activities = []
            for result in results:
                activity = dict(result)
                
                # Décodage des métadonnées si présentes
                if activity.get('metadata'):
                    activity['metadata'] = json.loads(activity['metadata'])
                
                activities.append(activity)
            
            return activities
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des activités: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_statistics(self, period='day'):
        """
        Récupère des statistiques sur les activités détectées pour une période donnée.
        
        Args:
            period (str): Période ('day', 'week', 'month', 'year')
            
        Returns:
            dict: Statistiques calculées
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Détermination de la date de début en fonction de la période
            now = datetime.now()
            
            if period == 'day':
                start_time = int(datetime(now.year, now.month, now.day).timestamp())
            elif period == 'week':
                # Début de la semaine (lundi)
                start_time = int((now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0).timestamp())
            elif period == 'month':
                start_time = int(datetime(now.year, now.month, 1).timestamp())
            elif period == 'year':
                start_time = int(datetime(now.year, 1, 1).timestamp())
            else:
                # Par défaut: dernières 24 heures
                start_time = int((now - timedelta(days=1)).timestamp())
            
            # Récupération du nombre d'activités par type
            cursor.execute('''
                SELECT activity, COUNT(*) as count
                FROM activities
                WHERE timestamp >= ?
                GROUP BY activity
                ORDER BY count DESC
            ''', (start_time,))
            
            activity_counts = cursor.fetchall()
            
            # Récupération de la durée totale par activité
            # Pour cela, nous devons analyser les timestamps consécutifs
            cursor.execute('''
                SELECT id, timestamp, activity
                FROM activities
                WHERE timestamp >= ?
                ORDER BY timestamp
            ''', (start_time,))
            
            activities_timeline = cursor.fetchall()
            
            # Calcul des durées par activité
            activity_durations = {}
            prev_timestamp = None
            prev_activity = None
            
            for activity_record in activities_timeline:
                current_timestamp = activity_record['timestamp']
                current_activity = activity_record['activity']
                
                if prev_timestamp is not None and prev_activity is not None:
                    # Durée en secondes entre les deux détections
                    duration = current_timestamp - prev_timestamp
                    
                    # Mise à jour de la durée cumulée pour cette activité
                    if prev_activity in activity_durations:
                        activity_durations[prev_activity] += duration
                    else:
                        activity_durations[prev_activity] = duration
                
                prev_timestamp = current_timestamp
                prev_activity = current_activity
            
            # Si la dernière activité est toujours en cours, lui attribuer la durée jusqu'à maintenant
            if prev_activity and prev_timestamp:
                current_time = int(time.time())
                duration = current_time - prev_timestamp
                
                if prev_activity in activity_durations:
                    activity_durations[prev_activity] += duration
                else:
                    activity_durations[prev_activity] = duration
            
            # Compilation des statistiques
            statistics = {
                'period': period,
                'start_time': start_time,
                'end_time': int(time.time()),
                'activity_counts': {},
                'activity_durations': {},
                'most_frequent_activity': None,
                'longest_activity': None
            }
            
            # Conversion des résultats en dictionnaires
            for item in activity_counts:
                activity = item['activity']
                count = item['count']
                statistics['activity_counts'][activity] = count
                
                # Mise à jour de l'activité la plus fréquente
                if statistics['most_frequent_activity'] is None or count > statistics['activity_counts'].get(statistics['most_frequent_activity'], 0):
                    statistics['most_frequent_activity'] = activity
            
            # Conversion des durées en minutes et mise à jour de l'activité la plus longue
            for activity, duration in activity_durations.items():
                # Conversion en minutes
                duration_minutes = duration / 60
                statistics['activity_durations'][activity] = round(duration_minutes, 1)
                
                # Mise à jour de l'activité la plus longue
                if statistics['longest_activity'] is None or duration > activity_durations.get(statistics['longest_activity'], 0):
                    statistics['longest_activity'] = activity
            
            return statistics
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {'error': str(e)}
        finally:
            if conn:
                conn.close()
