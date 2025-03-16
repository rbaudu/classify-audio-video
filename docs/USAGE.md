# Guide d'utilisation

Ce guide détaille les différentes fonctionnalités de Classify Audio Video et comment les utiliser efficacement.

## Démarrage de l'application

1. Lancez l'application (utiliser toujours le fichier run.py) :
```bash
python run.py
```

2. Accédez à l'interface web via votre navigateur :
```
http://localhost:5000
```

L'application commencera automatiquement à :
- Se connecter à OBS Studio pour la vidéo
- Capturer l'audio via PyAudio (microphone par défaut)
- Synchroniser les flux audio et vidéo
- Analyser et classifier l'activité toutes les 5 minutes
- Envoyer les résultats au service externe configuré

## Interface web

### Page d'accueil

La page d'accueil (`/`) fournit une vue d'ensemble de l'application avec :
- L'état actuel de la connexion à OBS
- L'état de la capture audio
- L'activité actuellement détectée
- Les statistiques de base sur les activités récentes

### Tableau de bord

Le tableau de bord (`/dashboard`) affiche :
- Un flux vidéo en direct
- L'analyse audio en temps réel
- L'activité détectée en cours
- Des graphiques de confiance pour chaque type d'activité

### Statistiques d'activité

La page de statistiques (`/statistics`) présente :
- Des graphiques de répartition des activités sur différentes périodes
- Des tendances d'activité au fil du temps
- Des rapports comparatifs entre différentes périodes
- La possibilité d'exporter les données

### Historique des activités

La page d'historique (`/history`) permet de :
- Consulter un journal chronologique de toutes les activités détectées
- Filtrer par type d'activité, date ou niveau de confiance
- Accéder aux détails complets de chaque analyse
- Exporter l'historique en CSV ou JSON

### Test du modèle

La page de test du modèle (`/model-testing`) offre :
- Un mode de classification manuelle d'images actuelles
- La possibilité de tester différents paramètres de classification
- L'analyse de fichiers vidéo chargés dans OBS

## Fonctionnalités principales

### Capture et analyse en temps réel

L'application capture et analyse en continu les flux audio et vidéo :
1. Les images sont capturées depuis OBS toutes les 100-200ms
2. L'audio est capturé en continu via PyAudio
3. Les flux sont synchronisés et analysés pour extraire des caractéristiques pertinentes
4. L'activité est classifiée toutes les 5 minutes (paramètre configurable)
5. Les résultats sont stockés dans la base de données et envoyés au service externe

### Modification du périphérique audio

Pour changer le périphérique audio utilisé pour la capture :

1. **Via l'interface web**
   - Accédez à "Paramètres" > "Audio" dans le menu principal
   - Sélectionnez le périphérique souhaité dans la liste déroulante
   - Cliquez sur "Appliquer" pour effectuer le changement

2. **Via l'API**
   - Accédez à `/api/audio-devices` pour obtenir la liste des périphériques disponibles
     ```bash
     curl http://localhost:5000/api/audio-devices
     ```
   - Utilisez l'API `/api/set-audio-device` en fournissant l'index du périphérique souhaité
     ```bash
     curl -X POST http://localhost:5000/api/set-audio-device -H "Content-Type: application/json" -d '{"device_index": 2}'
     ```

### Analyse de fichiers vidéo

Pour analyser des fichiers vidéo préalablement chargés dans OBS :

1. **Préparation dans OBS**
   - Ajoutez votre fichier vidéo comme "Source multimédia" dans OBS
   - Assurez-vous que la source est visible dans la scène active

2. **Analyse d'une image spécifique**
   - Accédez à l'onglet "Test du modèle" dans l'interface web
   - Basculez vers l'onglet "Fichiers vidéo"
   - Sélectionnez la source média dans la liste déroulante
   - Utilisez les contrôles de lecture pour naviguer dans la vidéo
   - Cliquez sur "Analyser cette image" pour classifier l'image actuellement visible

3. **Analyse complète de la vidéo**
   - Suivez les étapes 1 et 2 ci-dessus
   - Cliquez sur "Analyser la vidéo complète"
   - L'application échantillonnera la vidéo à intervalles réguliers
   - Vous serez redirigé vers une page de suivi de progression
   - Une fois l'analyse terminée, les résultats seront affichés avec des graphiques

