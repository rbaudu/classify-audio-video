# Classify Audio Video

## Présentation
Classify Audio Video est une application qui capture et analyse les flux audio et vidéo provenant d'OBS Studio pour classifier automatiquement l'activité d'une personne. L'application détecte 7 types d'activités différentes (endormi, à table, lisant, au téléphone, en conversation, occupé, inactif) et envoie le résultat vers un service externe toutes les 5 minutes.

## Fonctionnalités principales

- **Capture de flux OBS** : Connexion à OBS Studio via websocket pour recevoir les flux vidéo et audio en temps réel
- **Analyse avancée** : Traitement des flux pour extraire des caractéristiques pertinentes (mouvements, sons, présence humaine)
- **Classification d'activité** : Identification de l'activité courante parmi 7 catégories prédéfinies
- **Base de données** : Stockage de l'historique des activités avec horodatage
- **Statistiques** : Analyse des tendances, durées et fréquences des activités
- **Interface web** : Visualisation des données et tableaux de bord en temps réel
- **API externe** : Envoi des résultats vers un service tiers via HTTP POST

## Structure du projet

```
classify-audio-video/
├── README.md                 # Documentation du projet
├── requirements.txt          # Dépendances Python
├── server/                   # Code du serveur principal
│   ├── __init__.py           
│   ├── main.py               # Point d'entrée de l'application
│   ├── config.py             # Configuration de l'application
│   ├── capture/              # Module de capture des flux OBS
│   │   ├── __init__.py
│   │   ├── obs_capture.py    # Connexion et capture depuis OBS
│   │   └── stream_processor.py # Traitement des flux audio/vidéo
│   ├── analysis/             # Module d'analyse et classification
│   │   ├── __init__.py
│   │   └── activity_classifier.py # Classificateur d'activité
│   ├── database/             # Module de stockage des données
│   │   ├── __init__.py
│   │   └── db_manager.py     # Gestionnaire de base de données SQLite
│   └── api/                  # Module d'API et services externes
│       ├── __init__.py
│       └── external_service.py # Client pour le service externe
├── web/                      # Interface web
│   ├── templates/            # Gabarits HTML
│   │   ├── index.html        # Page d'accueil
│   │   ├── dashboard.html    # Tableau de bord
│   │   ├── statistics.html   # Statistiques d'activité
│   │   ├── history.html      # Historique des activités
│   │   └── model_testing.html # Test du modèle de classification
│   └── static/               # Ressources statiques
│       ├── css/              # Feuilles de style
│       │   └── main.css      # Style principal
│       └── js/               # Scripts JavaScript
│           ├── main.js       # Script principal
│           ├── dashboard.js  # Script du tableau de bord
│           ├── statistics.js # Script des statistiques
│           ├── history.js    # Script de l'historique
│           └── model_testing.js # Script de test du modèle
├── data/                     # Stockage des données
│   └── activity.db           # Base de données SQLite (générée à l'exécution)
└── models/                   # Modèles de classification pré-entraînés
    └── activity_classifier.h5 # Modèle de classification (à fournir)
```

## Prérequis

- Python 3.8 ou supérieur
- OBS Studio avec le plugin obs-websocket installé
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

3. Configuration d'OBS Studio (instructions détaillées ci-dessous)

4. Configurez l'application :
   - Modifiez le fichier `server/config.py` pour définir :
     - Les paramètres de connexion à OBS (hôte, port, mot de passe)
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

3. **Configurer les sources vidéo et audio appropriées** :
   - Créez une scène dédiée pour la capture d'activité
   - Ajoutez une source de capture vidéo :
     - "Capture de périphérique vidéo" pour une webcam
     - ou "Capture d'écran" pour analyser ce qui se passe sur votre écran
   - Ajoutez une source audio :
     - "Capture audio d'entrée" pour un microphone
     - et/ou "Capture audio de sortie" pour l'audio du système

4. **Vérifier que les sources sont actives** :
   - Assurez-vous que vos sources vidéo et audio ne sont pas muettes ou masquées
   - Vérifiez que les dispositifs de capture fonctionnent correctement

5. **Configuration recommandée pour de meilleures performances** :
   - Résolution vidéo : configurez une résolution moyenne (640x480 ou 720p) pour réduire la charge de traitement
   - Fréquence d'images : 15-30 FPS est suffisant pour l'analyse d'activité
   - Qualité audio : 44.1kHz, Mono est généralement suffisant

6. **Mettre à jour la configuration du programme** :
   - Modifiez le fichier `server/config.py` pour correspondre à vos paramètres OBS :
     ```python
     OBS_HOST = 'localhost'  # ou l'adresse IP si OBS est sur une autre machine
     OBS_PORT = 4444  # le port que vous avez configuré
     OBS_PASSWORD = 'votre-mot-de-passe'  # laissez vide si vous n'avez pas défini de mot de passe
     ```

