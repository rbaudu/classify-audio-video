# Classify Audio Video

## Présentation
Classify Audio Video est une application qui capture et analyse les flux audio et vidéo provenant d'OBS Studio pour classifier automatiquement l'activité d'une personne. L'application détecte 7 types d'activités différentes (endormi, à table, lisant, au téléphone, en conversation, occupé, inactif) et envoie le résultat vers un service externe toutes les 5 minutes. En plus des flux en direct, l'application prend désormais en charge l'analyse de fichiers vidéo chargés dans OBS.

## Fonctionnalités principales

- **Capture de flux OBS** : Connexion à OBS Studio via websocket pour recevoir les flux vidéo et audio en temps réel
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
│   ├── capture/                  # Module de capture des flux OBS
│   │   ├── __init__.py
│   │   ├── obs_capture.py        # Connexion et capture depuis OBS
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
│   └── analyses/                 # Dossier pour les analyses vidéo temporaires
└── models/                       # Modèles de classification pré-entraînés
    └── activity_classifier.h5    # Modèle de classification (à fournir)
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

4. **Ajouter des fichiers médias (pour l'analyse de vidéos)** :
   - Dans OBS Studio, cliquez sur le bouton "+" dans le panneau Sources
   - Sélectionnez "Source multimédia" (ou Media Source)
   - Donnez un nom à la source (par exemple "Vidéo test")
   - Cochez "Fichier local" et cliquez sur "Parcourir" pour sélectionner votre fichier vidéo
   - Vous pouvez ajuster les options comme la mise en boucle, le volume, etc.
   - Cliquez sur "OK" pour ajouter la source

5. **Vérifier que les sources sont actives** :
   - Assurez-vous que vos sources vidéo et audio ne sont pas muettes ou masquées
   - Vérifiez que les dispositifs de capture fonctionnent correctement
   - Pour les fichiers médias, assurez-vous qu'ils sont visibles dans la prévisualisation

6. **Configuration recommandée pour de meilleures performances** :
   - Résolution vidéo : configurez une résolution moyenne (640x480 ou 720p) pour réduire la charge de traitement
   - Fréquence d'images : 15-30 FPS est suffisant pour l'analyse d'activité
   - Qualité audio : 44.1kHz, Mono est généralement suffisant

7. **Mettre à jour la configuration du programme** :
   - Modifiez le fichier `server/config.py` pour correspondre à vos paramètres OBS :
     ```python
     class Config:
         # ...
         OBS_HOST = 'localhost'  # ou l'adresse IP si OBS est sur une autre machine
         OBS_PORT = 4444  # le port que vous avez configuré
         OBS_PASSWORD = 'votre-mot-de-passe'  # laissez vide si vous n'avez pas défini de mot de passe
     ```

8. **Test de connexion** :
   - Lancez OBS Studio
   - Lancez votre application Classify Audio Video
   - Vérifiez les journaux de l'application pour confirmer que la connexion est établie

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
   - Se connecter à OBS Studio
   - Capturer et analyser les flux vidéo et audio
   - Classifier l'activité toutes les 5 minutes
   - Envoyer les résultats au service externe configuré

4. Pour analyser des fichiers vidéo :
   - Accédez à l'onglet "Test du modèle"
   - Basculez vers l'onglet "Fichiers vidéo"
   - Sélectionnez une source média dans la liste déroulante
   - Utilisez les contrôles de lecture pour naviguer dans la vidéo
   - Cliquez sur "Analyser cette image" pour classifier l'image actuelle
   - Ou cliquez sur "Analyser la vidéo complète" pour une analyse de toute la vidéo

## Structure des importations

L'application utilise un système d'importation centralisé pour faciliter la gestion des dépendances et éviter les problèmes d'importations cycliques :

1. **Module principal `server/__init__.py`** :
   - Importe toutes les configurations depuis `server/config.py`
   - Expose ces configurations au niveau du package server
   - Permet d'importer facilement les variables de configuration depuis n'importe quel module

2. **Point d'entrée `run.py`** :
   - Ajoute le chemin du projet au chemin de recherche Python (sys.path)
   - Gère correctement les importations entre les différents modules
   - **Toujours utiliser ce fichier pour démarrer l'application**

3. **Exemples d'importation** :
   - Pour accéder aux configurations :
     ```python
     from server import OBS_HOST, OBS_PORT, DB_PATH
     ```
   - Pour accéder aux classes :
     ```python
     from server.capture.obs_capture import OBSCapture
     from server.database.db_manager import DBManager
     ```

4. **Pourquoi cette structure ?**
   - Évite les problèmes d'importation relative (`from ..module import X`)
   - Centralize la configuration
   - Facilite la maintenance et l'évolution du code

### Résolution des problèmes d'importation courants

Si vous rencontrez des erreurs d'importation lors de l'exécution :

1. **Toujours utiliser `python run.py`** au lieu de `python server/main.py`
2. Vérifier que tous les fichiers `__init__.py` sont présents dans chaque dossier
3. Préférer les importations absolues (`from server.xxx import X`) aux importations relatives

## Débogage avec ipdb

Pour faciliter le débogage de l'application, vous pouvez utiliser ipdb (Improved Python Debugger), qui offre une interface interactive pour inspecter et manipuler le code pendant son exécution.

### Installation d'ipdb

Si ce n'est pas déjà fait, installez ipdb :
```bash
pip install ipdb
```

### Utilisation basique

1. **Ajouter un point d'arrêt dans le code** :
   ```python
   import ipdb
   
   def ma_fonction():
       # Code...
       ipdb.set_trace()  # Le débogueur s'arrêtera ici
       # Suite du code...
   ```

2. **Commandes ipdb utiles** :
   - `n` (next) : Exécuter la ligne suivante sans entrer dans les fonctions
   - `s` (step) : Exécuter la ligne suivante et entrer dans les fonctions
   - `c` (continue) : Continuer l'exécution jusqu'au prochain point d'arrêt
   - `q` (quit) : Quitter le débogueur et arrêter l'exécution
   - `p expression` : Afficher la valeur d'une expression
   - `pp expression` : Afficher la valeur d'une expression avec un affichage formaté
   - `l` : Afficher le code autour de la ligne courante
   - `ll` : Afficher la fonction courante
   - `w` : Afficher la pile d'appels
   - `b ligne` ou `b fichier:ligne` : Ajouter un point d'arrêt
   - `h` : Afficher l'aide des commandes

### Débogage spécifique à Classify Audio Video

Pour déboguer les parties critiques de l'application :

1. **Débogage de la capture OBS** :
   ```python
   # Dans obs_capture.py
   def connect_to_obs(self):
       import ipdb; ipdb.set_trace()
       # Inspectez les paramètres de connexion et le processus d'établissement de la connexion
   ```

2. **Débogage du classificateur d'activité** :
   ```python
   # Dans activity_classifier.py
   def classify_activity(self, video_frame, audio_data):
       import ipdb; ipdb.set_trace()
       # Examinez les données d'entrée et les résultats de classification
   ```

3. **Débogage de l'analyse de fichiers vidéo** :
   ```python
   # Dans main.py, fonction analyze_video
   def analyze_video(video_source, interval):
       import ipdb; ipdb.set_trace()
       # Inspectez le processus d'analyse et les résultats
   ```

### Conseils avancés pour ipdb

1. **Points d'arrêt conditionnels** :
   ```python
   if problematic_condition:
       import ipdb; ipdb.set_trace()
   ```

2. **Utilisation avec les exceptions** :
   ```python
   try:
       # Code susceptible de générer une exception
   except Exception as e:
       import ipdb; ipdb.set_trace()
       # Inspectez l'exception et l'état du programme
   ```

3. **Déboguer avec post-mortem** : Si le programme plante, vous pouvez examiner l'état au moment du plantage :
   ```python
   try:
       # Code qui plante
   except:
       import ipdb; ipdb.post_mortem()
   ```

4. **Lancer l'application en mode débogage** :
   ```bash
   python -m ipdb run.py
   ```

## Débogage du serveur Flask

L'application utilise Flask comme framework web. Voici comment déboguer efficacement le serveur et les aspects liés à l'interface web.

### Configuration du mode debug

1. **Activer le mode debug dans Flask** :
   ```python
   # Dans main.py
   app = Flask(__name__, template_folder='../web/templates', static_folder='../web/static')
   app.config['DEBUG'] = True
   
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=5000, debug=True)
   ```

2. **Avantages du mode debug** :
   - Rechargement automatique du serveur lors des modifications de code
   - Traceback interactif dans le navigateur en cas d'erreur
   - Console de débogage intégrée
   - Préservation des sessions lors du redémarrage

### Utilisation de Flask avec ipdb

1. **Déboguer les routes Flask** :
   ```python
   @app.route('/dashboard')
   def dashboard():
       import ipdb; ipdb.set_trace()
       # Examinez les données et le contexte avant le rendu du template
       return render_template('dashboard.html')
   ```

2. **Déboguer les requêtes AJAX** :
   ```python
   @app.route('/api/analyze_frame', methods=['POST'])
   def analyze_frame_api():
       import ipdb; ipdb.set_trace()
       # Inspectez les données de la requête et préparez la réponse
       data = request.json
       # Traitement...
       return jsonify(result)
   ```

3. **Déboguer les templates** : Pour trouver les problèmes de rendu ou de variables dans les templates, ajoutez des points d'arrêt avant l'appel à `render_template`.

### Conseils pour déboguer Flask

1. **Journalisation avancée** :
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   logger = logging.getLogger(__name__)
   
   @app.route('/complex_route')
   def complex_route():
       logger.debug("Entering complex_route with args: %s", request.args)
       # Code...
       logger.debug("Processing complete, result: %s", result)
       return result
   ```

2. **Inspecter les sessions et cookies** :
   ```python
   @app.route('/check_session')
   def check_session():
       import ipdb; ipdb.set_trace()
       # Examinez session, request.cookies, etc.
       return jsonify(dict(session))
   ```

3. **Déboguer les problèmes de requêtes parallèles** :
   - En mode débogage avec ipdb, les requêtes supplémentaires peuvent rester en attente
   - Utilisez des sessions de navigateur distinctes ou des navigateurs différents pour tester
   - Pensez à utiliser un délai de timeout plus long dans le client JavaScript pour les requêtes AJAX

4. **Tester les réponses API** :
   ```python
   @app.route('/api/activity_data')
   def get_activity_data():
       # Préparer les données
       response_data = prepare_activity_data()
       
       # Vérifier les données avant de les renvoyer
       if debug_mode:
           import ipdb; ipdb.set_trace()
           # Inspectez response_data pour vérifier sa structure
       
       return jsonify(response_data)
   ```

### Déboguer les WebSockets (si utilisés)

Si votre application utilise des WebSockets pour des communications en temps réel :

```python
@socketio.on('connect')
def handle_connect():
    import ipdb; ipdb.set_trace()
    # Examinez l'établissement de la connexion

@socketio.on('activity_update')
def handle_activity_update(data):
    import ipdb; ipdb.set_trace()
    # Examinez les données d'activité reçues
```

## Fonctionnement technique

### Capture de flux

La classe `OBSCapture` établit une connexion WebSocket avec OBS Studio et capture :
- Les images de la source vidéo (webcam ou capture d'écran)
- Les données audio du microphone ou de l'audio système
- Les frames des fichiers vidéo chargés dans OBS

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
   - Onglet **Flux en direct** : Analyse du flux vidéo/audio en temps réel
   - Onglet **Fichiers vidéo** : Contrôle et analyse des fichiers médias chargés dans OBS
6. **Résultats d'analyse** : Affiche les résultats détaillés d'une analyse vidéo complète

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
- Gestion des onglets (flux en direct et fichiers vidéo)
- **Flux en direct** :
  - Affichage et contrôle des flux audio/vidéo en direct
  - Visualisation des caractéristiques extraites
  - Classification en temps réel et affichage des résultats
  - Niveaux de confiance pour chaque type d'activité
  - Fonctionnalités d'import/export et réentraînement du modèle
- **Fichiers vidéo** :
  - Listage et sélection des sources média disponibles dans OBS
  - Contrôles de lecture (play, pause, restart, seek)
  - Analyse d'une seule image ou de la vidéo complète
  - Configuration des options d'analyse (intervalle, sauvegarde, timeline)
  - Accès aux analyses précédentes

## Personnalisation

### Ajouter de nouvelles catégories d'activité

1. Modifiez la liste `ACTIVITY_CLASSES` dans `server/config.py`
2. Ajoutez la logique de détection dans `_rule_based_classification()` de `ActivityClassifier`
3. Réentraînez le modèle si vous utilisez l'approche basée sur un modèle

### Modifier la fréquence d'analyse

Changez la valeur de `ANALYSIS_INTERVAL` dans `server/config.py` (en secondes)

### Personnaliser l'analyse de fichiers vidéo

Vous pouvez ajuster plusieurs paramètres pour l'analyse de fichiers vidéo :
1. **Intervalle d'échantillonnage** : Modifiez les options dans `model_testing.html` ou la valeur par défaut dans `main.py`
2. **Format d'exportation** : Ajoutez de nouveaux formats dans `main.py` et `analysis_results.html`
3. **Visualisations** : Personnalisez les graphiques dans `analysis_results.html`

### Intégration avec d'autres services

Modifiez la classe `ExternalServiceClient` pour adapter le format des données et les méthodes de connexion à votre service tiers.

## Troubleshooting

### Problèmes d'importation

Si vous rencontrez des erreurs du type `ImportError: cannot import name X from Y` :
- Vérifiez que vous lancez l'application via `python run.py`
- N'exécutez jamais directement `python server/main.py` ou d'autres modules
- Si le problème persiste, vérifiez les modules d'initialisation (`__init__.py`) de chaque package

### Problèmes de connexion OBS

- Vérifiez que le plugin obs-websocket est correctement installé et activé
- Assurez-vous que le port n'est pas bloqué par un pare-feu
- Vérifiez que les identifiants de connexion dans `config.py` correspondent
- Lancez OBS avant de démarrer l'application Classify Audio Video
- Consultez les journaux de l'application pour identifier les problèmes de connexion spécifiques

### Problèmes avec les fichiers vidéo

- Assurez-vous que les formats des fichiers sont pris en charge par OBS (mp4, mov, avi, etc.)
- Vérifiez que les sources média sont correctement ajoutées et visibles dans OBS
- Si une analyse vidéo échoue, consultez les journaux d'OBS et de l'application
- Pour les vidéos longues, augmentez l'intervalle d'échantillonnage pour réduire le temps d'analyse

### Erreurs de classification

- Si le modèle de classification produit des résultats incorrects, essayez de réentraîner le modèle avec davantage de données
- Ajustez les seuils dans la méthode `_rule_based_classification` pour améliorer la précision

### Performances

- Pour les systèmes moins puissants, réduisez la résolution vidéo dans `config.py`
- Augmentez l'intervalle d'analyse pour réduire l'utilisation du CPU
- Pour l'analyse de fichiers vidéo, utilisez des valeurs d'échantillonnage plus élevées (10-30 secondes)

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
- [Chart.js](https://www.chartjs.org/)
