#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script principal pour lancer l'application classify-audio-video
avec une gestion améliorée de l'arrêt et l'ouverture automatique du navigateur
"""

import os
import sys
import time
import subprocess
import threading
import atexit
import signal
import platform

def launch_server():
    """Lance le serveur en utilisant fix_shutdown.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, 'fix_shutdown.py')
    
    # Lancer le serveur dans un nouveau processus
    server_process = subprocess.Popen([sys.executable, server_script] + sys.argv[1:],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    universal_newlines=True, bufsize=1)
    
    return server_process

def print_server_output(process):
    """Affiche la sortie du serveur en temps réel"""
    for line in process.stdout:
        print(line, end='')

def launch_browser():
    """Lance le navigateur après un court délai"""
    # Attendre un peu pour que le serveur puisse démarrer
    time.sleep(5)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    browser_script = os.path.join(script_dir, 'browser_launcher.py')
    
    # Lancer le script d'ouverture du navigateur
    browser_process = subprocess.Popen([sys.executable, browser_script],
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     universal_newlines=True)
    
    # Afficher la sortie du lanceur de navigateur
    for line in browser_process.stdout:
        print(line, end='')

def cleanup(server_process):
    """Nettoyage lors de la sortie"""
    if server_process and server_process.poll() is None:
        print("\nArrêt du serveur...")
        
        try:
            # Envoyer SIGTERM au processus
            if platform.system() == 'Windows':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(server_process.pid)], 
                              shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                server_process.terminate()
                
            # Attendre un peu pour l'arrêt propre
            time.sleep(2)
            
            # Si toujours en cours, forcer l'arrêt
            if server_process.poll() is None:
                if platform.system() == 'Windows':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(server_process.pid)], 
                                  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    server_process.kill()
        except Exception as e:
            print(f"Erreur lors de l'arrêt du serveur: {e}")

def signal_handler(sig, frame, server_process):
    """Gestionnaire de signal personnalisé"""
    print("\nSignal d'interruption reçu. Arrêt propre...")
    cleanup(server_process)
    sys.exit(0)

def main():
    """Fonction principale"""
    print("=== Lancement de classify-audio-video ===")
    print("Version améliorée avec gestion d'arrêt et lancement automatique du navigateur")
    print("Appuyez sur CTRL+C pour arrêter proprement l'application")
    print()
    
    # Lancer le serveur
    server_process = launch_server()
    
    # Enregistrer la fonction de nettoyage
    atexit.register(cleanup, server_process)
    
    # Configurer le gestionnaire de signal pour CTRL+C
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, server_process))
    signal.signal(signal.SIGTERM, lambda sig, frame: signal_handler(sig, frame, server_process))
    
    # Lancer le navigateur dans un thread séparé
    browser_thread = threading.Thread(target=launch_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Thread pour afficher la sortie du serveur
    output_thread = threading.Thread(target=print_server_output, args=(server_process,))
    output_thread.daemon = True
    output_thread.start()
    
    try:
        # Attendre que le serveur se termine
        server_process.wait()
        
    except KeyboardInterrupt:
        # CTRL+C a été pressé
        print("\nInterruption détectée. Arrêt du serveur...")
        cleanup(server_process)
    
    except Exception as e:
        print(f"Erreur : {e}")
        cleanup(server_process)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
