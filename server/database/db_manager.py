import os
import json
import sqlite3
import logging
import time
from datetime import datetime

# Import de la configuration
from ..config import DB_PATH

class DBManager:
    """
    Gestionnaire de base de données SQLite pour stocker l'historique des activités
    et les analyses de vidéo
    """
    
    def __init__(self, db_path=None):
        """
        Initialise le gestionnaire de base de données
        
        Args:
            db_path (str, optional): Chemin vers le fichier de base de données.
                                     Si None, utilise DB_PATH de la configuration.
        """
        self.logger = logging.getLogger(__name__)
        
        # Utiliser le chemin par défaut si non spécifié
        if not db_path:
            db_path = DB_PATH
        
        # Créer le répertoire parent si nécessaire
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.initialize_db()
    
    def get_connection(self):
        """
        Crée et retourne une connexion à la base de données
        
        Returns:
            sqlite3.Connection: Connexion SQLite
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        return conn
    
    def initialize_db(self):
        """
        Initialise la base de données en créant les tables si elles n'existent pas
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Création de la table des activités
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity TEXT NOT NULL,
                confidence REAL,
                timestamp INTEGER NOT NULL,
                metadata TEXT
            )
            ''')
            
            # Création de la table des analyses vidéo
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_analyses (
                id TEXT PRIMARY KEY,
                source_name TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                results TEXT NOT NULL
            )
            ''')
            
            conn.commit()
            self.logger.info("Base de données initialisée avec succès")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
    
    def add_activity(self, activity, confidence, timestamp, metadata=None):
        """
        Ajoute une nouvelle activité à la base de données
        
        Args:
            activity (str): Type d'activité détectée
            confidence (float): Niveau de confiance (0-1)
            timestamp (int): Horodatage Unix en secondes
            metadata (str, optional): Métadonnées supplémentaires au format JSON. Défaut à None.
        
        Returns:
            int: ID de l'activité insérée
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO activities (activity, confidence, timestamp, metadata)
            VALUES (?, ?, ?, ?)
            ''', (activity, confidence, timestamp, metadata))
            
            conn.commit()
            
            # Récupérer l'ID généré
            activity_id = cursor.lastrowid
            
            self.logger.info(f"Activité enregistrée avec succès (ID: {activity_id})")
            return activity_id
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout d'une activité: {str(e)}")
            return None
    
    def get_latest_activity(self):
        """
        Récupère la dernière activité enregistrée
        
        Returns:
            dict: Informations sur la dernière activité ou None si aucune n'est trouvée
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, activity, confidence, timestamp, metadata
            FROM activities
            ORDER BY timestamp DESC
            LIMIT 1
            ''')
            
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            else:
                return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de la dernière activité: {str(e)}")
            return None
    
    def get_activities(self, start_time=None, end_time=None, limit=100, offset=0):
        """
        Récupère les activités dans une plage de temps donnée, avec pagination
        
        Args:
            start_time (int, optional): Horodatage de début. Défaut à None (pas de limite).
            end_time (int, optional): Horodatage de fin. Défaut à None (pas de limite).
            limit (int, optional): Nombre maximum d'activités à récupérer. Défaut à 100.
            offset (int, optional): Décalage pour la pagination. Défaut à 0.
        
        Returns:
            list: Liste des activités correspondant aux critères
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Construire la requête SQL avec les filtres de temps
            query = '''
            SELECT id, activity, confidence, timestamp, metadata
            FROM activities
            WHERE 1=1
            '''
            params = []
            
            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            
            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)
            
            # Ajouter l'ordre et la pagination
            query += '''
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            '''
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des activités: {str(e)}")
            return []
    
    def get_activity_count(self, start_time=None, end_time=None):
        """
        Compte le nombre d'activités dans une plage de temps donnée
        
        Args:
            start_time (int, optional): Horodatage de début. Défaut à None (pas de limite).
            end_time (int, optional): Horodatage de fin. Défaut à None (pas de limite).
        
        Returns:
            int: Nombre d'activités correspondant aux critères
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Construire la requête SQL avec les filtres de temps
            query = 'SELECT COUNT(*) FROM activities WHERE 1=1'
            params = []
            
            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            
            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)
            
            cursor.execute(query, params)
            
            return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Erreur lors du comptage des activités: {str(e)}")
            return 0
    
    def get_activity_stats(self, start_time=None, end_time=None):
        """
        Calcule des statistiques sur les activités dans une plage de temps donnée
        
        Args:
            start_time (int, optional): Horodatage de début. Défaut à None (pas de limite).
            end_time (int, optional): Horodatage de fin. Défaut à None (pas de limite).
        
        Returns:
            dict: Statistiques d'activité
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Compter les activités par type
            query = '''
            SELECT activity, COUNT(*) as count
            FROM activities
            WHERE 1=1
            '''
            params = []
            
            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            
            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)
            
            query += ' GROUP BY activity'
            
            cursor.execute(query, params)
            activity_counts = {row['activity']: row['count'] for row in cursor.fetchall()}
            
            # Calculer les durées totales (estimation à partir des intervalles entre activités)
            # Note: Ce calcul est approximatif car il dépend des intervalles d'enregistrement
            query = '''
            SELECT id, activity, timestamp
            FROM activities
            WHERE 1=1
            '''
            params = []
            
            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            
            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)
            
            query += ' ORDER BY timestamp'
            
            cursor.execute(query, params)
            activities = cursor.fetchall()
            
            activity_durations = {}
            
            for i in range(len(activities) - 1):
                current = activities[i]
                next_act = activities[i + 1]
                
                duration = next_act['timestamp'] - current['timestamp']
                
                if current['activity'] not in activity_durations:
                    activity_durations[current['activity']] = 0
                
                activity_durations[current['activity']] += duration
            
            return {
                'activity_counts': activity_counts,
                'activity_durations': activity_durations,
                'total_count': sum(activity_counts.values())
            }
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {
                'activity_counts': {},
                'activity_durations': {},
                'total_count': 0
            }
    
    def delete_activities(self, start_time=None, end_time=None):
        """
        Supprime les activités dans une plage de temps donnée
        
        Args:
            start_time (int, optional): Horodatage de début. Défaut à None (pas de limite).
            end_time (int, optional): Horodatage de fin. Défaut à None (pas de limite).
        
        Returns:
            int: Nombre d'activités supprimées
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Construire la requête SQL avec les filtres de temps
            query = 'DELETE FROM activities WHERE 1=1'
            params = []
            
            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            
            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)
            
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            
            conn.commit()
            
            self.logger.info(f"{affected_rows} activités supprimées")
            return affected_rows
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression des activités: {str(e)}")
            return 0
    
    # Méthodes pour gérer les analyses vidéo
    
    def save_video_analysis(self, analysis_id, source_name, results):
        """
        Sauvegarde une analyse vidéo complète
        
        Args:
            analysis_id (str): Identifiant unique de l'analyse
            source_name (str): Nom de la source vidéo
            results (list): Résultats de l'analyse (liste de dictionnaires)
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Convertir les résultats en JSON
            results_json = json.dumps(results)
            
            # Timestamp actuel
            timestamp = int(time.time())
            
            cursor.execute('''
            INSERT INTO video_analyses (id, source_name, timestamp, results)
            VALUES (?, ?, ?, ?)
            ''', (analysis_id, source_name, timestamp, results_json))
            
            conn.commit()
            
            self.logger.info(f"Analyse vidéo enregistrée avec succès (ID: {analysis_id})")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement de l'analyse vidéo: {str(e)}")
            return False
    
    def get_video_analysis(self, analysis_id):
        """
        Récupère une analyse vidéo par son ID
        
        Args:
            analysis_id (str): Identifiant de l'analyse
        
        Returns:
            dict: Données de l'analyse ou None si non trouvée
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, source_name, timestamp, results
            FROM video_analyses
            WHERE id = ?
            ''', (analysis_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convertir le JSON en liste
            row_dict = dict(row)
            row_dict['results'] = json.loads(row_dict['results'])
            
            return row_dict
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de l'analyse vidéo: {str(e)}")
            return None
    
    def get_all_video_analyses(self, limit=100, offset=0):
        """
        Récupère toutes les analyses vidéo avec pagination
        
        Args:
            limit (int, optional): Nombre maximum d'analyses à récupérer. Défaut à 100.
            offset (int, optional): Décalage pour la pagination. Défaut à 0.
        
        Returns:
            list: Liste des analyses vidéo
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, source_name, timestamp
            FROM video_analyses
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            # Ne pas inclure les résultats complets pour des raisons de performance
            analyses = [dict(row) for row in cursor.fetchall()]
            
            return analyses
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des analyses vidéo: {str(e)}")
            return []
    
    def get_video_analyses_by_source(self, source_name, limit=100, offset=0):
        """
        Récupère les analyses vidéo pour une source donnée
        
        Args:
            source_name (str): Nom de la source vidéo
            limit (int, optional): Nombre maximum d'analyses à récupérer. Défaut à 100.
            offset (int, optional): Décalage pour la pagination. Défaut à 0.
        
        Returns:
            list: Liste des analyses vidéo
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, source_name, timestamp
            FROM video_analyses
            WHERE source_name = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            ''', (source_name, limit, offset))
            
            # Ne pas inclure les résultats complets pour des raisons de performance
            analyses = [dict(row) for row in cursor.fetchall()]
            
            return analyses
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des analyses vidéo: {str(e)}")
            return []
    
    def delete_video_analysis(self, analysis_id):
        """
        Supprime une analyse vidéo
        
        Args:
            analysis_id (str): Identifiant de l'analyse
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            DELETE FROM video_analyses
            WHERE id = ?
            ''', (analysis_id,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            
            if affected_rows > 0:
                self.logger.info(f"Analyse vidéo supprimée avec succès (ID: {analysis_id})")
                return True
            else:
                self.logger.warning(f"Aucune analyse vidéo trouvée avec l'ID: {analysis_id}")
                return False
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression de l'analyse vidéo: {str(e)}")
            return False
    
    def get_video_analysis_count(self):
        """
        Compte le nombre total d'analyses vidéo
        
        Returns:
            int: Nombre d'analyses vidéo
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM video_analyses')
            
            return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Erreur lors du comptage des analyses vidéo: {str(e)}")
            return 0
    
    # Méthodes utilitaires
    
    def vacuum_database(self):
        """
        Réorganise la base de données pour optimiser l'espace disque
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            conn = self.get_connection()
            conn.execute('VACUUM')
            
            self.logger.info("Base de données réorganisée avec succès")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la réorganisation de la base de données: {str(e)}")
            return False
