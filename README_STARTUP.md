# Guide de démarrage amélioré

Ce document explique comment utiliser les scripts de démarrage améliorés qui ont été ajoutés pour résoudre les problèmes de lancement de l'IHM et de l'arrêt par CTRL+C.

## Problèmes résolus

1. **Problème d'arrêt CTRL+C** : Impossible d'arrêter proprement le serveur avec CTRL+C
2. **Problème de lancement de l'IHM** : L'interface web ne se lance pas automatiquement

## Nouveaux scripts

Trois nouveaux scripts ont été ajoutés pour résoudre ces problèmes :

1. **start.py** : Script principal qui lance tout le système avec gestion améliorée de l'arrêt et ouverture automatique du navigateur
2. **fix_shutdown.py** : Wrapper pour run.py qui améliore la gestion de l'arrêt par CTRL+C
3. **browser_launcher.py** : Script qui détecte le démarrage du serveur et ouvre automatiquement un navigateur

## Comment utiliser le nouveau système

### Méthode recommandée

Utilisez simplement `start.py` pour lancer l'application :

```bash
python start.py
```

Ce script va :
- Démarrer le serveur avec une gestion robuste de CTRL+C
- Ouvrir automatiquement un navigateur vers l'interface web
- Assurer un arrêt propre lorsque vous appuyez sur CTRL+C

Vous pouvez également passer des arguments de ligne de commande qui seront transmis à `run.py` :

```bash
python start.py --obs-version 31 --obs-host localhost --obs-port 4455
```

### Utilisation des scripts individuels

Si vous préférez, vous pouvez utiliser les scripts individuellement :

#### Pour résoudre uniquement le problème CTRL+C

```bash
python fix_shutdown.py
```

#### Pour ouvrir uniquement le navigateur (après avoir démarré le serveur)

```bash
python browser_launcher.py
```

## Comment ça fonctionne

### Résolution du problème CTRL+C

Le script `fix_shutdown.py` résout le problème d'arrêt CTRL+C en :
- Exécutant `run.py` dans un sous-processus
- Interceptant le signal CTRL+C au niveau du script parent
- Utilisant des méthodes robustes pour terminer le sous-processus (taskkill sur Windows)

### Résolution du problème de l'IHM

Le script `browser_launcher.py` résout le problème de lancement de l'IHM en :
- Surveillant le port du serveur pour détecter quand il est prêt
- Ouvrant automatiquement le navigateur par défaut à l'URL correcte
- Tentant plusieurs navigateurs en cas d'échec du navigateur par défaut
- Fonctionnant sur Windows, macOS et Linux

### Script principal intégré

Le script `start.py` combine ces deux fonctionnalités et offre :
- Une interface utilisateur unifiée
- Une gestion propre des exceptions et des erreurs
- Un affichage en temps réel de la sortie du serveur
- Une gestion fiable des ressources lors de la fermeture

## Dépannage

### Si le navigateur ne s'ouvre pas automatiquement

Le serveur est accessible à l'URL affichée dans les logs (généralement http://localhost:5000).
Vous pouvez ouvrir manuellement votre navigateur à cette adresse.

### Si CTRL+C ne fonctionne toujours pas

Sur Windows, vous pouvez fermer la fenêtre de la console ou utiliser le gestionnaire de tâches pour terminer le processus.

Pour les utilisateurs avancés, vous pouvez aussi utiliser cette commande dans une autre console :

```bash
taskkill /F /IM python.exe /T
```

(Cette commande terminera tous les processus Python en cours, utilisez-la avec précaution)
