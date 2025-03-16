# Installation et prérequis

Ce document détaille l'installation et la configuration complète de l'application Classify Audio Video.

## Prérequis système

- Python 3.8 ou supérieur
- OBS Studio avec le plugin obs-websocket installé
- PyAudio correctement installé et configuré
- Navigateur web moderne (Chrome, Firefox, Edge, Safari)
- Espace disque : 500 Mo minimum pour l'application et ses dépendances
- RAM : 4 Go minimum recommandé pour un fonctionnement fluide

## Étapes d'installation

### 1. Clonage du dépôt

Commencez par cloner le dépôt de l'application :

```bash
git clone https://github.com/rbaudu/classify-audio-video.git
cd classify-audio-video
```

### 2. Installation des dépendances Python

Installez toutes les dépendances requises à l'aide de pip :

```bash
pip install -r requirements.txt
```

Les dépendances principales comprennent :
- Flask pour le serveur web
- NumPy et OpenCV pour le traitement d'image
- PyAudio pour la capture audio
- TensorFlow pour la classification d'activité
- SQLite pour le stockage des données

### 3. Installation et configuration de PyAudio

PyAudio est inclus dans le fichier requirements.txt et s'installera normalement avec `pip install -r requirements.txt`. Cependant, si vous rencontrez des problèmes lors de l'installation de PyAudio :

#### Windows
```bash
pip install pyaudio
```

Si cela échoue, téléchargez le fichier wheel approprié depuis [le site de Christoph Gohlke](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) et installez-le avec :
```bash
pip install [chemin-vers-le-fichier-wheel]
```

#### macOS
```bash
brew install portaudio
pip install pyaudio
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install python3-dev portaudio19-dev
pip install pyaudio
```

#### Linux (Fedora/RHEL)
```bash
sudo dnf install python3-devel portaudio-devel
pip install pyaudio
```

### 4. Installation et configuration d'OBS Studio

