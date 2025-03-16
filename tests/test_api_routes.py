"""
Tests unitaires pour le module routes.api_routes
"""
import unittest
import json
import time
import os
from unittest.mock import patch, MagicMock
from flask import Flask
from tests.helpers import (
    MockSyncManager, 
    MockActivityClassifier, 
    MockDBManager, 
    create_temp_directory,
    cleanup_temp_directory
)

class TestAPIRoutes(unittest.TestCase):
    """Tests pour les routes API"""
    
    def setUp(self):
        """Configuration des tests"""
        # Créer une application Flask de test
        self.app = Flask(__name__)
        self.app.testing = True
        self.client = self.app.test_client()
        
        # Créer les mocks
        self.sync_manager = MockSyncManager()
        self.activity_classifier = MockActivityClassifier(sync_manager=self.sync_manager)
        self.db_manager = MockDBManager()
        
        # Créer un répertoire d'analyse temporaire
        self.temp_dir = create_temp_directory()
        
        # Enregistrer les routes API
        from server.routes.api_routes import register_api_routes
        register_api_routes(
            self.app, 
            self.sync_manager, 
            self.activity_classifier, 
            self.db_manager, 
            self.temp_dir
        )
        
        # Créer des données de test
        self.db_manager.add_activity(
            'reading',
            0.85,
            int(time.time()) - 60,
            json.dumps({
                'video': {'features': {'movement': 0.2}},
                'audio': {'features': {'volume': 0.3}}
            })
        )
        
        # Ajouter une analyse vidéo de test
        self.test_analysis_id = f"test_analysis_{int(time.time())}"
        self.db_manager.save_video_analysis(
            self.test_analysis_id,
            "Test Video",
            [
                {
                    'activity': 'reading',
                    'confidence': 0.85,
                    'timestamp': 0,
                    'formatted_time': '00:00',
                    'features': {
                        'video': {'movement': 0.2},
                        'audio': {'volume': 0.3}
                    }
                },
                {
                    'activity': 'talking',
                    'confidence': 0.75,
                    'timestamp': 10,
                    'formatted_time': '00:10',
                    'features': {
                        'video': {'movement': 0.5},
                        'audio': {'volume': 0.7}
                    }
                }
            ]
        )
    
    def tearDown(self):
        """Nettoyage après les tests"""
        cleanup_temp_directory(self.temp_dir)
    
    def test_get_current_activity(self):
        """Test de l'API pour récupérer l'activité actuelle"""
        response = self.client.get('/api/current-activity')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('activity', data)
        self.assertIn('confidence', data)
        self.assertIn('timestamp', data)
        self.assertIn('features', data)
    
    def test_head_current_activity(self):
        """Test de l'API HEAD pour vérifier la connexion"""
        response = self.client.head('/api/current-activity')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'')
    
    def test_get_activities(self):
        """Test de l'API pour récupérer l'historique des activités"""
        response = self.client.get('/api/activities')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        first_activity = data[0]
        self.assertIn('activity', first_activity)
        self.assertIn('confidence', first_activity)
        self.assertIn('timestamp', first_activity)
        self.assertIn('metadata', first_activity)
    
    def test_get_activities_with_params(self):
        """Test de l'API pour récupérer l'historique avec des paramètres"""
        # Ajouter quelques activités de test avec des timestamps différents
        now = int(time.time())
        
        self.db_manager.add_activity('reading', 0.85, now - 3600, '{}')  # il y a 1 heure
        self.db_manager.add_activity('talking', 0.75, now - 1800, '{}')  # il y a 30 minutes
        self.db_manager.add_activity('eating', 0.65, now - 900, '{}')    # il y a 15 minutes
        
        # Test avec une plage de temps
        response = self.client.get(f'/api/activities?start={now-2000}&end={now-800}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Devrait retourner 'eating' uniquement
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['activity'], 'eating')
        
        # Test avec une limite
        response = self.client.get('/api/activities?limit=2')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Devrait retourner les 2 dernières activités
        self.assertEqual(len(data), 2)
    
    def test_get_statistics(self):
        """Test de l'API pour récupérer les statistiques"""
        response = self.client.get('/api/statistics')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('activity_counts', data)
        self.assertIn('activity_durations', data)
        self.assertIn('hourly_distribution', data)
        self.assertIn('trends', data)
        self.assertIn('total_classifications', data)
        self.assertIn('period', data)
    
    def test_classify(self):
        """Test de l'API pour classifier une activité"""
        # Test avec des caractéristiques fournies
        features = {
            'video': {'movement': 0.2},
            'audio': {'volume': 0.3}
        }
        
        response = self.client.post(
            '/api/classify',
            data=json.dumps(features),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('activity', data)
        self.assertIn('confidence', data)
        self.assertIn('confidence_scores', data)
        self.assertIn('timestamp', data)
        
        # Test sans caractéristiques (analyse en direct)
        response = self.client.post('/api/classify')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('activity', data)
        self.assertIn('confidence', data)
    
    def test_export_analysis_json(self):
        """Test de l'API pour exporter une analyse en JSON"""
        response = self.client.get(f'/api/export-analysis/{self.test_analysis_id}/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn(f'attachment; filename={self.test_analysis_id}.json', response.headers['Content-Disposition'])
        
        data = json.loads(response.data)
        
        self.assertIn('source_name', data)
        self.assertIn('timestamp', data)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 2)
    
    def test_export_analysis_csv(self):
        """Test de l'API pour exporter une analyse en CSV"""
        response = self.client.get(f'/api/export-analysis/{self.test_analysis_id}/csv')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/csv')
        self.assertIn(f'attachment; filename={self.test_analysis_id}.csv', response.headers['Content-Disposition'])
        
        # Vérifier les entêtes CSV
        csv_content = response.data.decode('utf-8')
        first_line = csv_content.split('\n')[0]
        
        self.assertIn('timestamp', first_line)
        self.assertIn('formatted_time', first_line)
        self.assertIn('activity', first_line)
        self.assertIn('confidence', first_line)
    
    def test_export_analysis_invalid_format(self):
        """Test de l'API avec un format d'export invalide"""
        response = self.client.get(f'/api/export-analysis/{self.test_analysis_id}/invalid')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('format d\'export non supporté', data['error'])
    
    def test_export_analysis_not_found(self):
        """Test de l'API avec une analyse non trouvée"""
        response = self.client.get('/api/export-analysis/invalid_id/json')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('Analyse non trouvée', data['error'])
    
    # Tests pour les autres points d'API
    def test_media_routes(self):
        """Test des routes API concernant les médias"""
        # Test pour la liste des sources média
        response = self.client.get('/api/media-sources')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIsInstance(data, list)
        self.assertIn('Source 1', data)
        
        # Test pour les propriétés d'un média
        response = self.client.get('/api/media-properties/Test Video')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('duration', data)
        self.assertIn('status', data)
        
        # Test pour le contrôle média
        response = self.client.post(
            '/api/control-media',
            data=json.dumps({
                'sourceName': 'Test Video',
                'action': 'play'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])

if __name__ == '__main__':
    unittest.main()
