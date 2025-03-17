# Journal des modifications (Changelog)

Ce fichier documente les modifications notables apportées au projet Classify Audio Video.

## Mars 2025 - Version 1.2.0

### Corrections
- **Capture d'image OBS** : Correction de l'erreur "Erreur lors de la capture d'image: 'img'" avec une détection améliorée des attributs de réponse OBS
  - Support pour différentes versions d'OBS avec vérification à la fois des attributs 'img' et 'imageData'
  - Ajout de logs détaillés pour mieux diagnostiquer les problèmes
  - Amélioration de la résilience face aux erreurs de capture

- **Gestion de l'arrêt du programme** : Amélioration significative de la réactivité au CTRL+C et arrêt propre des threads
  - Implémentation d'un mécanisme global d'événement d'arrêt (`stop_event`)
  - Utilisation de timeouts configurables pour l'arrêt des différents composants
  - Ajout d'un système d'arrêt d'urgence après un délai configurable
  - Amélioration des signaux d'interruption et de terminaison

### Modifications techniques
- Refonte du système de gestion des threads pour une meilleure terminaison
- Amélioration de la boucle de capture dans `sync_manager.py` pour utiliser des intervalles plus courts (0.01s au lieu de 0.03s)
- Optimisation de la détection des signaux d'arrêt dans tous les composants
- Ajout de mécanismes de récupération en cas d'erreur pendant l'arrêt

### Documentation
- Mise à jour du README.md avec les informations sur les dernières corrections
- Ajout de nouvelles sections dans le guide de dépannage (TROUBLESHOOTING.md)
- Création d'un fichier CHANGELOG.md pour suivre l'historique des modifications

## Janvier 2025 - Version 1.1.0

### Nouvelles fonctionnalités
- **Restructuration complète du code** pour améliorer la lisibilité et la maintenabilité
- **Tests unitaires complets** pour tous les modules principaux
- **Capture audio via PyAudio** au lieu d'OBS pour une meilleure qualité
- **Gestionnaire de synchronisation** pour aligner les flux audio et vidéo
- **API audio étendues** pour la gestion des périphériques
- **Système de gestion d'erreurs** robuste

### Améliorations
- Refonte de l'interface utilisateur
- Optimisation des performances
- Amélioration de la précision de classification

## Octobre 2024 - Version 1.0.0

### Fonctionnalités initiales
- Capture vidéo depuis OBS Studio
- Classification d'activité parmi 7 catégories
- Stockage des activités en base de données
- Interface web pour la visualisation
- Envoi des résultats vers un service externe
