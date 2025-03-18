# Guide de capture OBS 31.0.2

Ce guide explique comment utiliser la capture vidéo avec OBS 31.0.2 et son API WebSocket.

## Contexte

OBS 31.0.2 inclut nativement un serveur WebSocket, ce qui élimine le besoin d'installer le plugin externe obswebsocket. Cependant, l'API a changé, ce qui rend incompatibles certaines méthodes de capture d'écran utilisées dans les versions précédentes d'OBS.

## Solution

Nous avons créé un ensemble d'outils pour résoudre ce problème :

1. **OBS31Capture** - Une classe optimisée pour OBS 31.0.2+ qui utilise directement l'API WebSocket intégrée
2. **Scripts de test** - Des scripts pour explorer l'API et tester la capture
3. **Script d'installation** - Un script pour installer les dépendances requises

## Installation

```bash
# Cloner le dépôt (si ce n'est pas déjà fait)
git clone https://github.com/rbaudu/classify-audio-video.git
cd classify-audio-video

# Installer les dépendances
python install_requirements.py
```

## Tester l'API OBS 31.0.2

Le script `test_obs_31_api.py` explore l'API disponible et affiche les détails des méthodes disponibles :

```bash
python tests/test_obs_31_api.py
```

Ce script va :
- Se connecter à OBS
- Lister toutes les méthodes disponibles dans le client WebSocket
- Tester différentes approches pour capturer des images de sources vidéo

## Utiliser la classe OBS31Capture

La classe `OBS31Capture` est conçue spécifiquement pour OBS 31.0.2 et gère automatiquement les différences d'API.

Pour tester la capture avec cette classe :

```bash
python tests/test_obs_31_capture.py
```

Pour utiliser la classe dans votre code :

```python
from server.capture.obs_31_capture import OBS31Capture

# Créer une instance
obs = OBS31Capture()

# Activer le mode d'images de test (optionnel)
obs.enable_test_images(True)  # Si True, des images de test seront générées en cas d'échec

# Capturer une image d'une source
source_name = "camera"  # Remplacer par le nom de votre source
image = obs.capture_frame(source_name)

# Enregistrer l'image
if image:
    image.save("capture.png")
```

## Configuration OBS

Pour que la capture fonctionne :

1. Assurez-vous que le serveur WebSocket est activé dans OBS :
   - Allez dans `Outils > WebSocket Server Settings`
   - Activez `Enable WebSocket Server`
   - Le port par défaut est 4455
   - Si vous avez défini un mot de passe, vous devrez le fournir à la classe OBS31Capture

2. Ajoutez vos sources vidéo à OBS (caméra, capture d'écran, etc.)

3. La source doit être visible dans la scène active pour que la capture fonctionne

## Dépannage

Si vous rencontrez des problèmes :

1. **Erreur de connexion** : Vérifiez que le serveur WebSocket est activé dans OBS et que le port est correct

2. **Capture échoue** : 
   - Vérifiez que la source est visible dans la scène active
   - Essayez d'activer le mode d'images de test pour voir si le code fonctionne mais pas la capture
   - Consultez les logs pour les messages d'erreur spécifiques

3. **Version incompatible** :
   - Vérifiez la version d'OBS (Aide > À propos)
   - Mettez à jour vers OBS 31.0.2 ou plus récent

## Mode d'images de test

La classe `OBS31Capture` inclut un mode qui génère des images de test colorées si la capture réelle échoue :

```python
obs = OBS31Capture()
obs.enable_test_images(True)  # Activer les images de test
```

Ce mode est utile pour:
- Tester le code sans avoir OBS en fonctionnement
- Faire fonctionner votre application même si la capture OBS échoue
- Déboguer les problèmes en séparant les erreurs de capture des erreurs de traitement

## Notes techniques

- La classe utilise le module `obsws_python` pour communiquer avec OBS
- OBS 31.0.2 utilise un protocole WebSocket différent des versions précédentes
- La méthode `GetSourceScreenshot` est utilisée pour capturer les images
- Les images capturées sont renvoyées au format PNG encodé en base64
