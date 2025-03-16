"""
Tests unitaires pour le module routes.web_routes
"""
import unittest
import json
import time
from unittest.mock import patch, MagicMock
from flask import Flask, template_rendered
from contextlib import contextmanager
from tests.helpers import (
    MockSyncManager, 
    MockActivityClassifier, 
    MockDBManager
)

@contextmanager
def captured_templates(app):
    """Contexte pour capturer les templates rendus"""
    recorded = []
    
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

class TestWebRoutes(unittest.TestCase):
    """Tests pour les routes web"""
    
    def setUp(self):
        """Configuration des tests"""
        # Créer une application Flask de test
        self.app = Flask(__name__, 
                         template_folder='../web/templates')
        self.app.testing = True
        self.client = self.app.test_client()
        
        # Définir les classes mock globales comme attributs de app
        # (nécessaire parce que le module web_routes les importera)
        self.db_manager = MockDBManager()
        self.analysis_tasks = {}
        
        # Patcher l'import des modules dans web_routes
        self.patcher1 = patch('server.routes.web_routes.ACTIVITY_ICONS', {'reading': 'book'})
        self.patcher2 = patch('server.routes.web_routes.ACTIVITY_COLORS', {'reading': '#ff0000'})
        
        self.mock_icons = self.patcher1.start()
        self.mock_colors = self.patcher2.start()
        
        # Enregistrer les routes web
        from server.routes.web_routes import register_web_routes
        register_web_routes(self.app)
        
        # Créer des données de test
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
        
        # Injecter DBManager dans l'application
        with patch('server.routes.web_routes.DBManager', return_value=self.db_manager):
            pass
        
        # Injecter analysis_tasks dans l'application
        with patch('server.routes.web_routes.analysis_tasks', self.analysis_tasks):
            self.analysis_tasks[f"in_progress_{int(time.time())}"] = {
                'status': 'running',
                'progress': 50.0,
                'source_name': 'Test Video In Progress'
            }
    
    def tearDown(self):
        """Nettoyage après les tests"""
        self.patcher1.stop()
        self.patcher2.stop()
    
    def test_index_route(self):
        """Test de la route d'accueil"""
        with captured_templates(self.app) as templates:
            response = self.client.get('/')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(templates), 1)
            template, context = templates[0]
            
            self.assertEqual(template.name, 'index.html')
    
    def test_dashboard_route(self):
        """Test de la route du tableau de bord"""
        with captured_templates(self.app) as templates:
            response = self.client.get('/dashboard')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(templates), 1)
            template, context = templates[0]
            
            self.assertEqual(template.name, 'dashboard.html')
    
    def test_statistics_route(self):
        """Test de la route des statistiques"""
        with captured_templates(self.app) as templates:
            response = self.client.get('/statistics')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(templates), 1)
            template, context = templates[0]
            
            self.assertEqual(template.name, 'statistics.html')
    
    def test_history_route(self):
        """Test de la route de l'historique"""
        with captured_templates(self.app) as templates:
            response = self.client.get('/history')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(templates), 1)
            template, context = templates[0]
            
            self.assertEqual(template.name, 'history.html')
    
    def test_model_testing_route(self):
        """Test de la route de test du modèle"""
        with captured_templates(self.app) as templates:
            response = self.client.get('/model_testing')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(templates), 1)
            template, context = templates[0]
            
            self.assertEqual(template.name, 'model_testing.html')
    
    def test_analysis_results_route(self):
        """Test de la route des résultats d'analyse"""
        # Forcer l'utilisation de notre mock DBManager
        with patch('server.database.db_manager.DBManager', return_value=self.db_manager):
            with patch('server.routes.web_routes.DBManager', return_value=self.db_manager):
                with captured_templates(self.app) as templates:
                    response = self.client.get(f'/analysis-results/{self.test_analysis_id}')
                    
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(len(templates), 1)
                    template, context = templates[0]
                    
                    self.assertEqual(template.name, 'analysis_results.html')
                    self.assertEqual(context['analysis_id'], self.test_analysis_id)
                    self.assertEqual(context['source_name'], 'Test Video')
                    self.assertEqual(len(context['results']), 2)
                    self.assertEqual(context['activity_icons'], {'reading': 'book'})
                    self.assertEqual(context['activity_colors'], {'reading': '#ff0000'})
    
    def test_analysis_in_progress_route(self):
        """Test de la route pour une analyse en cours"""
        in_progress_id = list(self.analysis_tasks.keys())[0]
        
        # Forcer l'utilisation de notre mock
        with patch('server.routes.web_routes.analysis_tasks', self.analysis_tasks):
            with captured_templates(self.app) as templates:
                response = self.client.get(f'/analysis-results/{in_progress_id}')
                
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(templates), 1)
                template, context = templates[0]
                
                self.assertEqual(template.name, 'analysis_in_progress.html')
                self.assertEqual(context['analysis_id'], in_progress_id)
                self.assertEqual(context['progress'], 50.0)
    
    def test_analysis_not_found_route(self):
        """Test de la route pour une analyse non trouvée"""
        # Forcer l'utilisation de notre mock
        with patch('server.database.db_manager.DBManager', return_value=self.db_manager):
            with patch('server.routes.web_routes.DBManager', return_value=self.db_manager):
                with captured_templates(self.app) as templates:
                    response = self.client.get('/analysis-results/non_existent')
                    
                    self.assertEqual(response.status_code, 404)
                    self.assertEqual(len(templates), 1)
                    template, context = templates[0]
                    
                    self.assertEqual(template.name, 'error.html')
                    self.assertIn('message', context)
                    self.assertEqual(context['message'], 'Analyse non trouvée')

if __name__ == '__main__':
    unittest.main()
