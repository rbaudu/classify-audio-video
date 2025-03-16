import pyaudio

def test_pyaudio():
    print(f"PyAudio version: {pyaudio.__version__}")
    
    # Créer une instance PyAudio
    p = pyaudio.PyAudio()
    
    # Afficher les informations sur les périphériques audio
    print("\nPériphériques audio disponibles:")
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        print(f"  Device {i}: {device_info['name']}")
        print(f"    - Entrées: {device_info['maxInputChannels']}")
        print(f"    - Sorties: {device_info['maxOutputChannels']}")
        print(f"    - Taux d'échantillonnage par défaut: {device_info['defaultSampleRate']} Hz")
    
    # Essayer d'ouvrir un flux audio d'entrée (microphone)
    try:
        input_device_index = p.get_default_input_device_info()['index']
        print(f"\nEssai d'ouverture du périphérique d'entrée par défaut (index {input_device_index})...")
        
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=input_device_index,
            frames_per_buffer=1024
        )
        
        print("Le périphérique d'entrée a été ouvert avec succès.")
        print("Fermeture du flux...")
        stream.close()
    except Exception as e:
        print(f"Erreur lors de l'ouverture du périphérique d'entrée: {str(e)}")
    
    # Terminer PyAudio
    p.terminate()
    print("\nTest PyAudio terminé.")

if __name__ == "__main__":
    test_pyaudio()