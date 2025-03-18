# Migration vers OBS 31.0.2+ avec OBS31Capture

## Introduction

Ce projet inclut désormais un support intégré pour OBS Studio 31.0.2+ avec WebSocket 5.5.5+. Cette mise à jour est nécessaire car les versions récentes d'OBS Studio ont modifié leur API WebSocket, rendant incompatible l'ancienne implémentation `OBSCapture`.

## Nouveautés

- **Nouvelle classe `OBS31Capture`** : Implémentation optimisée pour OBS 31.0.2+
- **Classes auxiliaires** : `OBS31EventHandler`, `OBS31MediaManager`, `OBS31SourceManager`
- **Adaptateur unifié** : `OBS31Adapter` pour simplifier l'usage de toutes les fonctionnalités
- **Outils de migration** : Script `migrate_to_obs31.py` pour faciliter la transition
- **Exemples d'utilisation** : Dans le dossier `examples/`
- **Guide complet** : Consultez `docs/migration_obs31.md`

## Compatibilité

Cette nouvelle implémentation est compatible avec :
- OBS Studio 31.0.2 et versions ultérieures
- Plugin WebSocket version 5.5.5 et ultérieures

## Installation rapide

```bash
# Installer les dépendances requises
python install_requirements.py
```

## Utilisation rapide

```python
# Avant (ancienne approche)
from server.capture.obs_capture import OBSCapture
obs = OBSCapture()

# Maintenant (nouvelle approche)
from server.capture.obs_31_capture import OBS31Capture
obs = OBS31Capture()

# Ou mieux encore, utilisez l'adaptateur
from server.capture.obs_31_adapter import OBS31Adapter
obs = OBS31Adapter()
```

## Comment migrer ?

1. **Option 1 - Migration automatique** :
   ```bash
   # Analyser votre code et appliquer les modifications
   python server/capture/migrate_to_obs31.py votre/dossier --apply
   ```

2. **Option 2 - Migration manuelle** :
   Modifiez vos imports selon le guide de migration détaillé dans `docs/migration_obs31.md`.

## Tester votre installation

```bash
# Vérifier que tout fonctionne correctement avec votre installation OBS
python tests/test_obs_31_capture.py

# Exécuter un exemple complet
python examples/use_obs31.py
```

## Documentation

- **Guide de migration complet** : `docs/migration_obs31.md`
- **Exemples d'utilisation** : `examples/use_obs31.py`
- **Code source** : 
  - `server/capture/obs_31_capture.py` (classe principale)
  - `server/capture/obs_31_adapter.py` (adaptateur unifié)
  - `server/capture/obs_events_31.py` (gestion des événements)
  - `server/capture/obs_media_31.py` (contrôle des médias)
  - `server/capture/obs_sources_31.py` (gestion des sources)
  - `server/capture/migrate_to_obs31.py` (outil de migration)

## Problèmes fréquents

### "OBS n'est pas détecté ou erreur de connexion"

Vérifiez que :
1. OBS Studio est en cours d'exécution
2. Le plugin WebSocket est activé (dans OBS : Outils > WebSocket Server Settings)
3. Vous utilisez OBS Studio 31.0.2 ou ultérieur

### "Erreur d'importation de module"

Exécutez `python install_requirements.py` pour installer les dépendances requises.

## Remarques importantes

- **Sauvegardez** toujours votre code avant d'appliquer la migration automatique
- L'ancienne implémentation `OBSCapture` reste disponible pour la compatibilité avec les anciennes versions d'OBS, mais ne recevra plus de mises à jour
- Pour les projets complexes, privilégiez l'utilisation de `OBS31Adapter`

## Contribuer

Si vous rencontrez des problèmes spécifiques à votre configuration ou souhaitez améliorer cette implémentation, n'hésitez pas à ouvrir une issue ou une pull request.
