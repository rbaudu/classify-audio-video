# Système de gestion d'erreurs

L'application intègre un système complet de gestion d'erreurs pour améliorer la fiabilité et faciliter le débogage.

## Architecture d'erreurs

Le système est basé sur une hiérarchie d'exceptions personnalisées :

- **AppError** - Classe de base pour toutes les exceptions de l'application
  - **CaptureError** - Erreurs liées à la capture audio/vidéo
    - **OBSError** - Erreurs spécifiques à OBS
    - **AudioError** - Erreurs spécifiques à la capture audio
    - **SyncError** - Erreurs de synchronisation audio/vidéo
  - **AnalysisError** - Erreurs liées à l'analyse et la classification
    - **ClassificationError** - Erreurs spécifiques à la classification d'activité
  - **DatabaseError** - Erreurs liées à la base de données
  - **APIError** - Erreurs liées aux API
    - **ExternalServiceError** - Erreurs de communication avec les services externes
  - **ResourceError** - Erreurs liées aux ressources (fichiers, etc.)

## Codes d'erreur standardisés

Chaque type d'erreur est associé à un code unique via l'énumération `ErrorCode` :

- **Erreurs générales** (1-99) : `UNKNOWN_ERROR`, `CONFIG_ERROR`, `INITIALIZATION_ERROR`
- **Erreurs de capture** (100-199) : `OBS_CONNECTION_ERROR`, `AUDIO_DEVICE_ERROR`, `SYNC_ERROR`, etc.
- **Erreurs d'analyse** (200-299) : `ANALYSIS_DATA_ERROR`, `CLASSIFICATION_ERROR`, etc.
- **Erreurs de base de données** (300-399) : `DB_CONNECTION_ERROR`, `DB_QUERY_ERROR`, etc.
- **Erreurs d'API** (400-499) : `API_REQUEST_ERROR`, `EXTERNAL_SERVICE_ERROR`, etc.
- **Erreurs de ressources** (500-599) : `FILE_NOT_FOUND_ERROR`, `PERMISSION_ERROR`, etc.

## Fonctionnalités principales

Le système de gestion d'erreurs offre plusieurs avantages :

1. **Journalisation automatique** : Toutes les erreurs sont automatiquement enregistrées avec le niveau de détail approprié
2. **Messages contextuels** : Les erreurs incluent des détails sur le contexte dans lequel elles se sont produites
3. **Traçabilité** : Les exceptions d'origine sont conservées pour faciliter le débogage
4. **Format standardisé** : Les erreurs peuvent être facilement converties en JSON pour les API
5. **Récupération robuste** : L'application peut continuer à fonctionner malgré certaines erreurs non critiques

## Décorateurs d'erreurs

Deux décorateurs sont disponibles pour simplifier la gestion des erreurs :

1. **@handle_exceptions** : Pour les fonctions générales, attrape et enregistre les erreurs
   ```python
   @handle_exceptions
   def my_function():
       # Le code est protégé contre les exceptions
   ```

2. **@handle_route_exceptions** : Spécifique aux routes Flask, convertit les erreurs en réponses JSON
   ```python
   @app.route('/api/my-endpoint')
   @handle_route_exceptions
   def my_api_endpoint():
       # Les erreurs renvoient automatiquement une réponse JSON appropriée
   ```

## Pages d'erreur personnalisées

L'application fournit des pages d'erreur HTML personnalisées pour les erreurs courantes :
- **404.html** : Pour les ressources non trouvées
- **500.html** : Pour les erreurs serveur internes

## Gestion adaptative

Le système s'adapte au contexte de l'erreur :
- Pour les API, les erreurs sont renvoyées au format JSON avec un code HTTP approprié
- Pour l'interface web, des pages d'erreur conviviales sont affichées
- Pour les erreurs de connexion, des mécanismes de nouvelle tentative sont implémentés

## Utilisation dans le code

Exemple d'utilisation du système d'erreur :

```python
# Lever une erreur typée
def connect_to_obs():
    try:
        # Code de connexion à OBS
    except ConnectionError as e:
        raise OBSError(
            ErrorCode.OBS_CONNECTION_ERROR,
            "Impossible de se connecter à OBS Studio",
            details={"host": config.OBS_HOST, "port": config.OBS_PORT},
            original_exception=e
        )

# Gestion d'erreur avec récupération
@handle_exceptions
def process_video_frame():
    try:
        # Code principal de traitement
    except CaptureError as e:
        # Journalisation déjà gérée par le décorateur
        # Utilisation d'une stratégie de récupération
        return use_fallback_method()
```

## Correspondance entre codes d'erreur et codes HTTP

Le système mappe automatiquement les codes d'erreur de l'application aux codes de statut HTTP appropriés :

