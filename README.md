# Classify Audio Video

## Présentation
Classify Audio Video est une application qui capture et analyse les flux audio et vidéo pour classifier automatiquement l'activité d'une personne. L'application détecte 7 types d'activités différentes (endormi, à table, lisant, au téléphone, en conversation, occupé, inactif) et envoie le résultat vers un service externe toutes les 5 minutes. En plus des flux en direct, l'application prend désormais en charge l'analyse de fichiers vidéo chargés dans OBS.

## Nouveautés

### Capture Audio via PyAudio
La dernière mise à jour apporte une amélioration majeure : la capture audio est désormais réalisée directement via PyAudio au lieu d'OBS. Cette modification permet :
- Une capture audio haute qualité directement depuis le microphone
- Le maintien de la capture vidéo via OBS
- Une synchronisation précise entre les flux audio et vidéo
- Une analyse plus précise grâce à des données audio réelles (et non simulées)

### Gestionnaire de synchronisation
Un nouveau système de synchronisation audio/vidéo a été ajouté pour garantir que les flux audio et vidéo sont correctement alignés temporellement. Ce système permet :
- La capture simultanée de l'audio via PyAudio et de la vidéo via OBS
- L'alignement temporel des deux flux pour l'analyse
- La sauvegarde de clips synchronisés pour analyse ultérieure

### API audio étendues
De nouvelles API ont été ajoutées pour gérer les périphériques audio :
- Lister les périphériques audio disponibles (`/api/audio-devices`)
- Changer le périphérique audio de capture (`/api/set-audio-device`)
- Sauvegarder des clips synchronisés audio/vidéo (`/api/save-clip`)

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

## Structure du projet

```
classify-audio-video/
├── README.md                     # Documentation du projet
├── requirements.txt              # Dépendances Python
├── run.py                        # Point d'entrée principal pour lancer l'application
├── server/                       # Code du serveur principal
│   ├── __init__.py               # Initialisation du module server et configuration centralisée
│   ├── main.py                   # Point d'entrée de l'application
│   ├── config.py                 # Configuration de l'application
│   ├── analysis/                 # Module d'analyse et classification
│   │   ├── __init__.py
│   │   └── activity_classifier.py # Classificateur d'activité
│   ├── api/                      # Module d'API et services externes
│   │   ├── __init__.py
│   │   └── external_service.py   # Client pour le service externe
│   ├── capture/                  # Module de capture des flux
│   │   ├── __init__.py
│   │   ├── obs_capture.py        # Connexion et capture vidéo depuis OBS
│   │   ├── pyaudio_capture.py    # Capture audio via PyAudio
│   │   ├── sync_manager.py       # Gestionnaire de synchronisation audio/vidéo
│   │   └── stream_processor.py   # Traitement des flux audio/vidéo
│   └── database/                 # Module de stockage des données
│       ├── __init__.py
│       └── db_manager.py         # Gestionnaire de base de données SQLite
├── web/                          # Interface web
│   ├── templates/                # Gabarits HTML
│   │   ├── index.html            # Page d'accueil
│   │   ├── dashboard.html        # Tableau de bord
│   │   ├── statistics.html       # Statistiques d'activité
│   │   ├── history.html          # Historique des activités
│   │   ├── model_testing.html    # Test du modèle de classification
│   │   ├── analysis_results.html # Résultats d'analyse vidéo
│   │   ├── analysis_in_progress.html # Suivi d'analyse en cours
│   │   └── error.html            # Page d'erreur
│   └── static/                   # Ressources statiques
│       ├── css/                  # Feuilles de style
│       │   └── main.css          # Style principal
│       └── js/                   # Scripts JavaScript
│           ├── main.js           # Script principal (utilitaires, configuration)
│           ├── dashboard.js      # Script du tableau de bord
│           ├── history.js        # Script de l'historique
│           ├── statistics.js     # Script des statistiques
│           └── model_testing.js  # Script de test du modèle
├── data/                         # Stockage des données
│   ├── activity.db               # Base de données SQLite (générée à l'exécution)
│   ├── temp_captures/            # Dossier pour les clips audio/vidéo temporaires
│   └── analyses/                 # Dossier pour les analyses vidéo temporaires
└── models/                       # Modèles de classification pré-entraînés
    └── activity_classifier.h5    # Modèle de classification (à fournir)
```

## Prérequis

- Python 3.8 ou supérieur
- OBS Studio avec le plugin obs-websocket installé
- PyAudio correctement installé et configuré
- Navigateur web moderne (Chrome, Firefox, Edge, Safari)

## Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/rbaudu/classify-audio-video.git
cd classify-audio-video
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

### Note sur l'installation de PyAudio

PyAudio est inclus dans le fichier requirements.txt et s'installera normalement avec `pip install -r requirements.txt`. Cependant, si vous rencontrez des problèmes lors de l'installation de PyAudio :

