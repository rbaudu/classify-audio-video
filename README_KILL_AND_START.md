# Solution radicale : kill_and_start.py

Ce document explique comment utiliser la solution la plus radicale et fiable pour démarrer et arrêter l'application `classify-audio-video`.

## Présentation

Le script `kill_and_start.py` est une solution robuste qui résout définitivement les problèmes d'arrêt CTRL+C et de lancement de l'IHM en utilisant une approche radicale:

1. Il tue d'abord tous les processus Python existants (sauf lui-même)
2. Il lance un nouveau processus Python avec `run.py` en arrière-plan
3. Il attend que le serveur soit disponible, puis ouvre un navigateur
4. Le serveur s'exécute complètement indépendamment du script de démarrage

## Utilisation

### Démarrer l'application

```bash
python kill_and_start.py
```

Cela va:
1. Arrêter tous les processus Python en cours d'exécution
2. Démarrer le serveur en arrière-plan
3. Ouvrir votre navigateur avec l'interface utilisateur

### Arrêter l'application

```bash
python kill_and_start.py stop
```

Cela arrêtera tous les processus Python en cours d'exécution.

### Redémarrer l'application

```bash
python kill_and_start.py restart
```

Cela arrêtera tous les processus Python, puis redémarrera le serveur.

### Passer des arguments à run.py

Vous pouvez passer des arguments à `run.py` comme d'habitude:

```bash
python kill_and_start.py --obs-version 31 --obs-host localhost --obs-port 4455
```

## Fonctionnement

Le script fonctionne en:

1. Utilisant `taskkill` sur Windows (ou `pkill` sur Linux/Mac) pour arrêter tous les processus Python existants
2. Démarrant `run.py` dans un nouveau processus détaché qui continue à s'exécuter en arrière-plan
3. Redirigeant la sortie vers des fichiers log pour référence ultérieure
4. Sondant le port du serveur pour confirmer qu'il est prêt
5. Ouvrant un navigateur web vers l'interface

## Avantages

Cette approche présente plusieurs avantages:

1. **Fiabilité totale**: En tuant tous les processus Python, on s'assure qu'il n'y a pas de processus bloqués
2. **Démarrage propre**: L'application démarre toujours à partir d'un état propre
3. **Indépendance**: Le serveur s'exécute de manière complètement indépendante du script de démarrage
4. **Logs accessibles**: Les sorties du serveur sont redirigées vers des fichiers log facilement consultables
5. **Interface simple**: Une seule commande pour tout gérer

## Inconvénients

Cette approche a également quelques inconvénients:

1. **Radical**: Tous les processus Python sont arrêtés, y compris ceux qui pourraient ne pas être liés à l'application
2. **Logs séparés**: Les logs sont dans des fichiers plutôt que dans la console
3. **Processus orphelin**: Le serveur tourne en arrière-plan sans processus parent

## Dépannage

### Si l'application ne démarre pas

Vérifiez les fichiers `server_output.log` et `server_error.log` qui sont créés dans le répertoire courant.

### Si l'arrêt ne fonctionne pas

Sur Windows, vous pouvez toujours utiliser le Gestionnaire des tâches pour terminer les processus Python.

### Autres problèmes

Si vous rencontrez d'autres problèmes, vous pouvez:
1. Essayer d'abord `python kill_and_start.py stop` pour arrêter tous les processus
2. Vérifier qu'aucun processus Python ne tourne en arrière-plan
3. Redémarrer avec `python kill_and_start.py`

## Notes importantes

Ce script est conçu comme une solution de dernier recours lorsque les méthodes plus élégantes échouent. Il fonctionne en tuant tous les processus Python, donc utilisez-le avec précaution si vous avez d'autres applications Python en cours d'exécution.
