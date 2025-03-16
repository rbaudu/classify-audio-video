# Guide de dépannage

Ce guide vous aidera à résoudre les problèmes courants que vous pourriez rencontrer lors de l'utilisation de Classify Audio Video.

## Problèmes de démarrage

### L'application ne démarre pas

1. **Erreur Python ou importation de modules**
   - Vérifiez que vous utilisez Python 3.8 ou supérieur : `python --version`
   - Assurez-vous que toutes les dépendances sont installées : `pip install -r requirements.txt`
   - Utilisez `pip list` pour vérifier que les modules importants (Flask, OpenCV, PyAudio, etc.) sont présents

2. **Erreur de permissions**
   - Vérifiez les droits d'accès aux dossiers de l'application, en particulier le dossier `data/`
   - Sur Linux/Mac : `chmod -R 755 data/`

3. **Erreur dans le fichier de configuration**
   - Vérifiez que le fichier `server/config.py` est correctement formaté
   - Assurez-vous que tous les chemins spécifiés existent

### Erreur "Port déjà utilisé"

```
OSError: [Errno 98] Address already in use
```

- Le port 5000 est peut-être déjà utilisé par une autre application
- Modifiez le port dans `server/main.py` ou `server/config.py`
- Ou terminez le processus qui utilise ce port (utilisez `netstat -tulpn | grep 5000` sur Linux)

## Problèmes de connexion OBS

### Impossible de se connecter à OBS

```
[OBS_CONNECTION_ERROR] Impossible de se connecter à OBS Studio
```

1. **Vérifications de base**
   - Assurez-vous qu'OBS est en cours d'exécution
   - Vérifiez que le plugin obs-websocket est correctement installé et activé
   - Confirmez que les paramètres WebSocket sont activés dans OBS (Outils > WebSockets Server Settings)

2. **Problèmes de configuration**
   - Vérifiez que l'hôte et le port dans `config.py` correspondent à vos paramètres OBS
   - Assurez-vous que le mot de passe est correct si vous en avez configuré un

3. **Problèmes réseau**
   - Vérifiez que le port n'est pas bloqué par un pare-feu
   - Si OBS est sur une autre machine, assurez-vous que les deux machines peuvent communiquer
   - Essayez de vous connecter à l'adresse IP explicite plutôt qu'à localhost

4. **Solution de contournement**
   - Redémarrez OBS et réessayez
   - Vérifiez la version d'OBS et du plugin obs-websocket pour vous assurer qu'ils sont compatibles

### Pas de flux vidéo depuis OBS

```
[OBS_STREAM_ERROR] Erreur lors de la récupération des images
```

1. **Source vidéo non configurée**
   - Vérifiez qu'une source vidéo est ajoutée et active dans OBS
   - Assurez-vous que la source est visible dans la prévisualisation d'OBS

2. **Format vidéo incompatible**
   - Essayez de changer le format vidéo dans OBS (Paramètres > Vidéo)
   - Formats recommandés : NV12 ou I420

3. **Résolution trop élevée**
   - Réduisez la résolution dans OBS pour diminuer la charge

## Problèmes audio

### Erreur PyAudio / Périphérique audio

```
[AUDIO_DEVICE_ERROR] Impossible d'initialiser le périphérique audio
```

1. **Vérification des périphériques**
   - Utilisez l'API `/api/audio-devices` pour lister les périphériques disponibles
   - Vérifiez que votre microphone est correctement connecté et détecté par le système

2. **Problèmes d'installation PyAudio**
   - Réinstallez PyAudio en suivant les instructions spécifiques à votre OS dans [INSTALLATION.md](INSTALLATION.md)
   - Sur Windows, essayez d'utiliser un fichier wheel précompilé

3. **Pilotes audio**
   - Mettez à jour les pilotes audio de votre système
   - Essayez un autre périphérique audio si disponible

### Problèmes de synchronisation audio/vidéo

1. **Décalage entre l'audio et la vidéo**
   - Ajustez `AUDIO_VIDEO_SYNC_BUFFER_SIZE` dans `config.py` pour augmenter/diminuer la taille du buffer
   - Valeur par défaut : 10, essayez avec 5 ou 20 selon le sens du décalage

2. **Charge CPU élevée**
   - Réduisez la résolution vidéo et la fréquence d'images dans OBS
   - Augmentez `AUDIO_CHUNK_SIZE` dans `config.py` pour réduire la charge de traitement

## Problèmes de base de données

### Erreur d'accès à la base de données

```
[DB_CONNECTION_ERROR] Impossible d'accéder à la base de données
```

1. **Vérifications de base**
   - Assurez-vous que le dossier `data/` existe
   - Vérifiez les permissions du dossier et des fichiers

2. **Base de données corrompue**
   - Sauvegardez `activity.db` si elle contient des données importantes
   - Supprimez le fichier pour permettre à l'application d'en créer un nouveau