#### Installation d'OBS Studio
1. Téléchargez OBS Studio depuis [le site officiel](https://obsproject.com/)
2. Installez-le en suivant les instructions pour votre système d'exploitation

#### Installation du plugin obs-websocket
1. Téléchargez la dernière version compatible avec votre version d'OBS depuis [le dépôt GitHub](https://github.com/obsproject/obs-websocket/releases)
2. Suivez les instructions d'installation spécifiques à votre système d'exploitation
3. Redémarrez OBS après l'installation

#### Configuration d'OBS Studio
1. Lancez OBS Studio
2. Allez dans le menu "Outils" (ou "Tools") > "WebSockets Server Settings"
3. Cochez la case "Enable WebSockets Server"
4. Configurez les paramètres suivants :
   - Port : 4444 (par défaut, ou choisissez un autre port si nécessaire)
   - Mot de passe : définissez un mot de passe si vous souhaitez sécuriser la connexion
5. Cliquez sur "OK" pour enregistrer les paramètres

### 5. Configuration des sources vidéo dans OBS

1. Créez une scène dédiée pour la capture d'activité
2. Ajoutez une source de capture vidéo :
   - "Capture de périphérique vidéo" pour une webcam
   - ou "Capture d'écran" pour analyser ce qui se passe sur votre écran

### 6. Configuration des fichiers média (optionnel)

Si vous souhaitez analyser des fichiers vidéo :

1. Dans OBS Studio, cliquez sur le bouton "+" dans le panneau Sources
2. Sélectionnez "Source multimédia" (ou Media Source)
3. Donnez un nom à la source (par exemple "Vidéo test")
4. Cochez "Fichier local" et cliquez sur "Parcourir" pour sélectionner votre fichier vidéo
5. Vous pouvez ajuster les options comme la mise en boucle, le volume, etc.
6. Cliquez sur "OK" pour ajouter la source

### 7. Vérification des sources

1. Assurez-vous que vos sources vidéo ne sont pas masquées
2. Vérifiez que les dispositifs de capture fonctionnent correctement
3. Pour les fichiers médias, assurez-vous qu'ils sont visibles dans la prévisualisation

### 8. Configuration de l'application

Modifiez le fichier `server/config.py` pour correspondre à vos paramètres :

```python
class Config:
    # Paramètres OBS
    OBS_HOST = 'localhost'  # ou l'adresse IP si OBS est sur une autre machine
    OBS_PORT = 4444  # le port que vous avez configuré
    OBS_PASSWORD = 'votre-mot-de-passe'  # laissez vide si vous n'avez pas défini de mot de passe
    
    # Configuration audio PyAudio
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    AUDIO_FORMAT = pyaudio.paInt16
    AUDIO_CHUNK_SIZE = 1024
    
    # Configuration de l'API externe
    EXTERNAL_API_URL = 'https://api.example.com/endpoint'
    EXTERNAL_API_KEY = 'votre-clé-api'
    
    # Autres paramètres
    ANALYSIS_INTERVAL = 300  # 5 minutes en secondes
    DB_PATH = 'data/activity.db'
    TEMP_CAPTURES_DIR = 'data/temp_captures'
    ANALYSIS_DIR = 'data/analyses'
```

## Optimisation des performances

### Configuration vidéo recommandée

Pour de meilleures performances, configurez OBS avec ces paramètres :

- **Résolution vidéo** : 640x480 ou 720p (1280x720) 
- **Fréquence d'images** : 15-30 FPS
- **Format vidéo** : NV12 ou I420 (plus efficaces pour le traitement d'image)
- **Bitrate** : 2500-5000 Kbps maximum pour réduire la charge CPU

### Configuration audio recommandée

- **Taux d'échantillonnage** : 16000 Hz (suffisant pour l'analyse vocale)
- **Canaux** : Mono (1 canal)
- **Format** : 16 bits
- **Suppression de bruit** : Activée si disponible dans OBS

### Ressources système

- Si l'application s'exécute sur un système à ressources limitées, vous pouvez :
  - Réduire la résolution vidéo à 320x240
  - Baisser la fréquence d'images à 10 FPS
  - Augmenter `AUDIO_CHUNK_SIZE` à 2048 ou 4096 dans la configuration
  - Augmenter `ANALYSIS_INTERVAL` à 600 secondes (10 minutes) ou plus

## Création des répertoires nécessaires

Les répertoires suivants seront créés automatiquement au premier lancement :

```
data/
├── activity.db               # Base de données SQLite (générée à l'exécution)
├── temp_captures/            # Dossier pour les clips audio/vidéo temporaires
└── analyses/                 # Dossier pour les analyses vidéo temporaires
```

Vous pouvez également les créer manuellement avant le lancement :

```bash
mkdir -p data/temp_captures data/analyses
```

## Modèles de classification

Pour utiliser le classificateur basé sur un modèle de deep learning :

1. Placez votre modèle de classification pré-entraîné dans le dossier `models/`
2. Nommez-le `activity_classifier.h5` ou mettez à jour la configuration pour pointer vers votre fichier

Si aucun modèle n'est disponible, l'application utilisera automatiquement la classification basée sur des règles.

## Vérification de l'installation

Pour vérifier que tout est correctement installé :

```bash
python run.py --check
```

Cette commande effectuera des vérifications sur :
- La connexion à OBS
- La disponibilité des périphériques audio
- L'accès à la base de données
- Les permissions des dossiers

## Installation en environnement de développement

Si vous souhaitez contribuer au projet, nous recommandons d'utiliser un environnement virtuel :

```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dépendances additionnelles pour le développement
```

## Installation en mode production

Pour un déploiement en production, des étapes supplémentaires sont recommandées :

1. Utilisez un serveur WSGI comme gunicorn ou uWSGI
2. Configurez un proxy comme Nginx ou Apache
3. Mettez en place un service système pour démarrer automatiquement l'application

Exemple de fichier de service systemd pour Linux :

```ini
[Unit]
Description=Classify Audio Video Service
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/classify-audio-video
ExecStart=/path/to/python /path/to/classify-audio-video/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Dépannage d'installation

Si vous rencontrez des problèmes lors de l'installation, consultez la section [Troubleshooting](TROUBLESHOOTING.md) pour des solutions aux problèmes courants.

Pour plus d'informations sur l'utilisation de l'application, consultez le guide [d'utilisation](USAGE.md).