7. **Test de connexion** :
   - Lancez OBS Studio
   - Lancez votre application Classify Audio Video
   - Vérifiez les journaux de l'application pour confirmer que la connexion est établie

## Utilisation

1. Lancez l'application :
```bash
python server/main.py
```

2. Accédez à l'interface web via votre navigateur :
```
http://localhost:5000
```

3. L'application commencera automatiquement à :
   - Se connecter à OBS Studio
   - Capturer et analyser les flux vidéo et audio
   - Classifier l'activité toutes les 5 minutes
   - Envoyer les résultats au service externe configuré

## Fonctionnement technique

### Capture de flux

La classe `OBSCapture` établit une connexion WebSocket avec OBS Studio et capture :
- Les images de la source vidéo (webcam ou capture d'écran)
- Les données audio du microphone ou de l'audio système

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

### Envoi au service externe

La classe `ExternalServiceClient` envoie les résultats toutes les 5 minutes via une requête HTTP POST au service configuré, avec les données suivantes :
```json
{
  "timestamp": 1645276800,
  "date_time": "2022-02-19 12:00:00",
  "activity": "lisant",
  "metadata": { ... }
}
```

## Interface web

L'interface web offre plusieurs vues :

1. **Accueil** : Présentation générale du système
2. **Tableau de bord** : Vue en temps réel de l'activité courante et des statistiques essentielles
3. **Statistiques** : Analyse détaillée des données collectées (graphiques, tendances)
4. **Historique** : Journal chronologique des activités détectées
5. **Test du modèle** : Interface pour tester et affiner le modèle de classification

### Fonctionnalités des scripts JavaScript

#### main.js
- **Utilitaires globaux** pour l'ensemble de l'application
- Configuration des paramètres communs (URL API, intervalles, couleurs, icônes)
- Fonctions de formatage (dates, durées)
- Gestion des requêtes API
- Surveillance de l'état de connexion au serveur
- Gestionnaire de modales

#### dashboard.js
- Affichage en temps réel de l'activité courante
- Mise à jour automatique des informations
- Visualisation des statistiques quotidiennes
- Chronologie graphique des activités récentes
- Gestion des événements de reconnexion au serveur

#### history.js
- **Filtrage et recherche** dans l'historique des activités
- Pagination des résultats
- Affichage détaillé des activités (durée, niveau de confiance)
- Visualisation des métadonnées dans une modale
- Exportation des données filtrées au format CSV

#### statistics.js
- **Visualisation graphique** des données statistiques
- Affichage de différentes périodes (jour, semaine, mois, année)
- Graphiques de répartition des activités et durées
- Distribution horaire des activités
- Analyse des tendances d'activité
- Exportation des données au format CSV et JSON

#### model_testing.js
- Affichage et contrôle des flux audio/vidéo en direct
- **Visualisation des caractéristiques extraites**
- Classification en temps réel et affichage des résultats
- Niveaux de confiance pour chaque type d'activité
- Gestion des informations sur le modèle
- Fonctionnalités d'import/export et réentraînement du modèle

## Personnalisation

### Ajouter de nouvelles catégories d'activité

1. Modifiez la liste `ACTIVITY_CLASSES` dans `server/config.py`
2. Ajoutez la logique de détection dans `_rule_based_classification()` de `ActivityClassifier`
3. Réentraînez le modèle si vous utilisez l'approche basée sur un modèle

### Modifier la fréquence d'analyse

Changez la valeur de `ANALYSIS_INTERVAL` dans `server/config.py` (en secondes)

### Intégration avec d'autres services

Modifiez la classe `ExternalServiceClient` pour adapter le format des données et les méthodes de connexion à votre service tiers.

## Troubleshooting

### Problèmes de connexion OBS

- Vérifiez que le plugin obs-websocket est correctement installé et activé
- Assurez-vous que le port n'est pas bloqué par un pare-feu
- Vérifiez que les identifiants de connexion dans `config.py` correspondent
- Lancez OBS avant de démarrer l'application Classify Audio Video
- Consultez les journaux de l'application pour identifier les problèmes de connexion spécifiques

### Erreurs de classification

- Si le modèle de classification produit des résultats incorrects, essayez de réentraîner le modèle avec davantage de données
- Ajustez les seuils dans la méthode `_rule_based_classification` pour améliorer la précision

### Performances

- Pour les systèmes moins puissants, réduisez la résolution vidéo dans `config.py`
- Augmentez l'intervalle d'analyse pour réduire l'utilisation du CPU

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à soumettre des pull requests ou à signaler des problèmes via les issues GitHub.

## Licence

Ce projet est distribué sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Crédits

- [OBS Studio](https://obsproject.com/)
- [obs-websocket](https://github.com/obsproject/obs-websocket)
- [Flask](https://flask.palletsprojects.com/)
- [TensorFlow](https://www.tensorflow.org/)
- [OpenCV](https://opencv.org/)
