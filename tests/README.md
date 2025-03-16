# Tests Unitaires pour Classify Audio Video

Ce répertoire contient les tests unitaires pour les différents modules de l'application Classify Audio Video.

## Structure

```
tests/
├── __init__.py             # Initialisation du paquet de tests
├── README.md               # Ce fichier
├── helpers.py              # Classes mock et utilitaires pour les tests
├── runner.py               # Script pour lancer les tests
├── test_api_routes.py      # Tests pour les routes API
├── test_formatting.py      # Tests pour les utilitaires de formatage
├── test_analysis_manager.py # Tests pour le gestionnaire d'analyse
├── test_video_analysis.py  # Tests pour l'analyse vidéo
└── test_web_routes.py      # Tests pour les routes web
```

## Exécution des tests

Vous pouvez exécuter les tests de différentes manières :

### Utiliser le script runner.py

Ce script offre plusieurs options pour exécuter les tests :

```bash
# Afficher l'aide
python tests/runner.py --help

# Lister tous les tests disponibles
python tests/runner.py --list

# Exécuter tous les tests
python tests/runner.py --all

# Exécuter un test spécifique
python tests/runner.py --test=formatting

# Exécuter les tests pour un module spécifique
python tests/runner.py --module=video_analysis
```

### Utiliser unittest directement

Vous pouvez également utiliser le module unittest de Python directement :

```bash
# Exécuter tous les tests
python -m unittest discover tests

# Exécuter un test spécifique
python -m unittest tests.test_formatting

# Exécuter une classe de test spécifique
python -m unittest tests.test_api_routes.TestAPIRoutes

# Exécuter une méthode de test spécifique
python -m unittest tests.test_api_routes.TestAPIRoutes.test_get_current_activity
```

## Ajout de nouveaux tests

Pour ajouter de nouveaux tests :

1. Créez un nouveau fichier de test avec le préfixe `test_` (ex: `test_nouveau_module.py`)
2. Dans ce fichier, créez une classe qui hérite de `unittest.TestCase`
3. Ajoutez des méthodes de test avec le préfixe `test_`
4. Utilisez les assertions pour vérifier les comportements attendus
5. Ajoutez des méthodes `setUp` et `tearDown` si nécessaire pour initialiser et nettoyer l'environnement de test

Exemple :

```python
import unittest
from tests.helpers import MockDBManager  # Utilisez les mocks existants si approprié

class TestNouveauModule(unittest.TestCase):
    
    def setUp(self):
        self.db_manager = MockDBManager()
        # Autres initialisations
    
    def tearDown(self):
        # Nettoyage
        pass
    
    def test_ma_fonction(self):
        # Arrange
        attendu = "résultat attendu"
        
        # Act
        resultat = ma_fonction_a_tester()
        
        # Assert
        self.assertEqual(resultat, attendu)
```

## Classes Mock

Le fichier `helpers.py` fournit plusieurs classes mock qui simulent le comportement des composants réels de l'application. Utilisez ces mocks dans vos tests pour éviter de dépendre des composants externes.

Classes disponibles :
- `MockDBManager` : Mock du gestionnaire de base de données
- `MockOBSCapture` : Mock de la capture OBS
- `MockPyAudioCapture` : Mock de la capture PyAudio
- `MockSyncManager` : Mock du gestionnaire de synchronisation
- `MockStreamProcessor` : Mock du processeur de flux
- `MockActivityClassifier` : Mock du classificateur d'activité
- `MockExternalServiceClient` : Mock du client de service externe

## Création de données de test

Le fichier `helpers.py` fournit également des fonctions utilitaires pour créer et nettoyer des données temporaires :
- `create_temp_file` : Crée un fichier temporaire avec un contenu spécifique
- `create_temp_directory` : Crée un répertoire temporaire
- `cleanup_temp_file` : Supprime un fichier temporaire
- `cleanup_temp_directory` : Supprime un répertoire temporaire

## Bonnes pratiques

- Gardez les tests indépendants les uns des autres
- Utilisez des noms de méthodes descriptifs qui expliquent ce qui est testé
- Suivez le pattern AAA (Arrange, Act, Assert) pour structurer vos tests
- Utilisez les mocks pour isoler le code testé des dépendances externes
- Testez les cas positifs et négatifs (succès et échecs)
- Utilisez `setUp` et `tearDown` pour factoriser le code commun
- Évitez les effets de bord qui pourraient affecter d'autres tests
