"""
Tests unitaires pour le module analysis.video_analysis
"""
import unittest
import os
import time
import tempfile
import json
from unittest.mock import patch, MagicMock
from tests.helpers import (
    MockSyncManager,
    MockActivityClassifier,
    MockDBManager,
    create_temp_directory,
    cleanup_temp_directory
)

class TestVideoAnalysis(unittest.TestCase):
    """Tests pour l'analyse vidéo"""
    
    def setUp(self):
        """Configuration des tests"""
        self.temp_dir = create_temp_directory()
        self.sync_manager = MockSyncManager()
        self.activity_classifier = MockActivityClassifier(sync_manager=self.sync_manager)
        self.db_manager = MockDBManager()
        self.analysis_tasks = {}
        self.analysis_id = f"test_analysis_{int(time.time())}"
        self.source_name = "Test Video"
    
    def tearDown(self):
        """Nettoyage après les tests"""
        cleanup_temp_directory(self.temp_dir)
    
    def test_analyze_video_task(self):
        """Test de la tâche d'analyse vidéo"""
        from server.analysis.video_analysis import analyze_video_task
        
        # Exécuter la tâche d'analyse
        analyze_video_task(
            self.analysis_id,
            self.source_name,
            self.sync_manager,
            self.activity_classifier,
            self.db_manager,
            self.temp_dir,
            self.analysis_tasks
        )
        
        # Vérifier que l'analyse a été ajoutée aux tâches
        self.assertIn(self.analysis_id, self.analysis_tasks)
        
        # Vérifier l'état final de l'analyse
        task = self.analysis_tasks[self.analysis_id]
        self.assertEqual(task['status'], 'completed')
        self.assertIn('end_time', task)
        self.assertIn('total_samples', task)
        self.assertIn('results', task)
        self.assertGreater(len(task['results']), 0)
        
        # Vérifier que l'analyse a été sauvegardée dans la base de données
        self.assertIn(self.analysis_id, self.db_manager.video_analyses)
    
    def test_analyze_video_task_without_save(self):
        """Test de la tâche d'analyse vidéo sans sauvegarde"""
        from server.analysis.video_analysis import analyze_video_task
        
        # Exécuter la tâche d'analyse sans sauvegarde
        analyze_video_task(
            self.analysis_id,
            self.source_name,
            self.sync_manager,
            self.activity_classifier,
            self.db_manager,
            self.temp_dir,
            self.analysis_tasks,
            save_analysis=False
        )
        
        # Vérifier que l'analyse a été ajoutée aux tâches
        self.assertIn(self.analysis_id, self.analysis_tasks)
        
        # Vérifier l'état final de l'analyse
        task = self.analysis_tasks[self.analysis_id]
        self.assertEqual(task['status'], 'completed')
        
        # Vérifier que l'analyse n'a PAS été sauvegardée dans la base de données
        self.assertNotIn(self.analysis_id, self.db_manager.video_analyses)
    
    def test_analyze_video_task_with_timeline(self):
        """Test de la tâche d'analyse vidéo avec génération de timeline"""
        from server.analysis.video_analysis import analyze_video_task
        
        # Exécuter la tâche d'analyse avec génération de timeline
        analyze_video_task(
            self.analysis_id,
            self.source_name,
            self.sync_manager,
            self.activity_classifier,
            self.db_manager,
            self.temp_dir,
            self.analysis_tasks,
            generate_timeline=True
        )
        
        # Vérifier que la timeline a été générée
        timeline_path = os.path.join(self.temp_dir, f"{self.analysis_id}_timeline.json")
        self.assertTrue(os.path.exists(timeline_path))
        
        # Vérifier le contenu de la timeline
        with open(timeline_path, 'r') as f:
            timeline_data = json.load(f)
        
        self.assertEqual(timeline_data['analysis_id'], self.analysis_id)
        self.assertIn('timestamps', timeline_data)
        self.assertIn('activities', timeline_data)
        self.assertIn('formatted_times', timeline_data)
        self.assertIn('confidences', timeline_data)
    
    def test_invalid_source_name(self):
        """Test avec un nom de source invalide"""
        from server.analysis.video_analysis import analyze_video_task
        
        # Exécuter la tâche d'analyse avec un nom de source invalide
        analyze_video_task(
            self.analysis_id,
            "Invalid Source",
            self.sync_manager,
            self.activity_classifier,
            self.db_manager,
            self.temp_dir,
            self.analysis_tasks
        )
        
        # Vérifier que l'analyse a échoué
        task = self.analysis_tasks[self.analysis_id]
        self.assertEqual(task['status'], 'error')
        self.assertIn('error', task)
    
    def test_generate_timeline_visualization(self):
        """Test de la génération de timeline"""
        from server.analysis.video_analysis import generate_timeline_visualization
        
        # Créer des résultats de test
        results = [
            {
                'activity': 'reading',
                'confidence': 0.85,
                'timestamp': 0,
                'formatted_time': '00:00'
            },
            {
                'activity': 'talking',
                'confidence': 0.75,
                'timestamp': 10,
                'formatted_time': '00:10'
            },
            {
                'activity': 'reading',
                'confidence': 0.90,
                'timestamp': 20,
                'formatted_time': '00:20'
            }
        ]
        
        # Générer la timeline
        generate_timeline_visualization(self.analysis_id, results, self.temp_dir)
        
        # Vérifier que la timeline a été générée
        timeline_path = os.path.join(self.temp_dir, f"{self.analysis_id}_timeline.json")
        self.assertTrue(os.path.exists(timeline_path))
        
        # Vérifier le contenu de la timeline
        with open(timeline_path, 'r') as f:
            timeline_data = json.load(f)
        
        self.assertEqual(timeline_data['analysis_id'], self.analysis_id)
        self.assertEqual(len(timeline_data['timestamps']), 3)
        self.assertEqual(len(timeline_data['activities']), 3)
        self.assertEqual(len(timeline_data['formatted_times']), 3)
        self.assertEqual(len(timeline_data['confidences']), 3)
        
        # Vérifier les valeurs
        self.assertEqual(timeline_data['timestamps'], [0, 10, 20])
        self.assertEqual(timeline_data['activities'], ['reading', 'talking', 'reading'])
        self.assertEqual(timeline_data['formatted_times'], ['00:00', '00:10', '00:20'])
        self.assertEqual(timeline_data['confidences'], [0.85, 0.75, 0.90])

if __name__ == '__main__':
    unittest.main()