- **Windows** : Essayez `pip install pyaudio` directement, ou téléchargez le fichier wheel approprié depuis [le site de Christoph Gohlke](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
- **macOS** : Installez d'abord PortAudio avec `brew install portaudio`, puis `pip install pyaudio`
- **Linux (Ubuntu/Debian)** : Installez les dépendances avec `sudo apt-get install python3-dev portaudio19-dev`, puis `pip install pyaudio`

3. Configuration d'OBS Studio (instructions détaillées ci-dessous)

4. Configurez l'application :
   - Modifiez le fichier `server/config.py` pour définir :
     - Les paramètres de connexion à OBS (hôte, port, mot de passe)
     - Les paramètres audio pour PyAudio (taux d'échantillonnage, format, etc.)
     - L'URL du service externe
     - Les autres paramètres selon vos besoins

## Configuration détaillée d'OBS Studio

Pour que OBS Studio fonctionne correctement avec cette application, suivez ces étapes précises :

1. **Installer le plugin obs-websocket** :
   - Téléchargez la dernière version compatible avec votre version d'OBS sur https://github.com/obsproject/obs-websocket/releases
   - Suivez les instructions d'installation spécifiques à votre système d'exploitation
   - Redémarrez OBS après l'installation

2. **Activer et configurer le serveur WebSocket dans OBS** :
   - Lancez OBS Studio
   - Allez dans le menu "Outils" (ou "Tools") > "WebSockets Server Settings"
   - Cochez la case "Enable WebSockets Server"
   - Configurez les paramètres suivants :
     - Port : 4444 (par défaut, ou choisissez un autre port si nécessaire)
     - Mot de passe : définissez un mot de passe si vous souhaitez sécuriser la connexion
   - Cliquez sur "OK" pour enregistrer les paramètres

3. **Configurer les sources vidéo appropriées** :
   - Créez une scène dédiée pour la capture d'activité
   - Ajoutez une source de capture vidéo :
     - "Capture de périphérique vidéo" pour une webcam
     - ou "Capture d'écran" pour analyser ce qui se passe sur votre écran

4. **Ajouter des fichiers médias (pour l'analyse de vidéos)** :
   - Dans OBS Studio, cliquez sur le bouton "+" dans le panneau Sources
   - Sélectionnez "Source multimédia" (ou Media Source)
   - Donnez un nom à la source (par exemple "Vidéo test")
   - Cochez "Fichier local" et cliquez sur "Parcourir" pour sélectionner votre fichier vidéo
   - Vous pouvez ajuster les options comme la mise en boucle, le volume, etc.
   - Cliquez sur "OK" pour ajouter la source

5. **Vérifier que les sources sont actives** :
   - Assurez-vous que vos sources vidéo ne sont pas masquées
   - Vérifiez que les dispositifs de capture fonctionnent correctement
   - Pour les fichiers médias, assurez-vous qu'ils sont visibles dans la prévisualisation

6. **Configuration recommandée pour de meilleures performances** :
   - Résolution vidéo : configurez une résolution moyenne (640x480 ou 720p) pour réduire la charge de traitement
   - Fréquence d'images : 15-30 FPS est suffisant pour l'analyse d'activité

7. **Mettre à jour la configuration du programme** :
   - Modifiez le fichier `server/config.py` pour correspondre à vos paramètres OBS :
     ```python
     class Config:
         # ...
         OBS_HOST = 'localhost'  # ou l'adresse IP si OBS est sur une autre machine
         OBS_PORT = 4444  # le port que vous avez configuré
         OBS_PASSWORD = 'votre-mot-de-passe'  # laissez vide si vous n'avez pas défini de mot de passe
         
         # Configuration audio PyAudio
         AUDIO_SAMPLE_RATE = 16000
         AUDIO_CHANNELS = 1
         AUDIO_FORMAT = pyaudio.paInt16
         AUDIO_CHUNK_SIZE = 1024
     ```

## Utilisation

1. Lancez l'application (utiliser toujours le fichier run.py) :
```bash
python run.py
```

2. Accédez à l'interface web via votre navigateur :
```
http://localhost:5000
```

3. L'application commencera automatiquement à :
   - Se connecter à OBS Studio pour la vidéo
   - Capturer l'audio via PyAudio (microphone par défaut)
   - Synchroniser les flux audio et vidéo
   - Analyser et classifier l'activité toutes les 5 minutes
   - Envoyer les résultats au service externe configuré

4. Pour changer le périphérique audio :
   - Accédez à l'API `/api/audio-devices` pour obtenir la liste des périphériques disponibles
   - Utilisez l'API `/api/set-audio-device` en fournissant l'index du périphérique souhaité

5. Pour analyser des fichiers vidéo :
   - Accédez à l'onglet "Test du modèle"
   - Basculez vers l'onglet "Fichiers vidéo"
   - Sélectionnez une source média dans la liste déroulante
   - Utilisez les contrôles de lecture pour naviguer dans la vidéo
   - Cliquez sur "Analyser cette image" pour classifier l'image actuelle
   - Ou cliquez sur "Analyser la vidéo complète" pour une analyse de toute la vidéo

## Fonctionnement technique

### Capture de flux et synchronisation

1. **Capture vidéo via OBS** :
   - La classe `OBSCapture` établit une connexion WebSocket avec OBS Studio
   - Elle capture les images de la source vidéo (webcam, capture d'écran ou fichier média)

2. **Capture audio via PyAudio** :
   - La classe `PyAudioCapture` initialise PyAudio et ouvre un flux audio
   - Elle capture les données audio depuis le microphone ou autre périphérique
   - Les données sont stockées dans un buffer circulaire pour permettre la synchronisation

3. **Synchronisation audio/vidéo** :
   - Le `SyncManager` coordonne les deux types de capture
   - Il associe les frames vidéo avec les échantillons audio correspondants
   - Il fournit des méthodes pour récupérer des données synchronisées pour l'analyse

### Traitement des flux

La classe `StreamProcessor` extrait des caractéristiques importantes :
- Détection de mouvement par différence d'images
- Analyse des niveaux sonores et fréquences dominantes
- Détection de présence humaine par analyse de couleur de peau (simplifié)

### Classification d'activité

Le module `ActivityClassifier` utilise deux approches :
1. **Classification basée sur un modèle** : Utilise un modèle de deep learning (si disponible dans `/models`) pour identifier l'activité
2. **Classification basée sur des règles** : Utilise des heuristiques prédéfinies comme solution de repli

Les règles de classification incluent :
- **Endormi** : Très peu de mouvement, absence de son
- **À table** : Mouvement modéré, posture caractéristique
- **Lisant** : Peu de mouvement, position statique, attention visuelle
- **Au téléphone** : Parole détectée avec peu de mouvement
- **En conversation** : Parole active avec mouvements gestuels
- **Occupé** : Beaucoup de mouvement, activité physique
- **Inactif** : Peu de mouvement, absence prolongée

### Stockage des données

Le `DBManager` gère une base de données SQLite qui stocke :
- L'horodatage de chaque classification
- Le type d'activité détecté
- Le niveau de confiance de la classification
- Les métadonnées supplémentaires
- Les résultats complets des analyses de vidéo

### Analyse de fichiers vidéo

Le processus d'analyse de fichiers vidéo fonctionne comme suit :
1. L'utilisateur sélectionne un fichier média chargé dans OBS
2. L'utilisateur peut choisir entre :
   - **Analyse d'une image** : Classification de l'image actuellement visible
   - **Analyse complète** : La vidéo est échantillonnée à intervalles réguliers (configurable)
3. Pour l'analyse complète :
   - Une tâche d'arrière-plan est lancée pour analyser la vidéo
   - L'utilisateur est redirigé vers une page de suivi de progression
   - Une fois l'analyse terminée, les résultats sont affichés avec des graphiques et statistiques
   - Les résultats peuvent être exportés en CSV ou JSON

### Envoi au service externe

La classe `ExternalServiceClient` envoie les résultats toutes les 5 minutes via une requête HTTP POST au service configuré.

## Troubleshooting

### Problèmes de configuration audio

- Vérifiez que PyAudio est correctement installé
- Assurez-vous que votre microphone est correctement détecté par votre système
- Consultez la liste des périphériques audio via l'API `/api/audio-devices`
- Si aucun périphérique n'est détecté, vérifiez les pilotes audio de votre système

### Problèmes de synchronisation audio/vidéo

- Si vous remarquez un décalage entre l'audio et la vidéo, ajustez `AUDIO_VIDEO_SYNC_BUFFER_SIZE` dans config.py
- Vérifiez que la charge CPU n'est pas trop élevée, ce qui pourrait ralentir le traitement
- Pour les systèmes moins puissants, augmentez `AUDIO_CHUNK_SIZE` pour réduire la charge de traitement

### Problèmes de connexion OBS

- Vérifiez que le plugin obs-websocket est correctement installé et activé
- Assurez-vous que le port n'est pas bloqué par un pare-feu
- Vérifiez que les identifiants de connexion dans `config.py` correspondent
- Lancez OBS avant de démarrer l'application Classify Audio Video

### Problèmes avec les fichiers vidéo

- Assurez-vous que les formats des fichiers sont pris en charge par OBS (mp4, mov, avi, etc.)
- Vérifiez que les sources média sont correctement ajoutées et visibles dans OBS
- Si une analyse vidéo échoue, consultez les journaux d'OBS et de l'application
- Pour les vidéos longues, augmentez l'intervalle d'échantillonnage pour réduire le temps d'analyse

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