### Erreurs d'intégrité ou de requête

```
[DB_INTEGRITY_ERROR] Violation de contrainte d'intégrité
```

- Cela peut se produire si le schéma de base de données a changé
- Sauvegardez vos données et supprimez la base de données pour recréer un schéma propre

## Problèmes avec les fichiers vidéo

### Impossible de charger un fichier vidéo

1. **Format non supporté**
   - Vérifiez que le format est pris en charge par OBS (mp4, mov, avi, etc.)
   - Convertissez le fichier dans un format compatible

2. **Problèmes de chemin**
   - Évitez les caractères spéciaux dans les noms de fichiers
   - Utilisez des chemins absolus dans OBS

### Échec d'analyse vidéo

```
[ANALYSIS_PROCESSING_ERROR] Erreur pendant l'analyse vidéo
```

1. **Vidéo trop longue ou trop grande**
   - Essayez avec une vidéo plus courte ou de plus petite résolution
   - Augmentez l'intervalle d'échantillonnage pour l'analyse complète

2. **Problèmes de mémoire**
   - Fermez d'autres applications pour libérer de la RAM
   - Redémarrez l'application

## Problèmes de classification

### Classification incorrecte ou peu fiable

1. **Vérification du modèle**
   - Assurez-vous que le modèle de classification (`models/activity_classifier.h5`) est correctement installé
   - Si vous utilisez la classification basée sur des règles, ajustez les seuils dans `activity_classifier.py`

2. **Conditions d'enregistrement**
   - Améliorez l'éclairage pour une meilleure analyse vidéo
   - Réduisez le bruit ambiant pour l'analyse audio

3. **Recalibration**
   - Utilisez l'onglet "Test du modèle" pour vérifier la classification dans différentes conditions
   - Ajustez votre position par rapport à la caméra

## Problèmes d'API externe

### Échec de communication avec le service externe

```
[EXTERNAL_SERVICE_ERROR] Impossible d'envoyer les données
```

1. **Vérification de la configuration**
   - Assurez-vous que l'URL et la clé API dans `config.py` sont correctes
   - Vérifiez la connectivité Internet

2. **Problèmes de format de données**
   - Vérifiez que le format des données envoyées correspond à ce qu'attend l'API externe
   - Consultez les logs pour les détails des erreurs

3. **Limitations de l'API**
   - Vérifiez si vous avez atteint une limite de taux ou de quota

## Problèmes de performance

### Application lente ou gelée

1. **Utilisation CPU élevée**
   - Réduisez la résolution et la fréquence d'images dans OBS
   - Augmentez l'intervalle d'analyse dans `config.py`
   - Fermez les applications inutiles en arrière-plan

2. **Fuites mémoire**
   - Redémarrez l'application périodiquement
   - Vérifiez que `temp_captures/` et `analyses/` ne sont pas pleins de fichiers temporaires

### Journaux volumineux

- Les journaux sont stockés dans `activity_classifier.log`
- Vous pouvez ajuster le niveau de journalisation dans `server/main.py`
- Nettoyez régulièrement les anciens journaux

## Problèmes avec les tests unitaires

### Échec des tests

```
FAILED: test_api_routes.TestAPIRoutes.test_get_current_activity
```

1. **Dépendances manquantes**
   - Assurez-vous que toutes les dépendances de développement sont installées

2. **Configuration de test incorrecte**
   - Vérifiez que vous êtes dans le dossier racine du projet
   - Certains tests peuvent nécessiter des mocks ou des configurations spécifiques

3. **Modification du code**
   - Si vous avez modifié le code, certains tests peuvent échouer
   - Mettez à jour les tests pour qu'ils correspondent à vos changements

## Journalisation et débogage

### Activer la journalisation détaillée

Modifiez le niveau de journalisation dans `server/main.py` :

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changez INFO en DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("activity_classifier.log")
    ]
)
```

### Mode debug Flask

Lancez l'application en mode debug pour plus d'informations :

```bash
# Dans run.py, modifiez app.run(debug=False) en app.run(debug=True)
python run.py
```

### Débogage de routes spécifiques

Ajoutez des points de journalisation dans le code pour déboguer des routes spécifiques :

```python
@app.route('/api/problematic-route')
def problematic_route():
    app.logger.debug("Entrée dans la route problématique")
    # Votre code ici
    app.logger.debug(f"Valeurs intermédiaires: {some_variable}")
    # Plus de code
    return jsonify(result)
```

## Assistance supplémentaire

Si vous ne parvenez pas à résoudre votre problème, vous pouvez :

1. Ouvrir une issue sur [GitHub](https://github.com/rbaudu/classify-audio-video/issues)
2. Joindre les logs pertinents et une description détaillée du problème
3. Mentionner votre environnement (OS, version Python, version OBS)
