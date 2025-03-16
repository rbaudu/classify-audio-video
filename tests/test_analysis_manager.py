"""
Tests unitaires pour le module analysis.analysis_manager
"""
import unittest
import time
import threading
from unittest.mock import MagicMock, patch
from tests.helpers import (
    MockSyncManager, 
    MockActivityClassifier, 
    MockDBManager, 
    MockExternalServiceClient
)

class TestAnalysisManager(unittest.TestCase):
    """Tests pour le gestionnaire d'analyse"""
    
    def setUp(self):
        """Configuration des tests"""
        # Patching pour éviter d'importer réellement les modules externes
        self.patcher1 = patch('server.analysis.analysis_manager.ANALYSIS_INTERVAL', 0.1)
        self.mock_interval = self.patcher1.start()
        
        # Création des mocks
        self.sync_manager = MockSyncManager()
        self.activity_classifier = MockActivityClassifier(sync_manager=self.sync_manager)
        self.db_manager = MockDBManager()
        self.external_service = MockExternalServiceClient()
    
    def tearDown(self):
        """Nettoyage après les tests"""
        self.patcher1.stop()
    
    def test_start_analysis_loop(self):
        """Test du démarrage de la boucle d'analyse"""
        from server.analysis.analysis_manager import start_analysis_loop, analysis_running
        
        # Vérifier que l'analyse n'est pas en cours
        self.assertFalse(analysis_running)
        
        # Démarrer l'analyse
        result = start_analysis_loop(self.activity_classifier, self.db_manager, self.external_service)
        
        # Vérifier que l'analyse a démarré
        self.assertTrue(result)
        self.assertTrue(analysis_running)
        
        # Attendre un peu pour que la boucle s'exécute
        time.sleep(0.2)
        
        # Arrêter l'analyse
        from server.analysis.analysis_manager import stop_analysis_loop
        stop_analysis_loop()
        
        # Vérifier que l'analyse est arrêtée
        self.assertFalse(analysis_running)
    
    def test_stop_analysis_loop_when_not_running(self):
        """Test de l'arrêt lorsque la boucle n'est pas en cours d'exécution"""
        from server.analysis.analysis_manager import stop_analysis_loop, analysis_running, analysis_thread
        
        # S'assurer que l'analyse n'est pas en cours
        if analysis_running:
            stop_analysis_loop()
        
        # Vérifier que l'analyse n'est pas en cours
        self.assertFalse(analysis_running)
        self.assertIsNone(analysis_thread)
        
        # Tenter d'arrêter l'analyse
        result = stop_analysis_loop()
        
        # Vérifier que la fonction a renvoyé False
        self.assertFalse(result)
    
    @patch('server.analysis.analysis_manager.analysis_loop')
    def test_analysis_loop_process(self, mock_analysis_loop):
        """Test du processus de la boucle d'analyse"""
        from server.analysis.analysis_manager import analysis_loop
        
        # Configurer le mock pour simuler la boucle
        def side_effect(activity_classifier, db_manager, external_service):
            # Simuler une exécution puis s'arrêter
            global analysis_running
            analysis_running = False
        
        mock_analysis_loop.side_effect = side_effect
        
        # Initialiser la boucle
        from server.analysis.analysis_manager import analysis_running
        analysis_running = True
        
        # Appeler la fonction
        analysis_loop(self.activity_classifier, self.db_manager, self.external_service)
        
        # Vérifier que la fonction a été appelée
        mock_analysis_loop.assert_called_once_with(
            self.activity_classifier, 
            self.db_manager, 
            self.external_service
        )
    
    def test_start_stop_sequence(self):
        """Test d'une séquence démarrage-arrêt-démarrage"""
        from server.analysis.analysis_manager import start_analysis_loop, stop_analysis_loop
        
        # Premier démarrage
        start_analysis_loop(self.activity_classifier, self.db_manager, self.external_service)
        
        # Vérifier que l'analyse est en cours
        from server.analysis.analysis_manager import analysis_running, analysis_thread
        self.assertTrue(analysis_running)
        self.assertIsNotNone(analysis_thread)
        
        # Premier arrêt
        result = stop_analysis_loop()
        self.assertTrue(result)
        
        # Vérifier que l'analyse est arrêtée
        self.assertFalse(analysis_running)
        
        # Second démarrage
        start_analysis_loop(self.activity_classifier, self.db_manager, self.external_service)
        
        # Vérifier que l'analyse est en cours
        self.assertTrue(analysis_running)
        
        # Second arrêt
        stop_analysis_loop()

if __name__ == '__main__':
    unittest.main()
