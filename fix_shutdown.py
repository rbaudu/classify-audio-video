#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour lancer l'application avec un gestionnaire de signal amélioré
pour assurer l'arrêt correct via CTRL+C
"""

import os
import sys
import signal
import subprocess
import time
import platform

def signal_handler(sig, frame):
    """Gestionnaire de signal robuste pour CTRL+C"""
    print("\nInterruption détectée (CTRL+C). Arrêt forcé des processus...")
    
    # Si nous sommes sur Windows
    if platform.system() == 'Windows':
        # Obtenir le PID du processus Python actuel
        current_pid = os.getpid()
        
        # Utiliser taskkill pour tuer le processus
        subprocess.run(['taskkill', '/F', '/PID', str(current_pid), '/T'], 
                      shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        # Sur Linux/Mac utiliser kill
        os.kill(os.getpid(), signal.SIGKILL)

def main():
    """Fonction principale pour lancer l'application avec le gestionnaire de signal amélioré"""
    # Enregistrer notre gestionnaire de signal personnalisé
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Message d'information
    print("Lancement de classify-audio-video avec gestionnaire d'arrêt amélioré")
    print("Appuyez sur CTRL+C pour arrêter proprement l'application")
    
    # Chemin vers le script principal (relatif à ce script)
    script_path = os.path.join(os.path.dirname(__file__), 'run.py')
    
    try:
        # Exécuter run.py dans un sous-processus
        process = subprocess.Popen([sys.executable, script_path] + sys.argv[1:], 
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 universal_newlines=True, bufsize=1)
        
        # Afficher les sorties en temps réel
        for line in process.stdout:
            print(line, end='')
        
        # Attendre la fin du processus
        process.wait()
        
    except KeyboardInterrupt:
        # CTRL+C a été pressé
        print("\nInterruption détectée. Arrêt du serveur...")
        
        # Envoyer SIGTERM au sous-processus
        if process.poll() is None:  # Si le processus est toujours en cours
            process.terminate()
            
            # Attendre un peu pour un arrêt propre
            time.sleep(2)
            
            # Si toujours en cours, forcer l'arrêt
            if process.poll() is None:
                process.kill()
        
        print("Serveur arrêté.")
        
    except Exception as e:
        print(f"Erreur lors de l'exécution: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
