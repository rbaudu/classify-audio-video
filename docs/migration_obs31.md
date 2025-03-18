# Guide de migration vers OBS31Capture

Ce guide explique comment migrer votre code existant utilisant OBSCapture vers la nouvelle implémentation OBS31Capture qui est compatible avec OBS Studio 31.0.2+ et WebSocket 5.5.5+.

## Pourquoi migrer ?

La nouvelle implémentation OBS31Capture offre plusieurs avantages :

- **Compatibilité** : Fonctionne avec OBS Studio 31.0.2 et versions ultérieures
- **Performance** : Code optimisé pour les nouvelles API WebSocket
- **Stabilité** : Gestion améliorée des erreurs et des reconnexions
- **Maintenabilité** : Structure modulaire pour faciliter les évolutions futures

## Options de migration

Vous avez plusieurs options pour migrer votre code, selon vos besoins :

### Option 1 : Remplacement direct (le plus simple)

Modifiez simplement vos imports pour utiliser OBS31Capture au lieu de OBSCapture :

```python
# Avant
from server.capture.obs_capture import OBSCapture

# Après
from server.capture.obs_31_capture import OBS31Capture as OBSCapture  # Compatible OBS 31.0.2+
```

Cette approche est la plus simple et fonctionne dans la plupart des cas car OBS31Capture implémente la même interface que OBSCapture.

### Option 2 : Utiliser l'adaptateur (recommandé pour les utilisations complexes)

Si votre code utilise des fonctionnalités avancées comme les événements, le contrôle des médias ou les sources, utilisez l'adaptateur qui regroupe toutes ces fonctionnalités :

```python
# Avant
from server.capture.obs_capture import OBSCapture
from server.capture.obs_events import OBSEventsMixin
from server.capture.obs_media import OBSMediaMixin

# Après
from server.capture.obs_31_adapter import OBS31Adapter

# Au lieu de créer plusieurs instances
# obs = OBSCapture()
# Vous créez simplement une instance de l'adaptateur
obs = OBS31Adapter()  # Qui fournit les mêmes méthodes et attributs
```

L'adaptateur fournit une interface unifiée pour toutes les fonctionnalités, simplifiant votre code.

### Option 3 : Utiliser l'outil de migration automatique

Un script utilitaire `migrate_to_obs31.py` est fourni pour faciliter la migration :

```bash
# Analyser un répertoire et générer un rapport de migration
python server/capture/migrate_to_obs31.py /chemin/vers/votre/projet

# Analyser et appliquer automatiquement les modifications (crée des sauvegardes)
python server/capture/migrate_to_obs31.py /chemin/vers/votre/projet --apply
```

## Dépendances requises

Assurez-vous d'installer les dépendances à jour pour OBS31Capture :

```bash
# Installer les dépendances requises
python install_requirements.py
```

Cela installe notamment `obsws-python>=1.4.0` qui est nécessaire pour la communication avec OBS 31.0.2+.

## Changements dans l'API

### Méthodes compatibles

La plupart des méthodes sont identiques et fonctionnent de la même manière :

- `capture_frame(source_name=None)`
- `start_capture(source_name=None, interval=0.1)`
- `stop_capture()`
- `get_current_frame()`
- `get_frame_as_jpeg(quality=85)`
- `enable_test_images(enable=True)`
- `disconnect()`

### Nouveautés et améliorations

La nouvelle implémentation apporte quelques améliorations :

1. **Meilleure gestion des erreurs** : OBS31Capture récupère automatiquement en cas d'erreur de capture
2. **Compatibilité avec les futures versions** : L'architecture est conçue pour évoluer avec les futures versions d'OBS
3. **Mode de test amélioré** : Les images de test sont plus détaillées et personnalisables
4. **Adaptateur unifié** : OBS31Adapter simplifie l'usage des différentes fonctionnalités

## Exemples d'utilisation

### Exemple simple

```python
from server.capture.obs_31_capture import OBS31Capture

# Créer une instance
obs = OBS31Capture()

# Activer le mode de test (optionnel)
obs.enable_test_images(True)

# Capturer une image
if obs.video_sources:
    frame = obs.capture_frame(obs.video_sources[0])
    if frame:
        # Traiter l'image...
        frame.save("capture.png")

# Déconnecter
obs.disconnect()
```

### Exemple avec l'adaptateur

```python
from server.capture.obs_31_adapter import OBS31Adapter

# Créer l'adaptateur
adapter = OBS31Adapter()

# Il fournit un accès unifié à toutes les fonctionnalités
print(f"Sources vidéo: {adapter.video_sources}")
print(f"Sources média: {adapter.media_sources}")

# Enregistrer un callback pour les événements
adapter.register_event_callback('scene_changed', lambda data: print(f"Scène changée: {data['scene_name']}"))

# Contrôler un média si disponible
if adapter.media_sources:
    adapter.control_media(adapter.media_sources[0], 'play')

# Capturer des images
frame = adapter.capture_frame()
```

## Migration des composants spécifiques

### Événements

Si vous utilisiez les événements OBS :

```python
# Avant
from server.capture.obs_events import OBSEventsMixin

# Après
from server.capture.obs_events_31 import OBS31EventHandler

# Création et utilisation
events = OBS31EventHandler()
events.register_callback('scene_changed', my_callback_function)
```

### Médias

Si vous utilisiez le contrôle des médias :

```python
# Avant
from server.capture.obs_media import OBSMediaMixin

# Après
from server.capture.obs_media_31 import OBS31MediaManager

# Création et utilisation
media = OBS31MediaManager()
media.get_media_sources()
media.control_media('ma_source', 'play')
```

### Sources

Si vous utilisiez la gestion avancée des sources :

```python
# Avant
from server.capture.obs_sources import OBSSourcesMixin

# Après
from server.capture.obs_sources_31 import OBS31SourceManager

# Création et utilisation
sources = OBS31SourceManager()
sources.capture_screenshot('ma_source')
```

## Problèmes connus et solutions

### Problème : Erreur "Name 'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY' is not defined"

**Solution** : Assurez-vous d'avoir installé `obsws-python>=1.4.0` avec `python install_requirements.py`

### Problème : La capture d'image échoue avec OBS Studio 31.0.2

**Solution** : Vérifiez que le plugin WebSocket est activé dans OBS Studio :
1. Ouvrez OBS Studio
2. Allez dans "Outils" > "WebSocket Server Settings"
3. Assurez-vous que "Enable WebSocket Server" est coché

## Tests

Pour vérifier que votre installation fonctionne correctement avec OBS31Capture :

```bash
# Exécuter les tests de base
python tests/test_obs_31_capture.py

# Exécuter un exemple complet
python examples/use_obs31.py
```

## Besoin d'aide ?

Si vous rencontrez des problèmes pendant la migration :

1. Consultez les messages d'erreur détaillés dans les logs
2. Vérifiez que votre version d'OBS Studio est bien 31.0.2 ou supérieure
3. Examinez le rapport généré par l'outil de migration pour des suggestions spécifiques
4. N'hésitez pas à ouvrir une issue sur GitHub pour obtenir de l'aide

## Conclusion

La migration vers OBS31Capture est une étape importante pour assurer la compatibilité avec les versions récentes d'OBS Studio. Bien que cela nécessite quelques modifications dans votre code, les avantages en termes de stabilité et de performances en valent la peine.
