# Guide de correction des problèmes du serveur

Ce document explique comment résoudre les problèmes rencontrés avec le serveur classify-audio-video, spécifiquement:

1. L'interface web qui ne se lance pas
2. L'impossibilité d'arrêter le serveur avec CTRL+C

## Solution recommandée: Scripts d'isolation

Pour diagnostiquer et résoudre les problèmes, j'ai créé plusieurs scripts qui isolent différentes parties du système:

### 1. `flask_server_only.py`

Ce script démarre uniquement la partie Flask de l'application, sans initialiser les composants de capture OBS et audio:

```bash
python flask_server_only.py
```

**Avantages**:
- Détermine si le problème vient de Flask ou des autres composants
- Ouvre automatiquement un navigateur vers une page de test
- Logs détaillés dans `flask_server.log`

### 2. `debug_flask.py`

Ce script crée une application Flask minimale indépendante de votre code pour tester si Flask fonctionne correctement:

```bash
python debug_flask.py
```

**Avantages**:
- Application Flask complètement isolée
- Logs détaillés dans `flask_debug.log`
- Permet de vérifier si le problème est lié à votre code ou à l'environnement

## Solution alternative: Script de correction manuelle

J'ai également créé un script qui applique automatiquement des correctifs aux fichiers problématiques:

```bash
python patch_server.py
```

**Ce script**:
1. Sauvegarde les fichiers originaux avec l'extension `.bak`
2. Remplace `os._exit(0)` par `sys.exit(0)` dans `run.py`
3. Change `daemon=True` en `daemon=False` pour le thread Flask dans `run.py`
4. Ajoute une route de test `/flask-test` dans `flask_app.py`
5. Crée les templates manquants si nécessaire

## Solution radicale: `kill_and_start.py`

Si les autres approches ne fonctionnent pas, le script radical `kill_and_start.py` offre une solution garantie:

```bash
# Démarrer le serveur
python kill_and_start.py

# Arrêter le serveur
python kill_and_start.py stop
```

Ce script:
1. Tue tous les processus Python en cours
2. Démarre le serveur en arrière-plan
3. Ouvre un navigateur vers l'interface
4. Capture les logs dans des fichiers séparés

## Diagnostics et causes probables

Voici les causes possibles des problèmes rencontrés:

### Problème d'arrêt CTRL+C

1. **Utilisation de `os._exit(0)`** qui ne permet pas aux threads de se nettoyer correctement
2. **Thread Flask configuré en daemon** qui est automatiquement tué sans nettoyage quand le thread principal se termine

### Problème d'interface web

1. **Templates manquants ou problèmes d'accès aux dossiers**
2. **Conflit de ports** où un autre processus utilise déjà le port 5000
3. **Problème de configuration des routes Flask**
4. **Pare-feu ou restrictions réseau** bloquant l'accès au serveur web

## Résumé des scripts fournis

| Script | Objectif | Quand l'utiliser |
|--------|----------|------------------|
| `flask_server_only.py` | Exécuter uniquement Flask | Pour isoler les problèmes de Flask |
| `debug_flask.py` | Tester Flask en isolation complète | Pour vérifier si Flask fonctionne correctement |
| `patch_server.py` | Corriger automatiquement les fichiers | Pour appliquer les correctifs sans modifier manuellement les fichiers |
| `kill_and_start.py` | Solution radicale | Quand rien d'autre ne fonctionne |

## Étapes recommandées

1. Essayez d'abord `python flask_server_only.py` pour voir si Flask démarre
2. Si cela échoue, essayez `python debug_flask.py`
3. Exécutez `python patch_server.py` pour appliquer les correctifs
4. En dernier recours, utilisez `python kill_and_start.py`

## Notes importantes

- Tous ces scripts créent des fichiers log détaillés (`flask_server.log`, `flask_debug.log`, etc.)
- Les modifications apportées par `patch_server.py` peuvent être annulées en restaurant les fichiers `.bak`
- `kill_and_start.py` arrête tous les processus Python, pas seulement ceux liés à l'application
