# Classify Audio Video

## Présentation
Classify Audio Video est une application qui capture et analyse les flux audio et vidéo pour classifier automatiquement l'activité d'une personne. L'application détecte 7 types d'activités différentes (endormi, à table, lisant, au téléphone, en conversation, occupé, inactif) et envoie le résultat vers un service externe toutes les 5 minutes. En plus des flux en direct, l'application prend désormais en charge l'analyse de fichiers vidéo chargés dans OBS.

## Nouveautés

### Support pour OBS 31.0.2 (Mars 2025)
La dernière mise à jour ajoute la compatibilité avec OBS 31.0.2 et son API WebSocket intégrée :

- **Classe OBS31Capture** : Nouvelle classe optimisée pour capturer des images depuis OBS 31.0.2+ via WebSocket
- **Adaptateur OBS31Adapter** : Classe unifiant les fonctionnalités de capture, événements et média pour OBS 31.0.2+
- **Compatibilité OBS native** : Plus besoin d'installer le plugin WebSocket externe pour OBS 31.0.2+
- **Mécanisme de fallback** : Option pour utiliser des images de test si la capture échoue, garantissant la continuité de l'application
- **Scripts de diagnostic** : Outils pour explorer l'API WebSocket et tester la capture
- **Utilisé par défaut** : L'application utilise désormais OBS31Capture par défaut mais reste compatible avec les anciennes versions

Voir la [Documentation spécifique pour OBS 31.0.2](README_OBS31.md) pour plus de détails sur cette fonctionnalité.

### Architecture JavaScript modulaire (Mars 2025)
La dernière mise à jour introduit une architecture JavaScript modulaire pour améliorer la maintenabilité et les performances :

#### Scripts frontend modulaires
- **Division des fichiers volumineux** : Les fichiers JavaScript comme `model_testing.js` et `statistics.js` ont été divisés en modules spécialisés
- **Chargement asynchrone** : Modules chargés de manière asynchrone pour optimiser les performances
- **Architecture flexible** : Structure qui facilite les évolutions futures et les tests
- **Meilleur affichage des flux** : Amélioration de l'affichage des flux vidéo et audio avec gestion robuste des erreurs

#### Structure des modules JavaScript
L'architecture frontend a été réorganisée en modules spécialisés :

**Pour la page de test de modèle** :
- `video-feed.js` : Gestion de l'affichage des flux vidéo
- `audio-visualizer.js` : Visualisation et traitement des flux audio
- `classification.js` : Analyse et classification des activités
- `model-info.js` : Gestion des informations et opérations sur le modèle

**Pour la page de statistiques** :
- `data-loader.js` : Chargement et mise en cache des données
- `chart-manager.js` : Création et gestion des graphiques
- `export-manager.js` : Exportation des données dans différents formats
- `summary-manager.js` : Génération des résumés statistiques

### Améliorations de fiabilité (Mars 2025)
La mise à jour améliore la fiabilité de l'application en adressant deux problèmes majeurs :
- **Correction de la capture d'images OBS** : Résolution du problème "Erreur lors de la capture d'image: 'img'" grâce à une meilleure gestion des attributs de réponse OBS, avec support pour différentes versions d'OBS
- **Gestion améliorée de l'arrêt du programme** : Implémentation d'un mécanisme robuste de gestion CTRL+C et arrêt des threads, permettant une terminaison propre et rapide de l'application

Ces améliorations assurent un fonctionnement plus fluide et réduisent les risques de blocage de l'application.

### Restructuration du code
La mise à jour précédente apporte une restructuration majeure du code pour améliorer sa lisibilité, sa maintenabilité et son extensibilité. Le code est désormais organisé en modules plus petits et spécialisés, ce qui facilite :
- Le développement et la maintenance de fonctionnalités spécifiques
- La collaboration entre développeurs
- L'implémentation de tests unitaires
- L'extension et l'évolution de l'application

### Tests unitaires complets
Une suite complète de tests unitaires a été ajoutée pour garantir la qualité et la robustesse du code :
- Tests pour chaque module principal de l'application
- Mocks et utilitaires pour faciliter les tests
- Script d'exécution de tests flexible
- Documentation détaillée sur l'utilisation des tests

### Capture Audio via PyAudio
La mise à jour précédente a apporté une amélioration majeure : la capture audio est désormais réalisée directement via PyAudio au lieu d'OBS. Cette modification permet :
- Une capture audio haute qualité directement depuis le microphone
- Le maintien de la capture vidéo via OBS
- Une synchronisation précise entre les flux audio et vidéo
- Une analyse plus précise grâce à des données audio réelles (et non simulées)

### Gestionnaire de synchronisation
Un système de synchronisation audio/vidéo a été ajouté pour garantir que les flux audio et vidéo sont correctement alignés temporellement. Ce système permet :
- La capture simultanée de l'audio via PyAudio et de la vidéo via OBS
- L'alignement temporel des deux flux pour l'analyse
- La sauvegarde de clips synchronisés pour analyse ultérieure

### API audio étendues
De nouvelles API ont été ajoutées pour gérer les périphériques audio :
- Lister les périphériques audio disponibles (`/api/audio-devices`)
- Changer le périphérique audio de capture (`/api/set-audio-device`)
- Sauvegarder des clips synchronisés audio/vidéo (`/api/save-clip`)

