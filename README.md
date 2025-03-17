# Classify Audio Video

## Présentation
Classify Audio Video est une application qui capture et analyse les flux audio et vidéo pour classifier automatiquement l'activité d'une personne. L'application détecte 7 types d'activités différentes (endormi, à table, lisant, au téléphone, en conversation, occupé, inactif) et envoie le résultat vers un service externe toutes les 5 minutes. En plus des flux en direct, l'application prend désormais en charge l'analyse de fichiers vidéo chargés dans OBS.

## Nouveautés

### Améliorations de fiabilité (Mars 2025)
La dernière mise à jour améliore la fiabilité de l'application en adressant deux problèmes majeurs :
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

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à soumettre des pull requests ou à signaler des problèmes via les issues GitHub.

## Licence

Ce projet est distribué sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Crédits

- [OBS Studio](https://obsproject.com/)
- [obs-websocket](https://github.com/obsproject/obs-websocket)
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/)
- [Flask](https://flask.palletsprojects.com/)
- [TensorFlow](https://www.tensorflow.org/)
- [OpenCV](https://opencv.org/)
- [Chart.js](https://www.chartjs.org/)
