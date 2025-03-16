#!/usr/bin/env python
"""
Script pour exécuter les tests unitaires
"""
import unittest
import sys
import os

# Ajouter le répertoire parent au chemin pour permettre l'importation des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_all_tests():
    """Exécute tous les tests unitaires"""
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_specific_test(test_name):
    """Exécute un test spécifique"""
    if not test_name.startswith('test_'):
        test_name = f'test_{test_name}'
    if not test_name.endswith('.py'):
        test_name = f'{test_name}.py'
    
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    
    try:
        tests = loader.discover(start_dir, pattern=test_name)
        if tests.countTestCases() == 0:
            print(f"Aucun test trouvé avec le motif: {test_name}")
            return False
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(tests)
        
        return result.wasSuccessful()
    except ImportError:
        print(f"Impossible d'importer le module de test: {test_name}")
        return False

def run_test_by_module(module_name):
    """Exécute les tests pour un module spécifique"""
    if module_name.endswith('.py'):
        module_name = module_name[:-3]
    
    test_pattern = f"test_{module_name}.py"
    
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    
    try:
        tests = loader.discover(start_dir, pattern=test_pattern)
        if tests.countTestCases() == 0:
            print(f"Aucun test trouvé pour le module: {module_name}")
            return False
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(tests)
        
        return result.wasSuccessful()
    except ImportError:
        print(f"Impossible d'importer les tests pour le module: {module_name}")
        return False

def print_available_tests():
    """Affiche la liste des tests disponibles"""
    start_dir = os.path.dirname(__file__)
    test_files = [f for f in os.listdir(start_dir) if f.startswith('test_') and f.endswith('.py')]
    
    if not test_files:
        print("Aucun test disponible.")
        return
    
    print("Tests disponibles:")
    for test_file in sorted(test_files):
        module_name = test_file[5:-3]  # Enlever 'test_' et '.py'
        print(f"  - {module_name}")

def print_usage():
    """Affiche l'aide d'utilisation"""
    print("Usage: python runner.py [options]")
    print("\nOptions:")
    print("  --all                   Exécuter tous les tests")
    print("  --test=NOM_TEST         Exécuter un test spécifique")
    print("  --module=NOM_MODULE     Exécuter les tests pour un module spécifique")
    print("  --list                  Afficher la liste des tests disponibles")
    print("  --help                  Afficher cette aide")
    print("\nExemples:")
    print("  python runner.py --all")
    print("  python runner.py --test=formatting")
    print("  python runner.py --module=video_analysis")
    print("  python runner.py --list")

if __name__ == '__main__':
    # Traiter les arguments de ligne de commande
    if len(sys.argv) == 1 or '--help' in sys.argv:
        print_usage()
        sys.exit(0)
    
    if '--list' in sys.argv:
        print_available_tests()
        sys.exit(0)
    
    if '--all' in sys.argv:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    
    for arg in sys.argv[1:]:
        if arg.startswith('--test='):
            test_name = arg[7:]
            success = run_specific_test(test_name)
            sys.exit(0 if success else 1)
        
        if arg.startswith('--module='):
            module_name = arg[9:]
            success = run_test_by_module(module_name)
            sys.exit(0 if success else 1)
    
    print("Option non reconnue.")
    print_usage()
    sys.exit(1)