### Exportation des résultats d'analyse

Après avoir analysé une vidéo ou accumulé des données d'activité, vous pouvez exporter les résultats :

1. **Format CSV**
   - Idéal pour l'analyse dans des tableurs (Excel, Google Sheets)
   - Contient toutes les données dans un format tabulaire
   - Colonnes détaillées incluant horodatage, type d'activité, niveau de confiance, etc.

2. **Format JSON**
   - Pour l'intégration avec d'autres applications
   - Format plus riche avec structure complète des données
   - Inclut toutes les métadonnées et détails d'analyse

Pour exporter les données :
- Depuis la page de résultats d'analyse vidéo, cliquez sur le bouton "Exporter en CSV" ou "Exporter en JSON"
- Depuis la page d'historique, sélectionnez la période souhaitée puis cliquez sur "Exporter"

### Sauvegarde de clips synchronisés

Pour sauvegarder des clips audio/vidéo synchronisés pour analyse ultérieure :

1. **Via l'interface web**
   - Accédez à l'onglet "Clips" dans l'interface web
   - Définissez la durée du clip (1-30 secondes)
   - Cliquez sur "Capturer un clip"
   - Le clip sera enregistré dans le dossier `data/temp_captures/`

2. **Via l'API**
   - Utilisez l'API `/api/save-clip` pour enregistrer un clip
     ```bash
     curl -X POST http://localhost:5000/api/save-clip -H "Content-Type: application/json" -d '{"duration": 5}'
     ```

## API REST

L'application fournit plusieurs API RESTful pour l'intégration avec d'autres systèmes :

### Activité actuelle

```
GET /api/current-activity
```

Retourne l'activité actuellement détectée au format JSON :
```json
{
  "timestamp": "2023-09-15T14:32:45",
  "activity": "reading",
  "confidence": 0.87,
  "details": {
    "movement_level": 0.2,
    "sound_level": 0.1,
    "confidence_scores": {
      "sleeping": 0.05,
      "eating": 0.03,
      "reading": 0.87,
      "on_phone": 0.02,
      "conversation": 0.01,
      "occupied": 0.01,
      "inactive": 0.01
    }
  }
}
```

### Historique des activités

```
GET /api/activity-history?start=2023-09-01&end=2023-09-15&limit=100
```

Retourne l'historique des activités dans la période spécifiée, avec des paramètres optionnels :
- `start` : Date de début (format YYYY-MM-DD)
- `end` : Date de fin (format YYYY-MM-DD)
- `limit` : Nombre maximum d'entrées à retourner
- `activity` : Filtrer par type d'activité
- `min_confidence` : Niveau de confiance minimum

### Périphériques audio disponibles

```
GET /api/audio-devices
```

Retourne la liste des périphériques audio disponibles :
```json
{
  "devices": [
    {
      "index": 0,
      "name": "Microphone (Realtek Audio)",
      "default": true,
      "channels": 2
    },
    {
      "index": 1,
      "name": "Webcam Microphone (USB Audio Device)",
      "default": false,
      "channels": 1
    }
  ],
  "current_device_index": 0
}
```

### Changer de périphérique audio

```
POST /api/set-audio-device
```

Corps de la requête :
```json
{
  "device_index": 1
}
```

Réponse :
```json
{
  "success": true,
  "message": "Périphérique audio changé avec succès",
  "device": {
    "index": 1,
    "name": "Webcam Microphone (USB Audio Device)"
  }
}
```

### Sauvegarde de clip

```
POST /api/save-clip
```

Corps de la requête :
```json
{
  "duration": 5,
  "filename": "test_clip"  // Optionnel
}
```

Réponse :
```json
{
  "success": true,
  "message": "Clip enregistré avec succès",
  "filepath": "data/temp_captures/test_clip_20230915_143245.mp4"
}
```

### Analyse d'une image

```
POST /api/analyze-frame
```

Corps de la requête (pour une source média OBS) :
```json
{
  "source_name": "VideoTest"
}
```

Réponse :
```json
{
  "activity": "reading",
  "confidence": 0.87,
  "details": {
    "movement_level": 0.2,
    "sound_level": 0.1,
    "confidence_scores": {
      "sleeping": 0.05,
      "eating": 0.03,
      "reading": 0.87,
      "on_phone": 0.02,
      "conversation": 0.01,
      "occupied": 0.01,
      "inactive": 0.01
    }
  }
}
```