| Code d'erreur | Code HTTP | Description |
|---------------|-----------|-------------|
| `UNKNOWN_ERROR` | 500 | Erreur serveur interne |
| `OBS_CONNECTION_ERROR` | 503 | Service indisponible |
| `ANALYSIS_DATA_ERROR` | 400 | Requête incorrecte |
| `DB_CONNECTION_ERROR` | 503 | Service indisponible |
| `FILE_NOT_FOUND_ERROR` | 404 | Ressource non trouvée |
| `PERMISSION_ERROR` | 403 | Accès interdit |
| `EXTERNAL_SERVICE_ERROR` | 502 | Mauvaise passerelle |
| `RATE_LIMIT_ERROR` | 429 | Trop de requêtes |

## Journalisation des erreurs

Les erreurs sont journalisées avec différents niveaux de gravité :

- **ERROR** : Pour la plupart des erreurs standards
- **CRITICAL** : Pour les erreurs qui empêchent l'application de fonctionner
- **WARNING** : Pour les erreurs mineures ou les situations anormales

Le format de journalisation inclut :
- Code d'erreur et nom symbolique
- Message descriptif
- Détails contextuels (sous forme JSON)
- Exception d'origine (si disponible)
- Stack trace complet pour le débogage

## Avantages pour les utilisateurs et les développeurs

Ce système de gestion d'erreurs offre plusieurs avantages :

1. **Pour les utilisateurs** :
   - Messages d'erreur clairs et compréhensibles
   - Interface qui reste opérationnelle même en cas de problème
   - Pages d'erreur personnalisées qui expliquent le problème
   - Possibilité de réessayer automatiquement certaines opérations

2. **Pour les développeurs** :
   - Traçabilité complète des erreurs pour faciliter le débogage
   - Classification standardisée des erreurs pour faciliter l'analyse
   - Simplification de la gestion des erreurs grâce aux décorateurs
   - Flexibilité pour ajouter de nouveaux types d'erreurs ou codes spécifiques

## Mécanismes de reprise après erreur

L'application comprend plusieurs stratégies de reprise automatique après erreur :

1. **Reconnexion automatique à OBS** :
   - En cas de perte de connexion à OBS, l'application tente automatiquement de se reconnecter
   - Un mécanisme de backoff exponentiel évite la surcharge du serveur OBS
   - Après un certain nombre de tentatives, l'erreur est remontée à l'utilisateur

2. **Récupération des erreurs de base de données** :
   - Les transactions sont sécurisées avec des points de contrôle
   - En cas d'erreur d'écriture, l'application essaie de réutiliser la dernière connexion valide
   - Les problèmes d'intégrité sont détectés et signalés clairement

3. **Gestion des erreurs de services externes** :
   - Les données à envoyer sont mises en cache en cas d'échec de connexion
   - L'application retente l'envoi lors des prochains cycles d'analyse
   - Un mécanisme de file d'attente évite la perte de données

4. **Récupération des erreurs de capture** :
   - En cas d'erreur de capture audio, l'application peut basculer sur un autre périphérique
   - En cas d'erreur de capture vidéo, l'application utilise les dernières images valides
   - Les problèmes de synchronisation sont détectés et corrigés automatiquement si possible

## Implémentation technique

Le système de gestion d'erreurs est implémenté dans le fichier `server/utils/error_handling.py` qui contient :

1. **La classe `ErrorCode` (enum)** - Définit tous les codes d'erreur standardisés
2. **La classe `AppError`** - Classe de base pour toutes les exceptions
3. **Les classes d'erreurs spécifiques** - Héritant de `AppError` pour chaque type d'erreur
4. **Le décorateur `@handle_exceptions`** - Pour la gestion générique des erreurs
5. **Le décorateur `@handle_route_exceptions`** - Pour la gestion des erreurs dans les routes Flask
6. **La fonction `determine_http_status`** - Qui mappe les codes d'erreur aux statuts HTTP
7. **La fonction `log_exception`** - Pour la journalisation standardisée des exceptions

## Extension du système d'erreur

Pour ajouter un nouveau type d'erreur :

1. Ajoutez un nouveau code dans l'énumération `ErrorCode`
2. Créez une nouvelle classe d'exception qui hérite de la classe appropriée
3. Mettez à jour la fonction `determine_http_status` si nécessaire

Exemple :

```python
# Ajouter un nouveau code
class ErrorCode(Enum):
    # ...
    MODEL_VERSION_ERROR = 212

# Créer une nouvelle classe d'erreur
class ModelVersionError(ClassificationError):
    """Erreur spécifique aux versions de modèle incompatibles"""
    pass

# Utiliser la nouvelle erreur
def load_model(path):
    try:
        # Chargement du modèle
        if model_version < min_supported_version:
            raise ModelVersionError(
                ErrorCode.MODEL_VERSION_ERROR,
                f"Version de modèle non supportée: {model_version}",
                details={"path": path, "version": model_version}
            )
    except Exception as e:
        # ...
```
