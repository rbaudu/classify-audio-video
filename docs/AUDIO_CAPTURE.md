# Documentation sur la capture audio

Ce document explique comment configurer et dépanner la capture audio dans le projet `classify-audio-video`.

## Configuration audio

La configuration audio se fait via le fichier `server/config.py` :

```python
# Configuration des paramètres de capture audio via PyAudio
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHUNK_SIZE = 1024
```

## Utilisation de PyAudio vs OBS

Le système peut utiliser deux sources pour l'audio :

1. **PyAudio** (direct) - capture l'audio directement depuis les périphériques du système
2. **OBS** - récupère l'audio depuis OBS via le websocket

Par défaut, le système utilise PyAudio :

```python
# Activation de la capture audio directe (PyAudio) vs OBS
USE_DIRECT_AUDIO_CAPTURE = True  # True = PyAudio, False = OBS
```

## Sélection du périphérique audio

Le système détecte automatiquement les périphériques audio disponibles et essaie de choisir le plus approprié :

1. Si aucun périphérique n'est spécifié, il liste tous les périphériques d'entrée
2. Il utilise le premier périphérique d'entrée disponible par défaut
3. Si le périphérique spécifié ne fonctionne pas, il teste automatiquement les autres

## Résolution des problèmes courants

### Aucun audio capturé

Si le système ne capture pas d'audio :

1. **Vérifiez les périphériques disponibles** dans les logs. Le système affiche tous les périphériques audio au démarrage.
2. **Vérifiez que le microphone est activé** dans les paramètres de votre système.
3. **Essayez d'exécuter le script de test** `test_pyAudio.py` pour tester directement votre configuration audio.

### Spécifier manuellement un périphérique audio

Pour utiliser un périphérique audio spécifique, vous pouvez modifier le code comme suit :

```python
# Dans server/main.py ou run.py
audio_capture = PyAudioCapture(device_index=14)  # Remplacer 14 par l'indice de votre périphérique
```

### Erreurs de format ou de taux d'échantillonnage

Si vous rencontrez des erreurs liées au format audio ou au taux d'échantillonnage :

1. Vérifiez les capacités de votre périphérique (taux d'échantillonnage supportés)
2. Modifiez `AUDIO_SAMPLE_RATE` et `AUDIO_FORMAT` dans `server/config.py` selon les capacités de votre périphérique

## Analyse des niveaux audio

Le système inclut une fonction `analyze_audio_levels()` qui permet de diagnostiquer les problèmes de niveau audio :

- **RMS** (Root Mean Square) - Niveau audio moyen
- **Peak** - Niveau de crête
- **Average** - Niveau moyen absolu
- **has_audio** - Indique si le niveau audio dépasse un seuil minimal

## Mécanismes de récupération

Le système inclut plusieurs mécanismes pour se remettre automatiquement des erreurs :

1. **Détection de périphériques alternatifs** - Si un périphérique échoue, le système teste et utilise automatiquement d'autres périphériques disponibles
2. **Surveillance continue** - Un thread vérifie régulièrement si le flux audio est toujours actif et tente de le redémarrer si nécessaire
3. **Gestion des erreurs** - Les erreurs sont interceptées pour éviter les plantages