### Système de gestion d'erreurs
Un système robuste de gestion d'erreurs a été implémenté pour améliorer la fiabilité et le débogage de l'application :
- Architecture d'erreurs hiérarchique avec codes standardisés
- Gestion centralisée des exceptions avec journalisation détaillée
- Messages d'erreur adaptatifs selon le contexte (API vs interface web)
- Mécanismes de récupération pour minimiser l'impact des problèmes
- Décorateurs pour simplifier la gestion des exceptions dans le code

## Fonctionnalités principales

- **Capture vidéo depuis OBS** : Connexion à OBS Studio via websocket pour recevoir les flux vidéo en temps réel
- **Support pour OBS 31.0.2+** : Compatibilité avec le WebSocket intégré d'OBS 31.0.2 et versions ultérieures
- **Capture audio via PyAudio** : Capture audio directe depuis le microphone ou autre périphérique audio
- **Synchronisation audio/vidéo** : Alignement temporel des flux audio et vidéo
- **Analyse avancée** : Traitement des flux pour extraire des caractéristiques pertinentes (mouvements, sons, présence humaine)
- **Classification d'activité** : Identification de l'activité courante parmi 7 catégories prédéfinies
- **Base de données** : Stockage de l'historique des activités avec horodatage
- **Statistiques** : Analyse des tendances, durées et fréquences des activités
- **Interface web** : Visualisation des données et tableaux de bord en temps réel
- **API externe** : Envoi des résultats vers un service tiers via HTTP POST
- **Analyse de fichiers vidéo** : Prise en charge des fichiers médias chargés dans OBS pour analyse complète ou image par image
- **Exportation de données** : Export des analyses en formats JSON et CSV
- **Tests unitaires** : Couverture de test complète pour tous les modules principaux
- **Gestion d'erreurs robuste** : Système complet pour la détection, le logging et la récupération des erreurs
- **Arrêt propre et réactif** : Mécanisme fiable pour terminer proprement l'application avec CTRL+C
- **Architecture frontend modulaire** : Organisation du code JavaScript en modules spécialisés pour améliorer la maintenabilité

## Documentation détaillée

La documentation complète est divisée en plusieurs sections pour une meilleure lisibilité :

- [Structure du projet](docs/STRUCTURE.md) - Description détaillée de l'organisation des fichiers et dossiers
- [Installation et prérequis](docs/INSTALLATION.md) - Instructions d'installation et configuration
- [Utilisation](docs/USAGE.md) - Guide d'utilisation de l'application
- [Tests unitaires](docs/TESTS.md) - Documentation sur les tests unitaires
- [Système de gestion d'erreurs](docs/ERROR_HANDLING.md) - Présentation du système de gestion d'erreurs
- [Fonctionnement technique](docs/TECHNICAL.md) - Explications techniques sur le fonctionnement interne
- [Dépannage](docs/TROUBLESHOOTING.md) - Solutions aux problèmes courants
- [Développement et extension](docs/DEVELOPMENT.md) - Guide pour étendre l'application
- [Architecture JavaScript](docs/JS_ARCHITECTURE.md) - Détails sur l'architecture modulaire JavaScript
- [Support OBS 31.0.2+](README_OBS31.md) - Guide pour utiliser l'application avec OBS 31.0.2 et plus

## Installation rapide

Pour installer et configurer l'application avec les dernières fonctionnalités :

```bash
# Cloner le dépôt
git clone https://github.com/rbaudu/classify-audio-video.git
cd classify-audio-video

# Installer les dépendances
python install_requirements.py

# Tester la compatibilité avec OBS 31.0.2 (si vous utilisez cette version d'OBS)
python tests/test_obs_31_api.py
python tests/test_obs_31_capture.py

# Démarrer l'application (utilise OBS31Capture par défaut)
python run.py
```

## Options de démarrage

L'application propose plusieurs options pour contrôler la version d'OBS à utiliser :

```bash
# Utiliser OBS31Capture (par défaut)
python run.py

# Utiliser explicitement OBS31Capture avec l'adaptateur
python run.py --obs-version 31 --use-adapter true

# Utiliser OBS31Capture directement (sans adaptateur)
python run.py --obs-version 31 --use-adapter false

# Utiliser l'ancienne implémentation pour OBS 30 et versions antérieures
python run.py --obs-version legacy

# Spécifier l'hôte et le port OBS
python run.py --obs-host 192.168.1.10 --obs-port 4455

# Obtenir la liste complète des options
python run.py --help
```

## Configuration de l'environnement

Vous pouvez également configurer l'application via des variables d'environnement :

```bash
# Configuration OBS
export OBS_HOST=localhost
export OBS_PORT=4455
export OBS_PASSWORD=votre_mot_de_passe

# Configuration OBS31
export USE_OBS_31=true      # true pour OBS 31.0.2+, false pour versions antérieures
export USE_OBS_ADAPTER=true # true pour utiliser l'adaptateur, false pour utiliser directement OBS31Capture

# Configuration Flask
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export FLASK_DEBUG=false

# Démarrer l'application avec ces paramètres
python run.py
```

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à soumettre des pull requests ou à signaler des problèmes via les issues GitHub.

## Licence

Ce projet est distribué sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Crédits

- [OBS Studio](https://obsproject.com/)
- [obs-websocket](https://github.com/obsproject/obs-websocket)
- [obsws-python](https://github.com/aatikturk/obsws-python)
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/)
- [Flask](https://flask.palletsprojects.com/)
- [TensorFlow](https://www.tensorflow.org/)
- [OpenCV](https://opencv.org/)
- [Chart.js](https://www.chartjs.org/)
- [Pillow](https://python-pillow.org/)
- [NumPy](https://numpy.org/)