## Utilisation avancée

### Configuration OBS optimale

Pour une meilleure performance de classification, configurez OBS avec ces paramètres :

- **Résolution** : 640x480 ou 720p (1280x720)
- **FPS** : 15-30 est suffisant pour l'analyse d'activité
- **Format vidéo** : NV12 ou I420

### Ajustement des intervalles d'analyse

L'application analyse l'activité par défaut toutes les 5 minutes (300 secondes). Vous pouvez modifier ce paramètre dans le fichier `server/config.py` :

```python
ANALYSIS_INTERVAL = 300  # 5 minutes en secondes
```

Utilisez une valeur plus basse pour une détection plus rapide des changements d'activité, ou une valeur plus élevée pour réduire la charge système.

### Mode silencieux

Pour exécuter l'application sans interface utilisateur (par exemple, sur un serveur headless) :

```bash
python run.py --headless
```

Dans ce mode, l'application :
- Démarre toutes les fonctions de capture et d'analyse
- Expose toutes les API REST
- N'affiche pas d'interface web
- Enregistre plus d'informations dans les journaux

### Gestion de la base de données

L'application utilise SQLite pour stocker les données d'analyse. Le fichier de base de données se trouve à `data/activity.db`.

Vous pouvez :
- **Sauvegarder** : Copiez simplement le fichier `activity.db`
- **Restaurer** : Remplacez le fichier existant par votre sauvegarde
- **Nettoyer** : Supprimez le fichier pour que l'application crée une nouvelle base de données vide
- **Explorer** : Utilisez un outil comme SQLite Browser pour examiner les données

### Intégration avec d'autres services

L'application peut envoyer les résultats d'analyse à un service externe. Par défaut, elle envoie les données via une requête HTTP POST. Vous pouvez configurer :

1. **Destination** : Modifiez `EXTERNAL_API_URL` dans `config.py`
2. **Format des données** : Ajustez la méthode `format_data_for_external_service()` dans `external_service.py`
3. **Authentification** : Configurez `EXTERNAL_API_KEY` ou d'autres paramètres selon les besoins de votre service

Exemple d'intégration personnalisée :
```python
# Dans server/api/external_service.py
def send_results(activity_data):
    # Formatage des données
    formatted_data = format_data_for_external_service(activity_data)
    
    # Ajout d'authentification
    headers = {
        "Authorization": f"Bearer {config.EXTERNAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Envoi des données
    try:
        response = requests.post(
            config.EXTERNAL_API_URL,
            json=formatted_data,
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        return True
    except Exception as e:
        # Gestion des erreurs avec notre système standardisé
        raise ExternalServiceError(
            ErrorCode.EXTERNAL_SERVICE_ERROR,
            "Erreur lors de l'envoi des données au service externe",
            details={"url": config.EXTERNAL_API_URL},
            original_exception=e
        )
```

## Arrêt propre de l'application

Pour arrêter l'application correctement :

1. Appuyez sur `Ctrl+C` dans le terminal où l'application s'exécute
2. L'application effectuera un arrêt propre :
   - Arrêt de la boucle d'analyse
   - Fermeture des connexions OBS et PyAudio
   - Enregistrement de l'état actuel dans la base de données
   - Libération des ressources

Si l'application ne s'arrête pas proprement, attendez quelques secondes et appuyez à nouveau sur `Ctrl+C`.

## Mises à jour et maintenance

### Mise à jour de l'application

Pour mettre à jour l'application vers la dernière version :

```bash
# Dans le répertoire du projet
git pull
pip install -r requirements.txt
```

### Maintenance périodique

Pour maintenir des performances optimales :

1. **Nettoyage des fichiers temporaires** :
   ```bash
   # Supprimez les anciens clips et analyses
   find data/temp_captures -type f -mtime +30 -delete
   find data/analyses -type f -mtime +30 -delete
   ```

2. **Optimisation de la base de données** :
   ```bash
   # Utilisez l'utilitaire sqlite3
   sqlite3 data/activity.db 'VACUUM;'
   ```

3. **Rotation des journaux** :
   ```bash
   # Créez une archive des anciens journaux
   mv activity_classifier.log activity_classifier.log.old
   ```
