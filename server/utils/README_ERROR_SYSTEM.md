# Système de Gestion d'Erreurs

Ce document décrit le système de gestion d'erreurs avancé implémenté dans le projet classify-audio-video.

## À propos du système

Le système de gestion d'erreurs est conçu pour :

1. Standardiser la gestion des erreurs à travers l'application
2. Améliorer la tolérance aux pannes et la récupération automatique
3. Fournir une meilleure visibilité sur les erreurs via des logs structurés
4. Permettre des alertes configurable pour les erreurs critiques
5. Intégrer des patterns comme Circuit Breaker et Retry

## Structure du système

Le système de gestion d'erreurs est divisé en plusieurs modules :

- `error_handling.py` : Base du système avec les classes d'exception et codes d'erreur
- `error_enums.py` : Énumérations pour les alertes et états des circuit breakers
- `error_monitor.py` : Surveillance et statistiques des erreurs
- `health_check.py` : Vérifications de santé de l'application
- `circuit_breaker.py` : Implémentation du pattern Circuit Breaker
- `retry.py` : Mécanismes de retry avec backoff
- `error_system.py` : Point d'entrée et intégration des fonctionnalités

## Utilisation

### Initialisation

Le système doit être initialisé au démarrage de l'application :

```python
from server.utils.error_system import init_error_system

# Au démarrage de l'application
init_error_system()
```

### Exceptions standardisées

Utilisez `AppError` et `ErrorCode` pour des exceptions standardisées :

```python
from server.utils.error_handling import AppError, ErrorCode

# Lever une exception standardisée
raise AppError(
    ErrorCode.DB_CONNECTION_ERROR,
    "Impossible de se connecter à la base de données",
    details={"host": "localhost", "port": 5432}
)
```

### Décorateurs pour la gestion d'erreurs

#### Enhanced Error Handling

Protection simple d'une fonction :

```python
from server.utils.error_system import enhanced_error_handling

@enhanced_error_handling(error_code=ErrorCode.ANALYSIS_PROCESSING_ERROR)
def process_data(data):
    # Traitement qui peut échouer
    pass
```

#### Circuit Breaker

Pour protéger des appels à des services externes :

```python
from server.utils.error_system import with_circuit_breaker

@with_circuit_breaker(name="external-api")
def call_api():
    # Appel à un service externe
    pass
```

#### Retry

Pour réessayer automatiquement des opérations :

```python
from server.utils.error_system import retry_with_circuit_breaker

@retry_with_circuit_breaker(name="database", max_retries=3)
def save_to_database(data):
    # Opération qui peut échouer temporairement
    pass
```

### Gestionnaires de contexte

#### Error Boundary

Délimitez des blocs de code pour isoler les erreurs :

```python
from server.utils.error_system import error_boundary

with error_boundary("processing-batch", error_code=ErrorCode.ANALYSIS_DATA_ERROR):
    # Code qui peut échouer
    pass
```

#### Transaction Boundary

Pour les opérations atomiques avec rollback :

```python
from server.utils.error_system import transaction_boundary

def rollback_function(error):
    # Logique de rollback
    pass

with transaction_boundary("db-transaction", on_error_callback=rollback_function) as tx:
    # Opérations atomiques
    tx['data']['progress'] = 50  # Stockage de l'état
```

### Health Checks

Pour surveiller l'état de santé des composants :

```python
from server.utils.health_check import health_check

# Enregistrer une vérification personnalisée
health_check.register_check("custom-service", lambda: check_service_status())

# Exécuter toutes les vérifications
results = health_check.run_all_checks()

# Obtenir le statut de santé global
status = health_check.get_health_status()
```

## Exemple complet

Voir le fichier `server/examples/error_system_example.py` pour un exemple complet d'utilisation du système.

## Bonnes pratiques

1. **Utilisez les codes d'erreur standardisés** définis dans `ErrorCode` pour catégoriser les erreurs
2. **Incluez des détails utiles** dans les exceptions pour faciliter le débogage
3. **Utilisez les boundaries d'erreur** pour isoler les parties critiques du code
4. **Appliquez Circuit Breaker** pour les services externes non fiables
5. **Configurez les retries avec backoff** pour les opérations qui peuvent échouer temporairement

## Extension du système

Pour ajouter de nouveaux codes d'erreur :

1. Ajoutez-les à l'énumération `ErrorCode` dans `error_handling.py`
2. Mettez à jour la fonction `determine_http_status` si nécessaire pour mapper les nouveaux codes

Pour ajouter de nouvelles vérifications de santé :

1. Créez une fonction de vérification qui renvoie un booléen
2. Enregistrez-la avec `health_check.register_check()`
3. Ajoutez-la à la fonction `register_health_checks` dans `health_check.py`
