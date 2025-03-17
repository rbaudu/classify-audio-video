# Documentation sur la capture OBS

Ce document explique comment configurer la capture vidéo depuis OBS Studio dans le projet `classify-audio-video`.

## Paramètres de configuration

La configuration de la source vidéo se fait dans le fichier `server/config.py` :

```python
VIDEO_SOURCE_NAME = os.environ.get('VIDEO_SOURCE_NAME') or 'camera'
```

Cette valeur doit correspondre exactement au nom de la source vidéo dans OBS Studio.

## Versions d'OBS Studio supportées

Le système supporte plusieurs versions d'OBS Studio :

- OBS 28+ : utilise `TakeSourceScreenshot`
- OBS 31+ : peut nécessiter `GetSourceScreenshot` comme méthode alternative

## Résolution des problèmes courants

1. **Aucune image capturée :** Si le système se connecte à OBS mais qu'aucune image n'est capturée, vérifiez que :
   - Le nom de source dans la configuration correspond exactement à celui dans OBS
   - La source est visible dans la scène active
   - Le plugin obs-websocket est correctement installé et activé

2. **Format de réponse inattendu :** Ce message d'erreur peut apparaître si :
   - La version d'OBS Studio n'est pas compatible avec la méthode de capture utilisée
   - La source n'existe pas ou n'est pas disponible
   - Le format de réponse a changé dans une nouvelle version d'OBS

## Méthodes de capture d'écran

Le système tente d'abord d'utiliser `TakeSourceScreenshot` et s'il échoue, il essaie la méthode alternative `GetSourceScreenshot`.

Les données d'image sont attendues dans différents formats selon la version d'OBS :
- Attribut `img`
- Attribut `imageData`
- Dans l'objet `data['imageData']`

## Configuration OBS WebSocket

Pour que la capture fonctionne, assurez-vous que :

1. Le plugin obs-websocket est installé (inclus par défaut depuis OBS 28)
2. Le serveur WebSocket est activé dans OBS (Outils > WebSocket Server Settings)
3. Le port configuré correspond à celui dans `server/config.py` (par défaut : 4455)
4. Si vous avez configuré un mot de passe, mettez-le à jour dans `server/config.py`
