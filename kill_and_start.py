#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script ultime pour démarrer/arrêter l'application
Ce script fonctionne en deux parties:
1. Il tue tous les processus Python existants (y compris lui-même)
2. Il relance un nouveau processus Python avec run.py
"""

import os
import sys
import subprocess
import time
import webbrowser
import platform
import socket

def kill_all_python():
    """Tue tous les processus Python en cours d'exécution"""
    print("Arrêt de tous les processus Python en cours...")
    
    if platform.system() == 'Windows':
        # Sur Windows, utiliser taskkill pour tuer tous les processus Python
        try:
            # Cette commande tue tous les processus Python SAUF celui-ci
            # /F = forcé, /FI = filtre, /IM = par nom d'image
            subprocess.run(
                ['taskkill', '/F', '/FI', f'PID ne {os.getpid()}', '/IM', 'python.exe'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                shell=True
            )
            print("Processus Python arrêtés avec succès")
        except Exception as e:
            print(f"Erreur lors de l'arrêt des processus Python: {e}")
    else:
        # Sur Unix, utiliser pkill
        try:
            subprocess.run(['pkill', '-9', 'python'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Processus Python arrêtés avec succès")
        except Exception as e:
            print(f"Erreur lors de l'arrêt des processus Python: {e}")
    
    # Attendre un peu pour que les processus se terminent
    time.sleep(2)

def start_server():
    """Démarre le serveur"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, 'run.py')
    
    print("Démarrage du serveur classify-audio-video...")
    
    # Construire les arguments à passer à run.py
    run_args = []
    if len(sys.argv) > 1:
        run_args = sys.argv[1:]
    
    # Démarrer le processus en arrière-plan avec son propre groupe de processus
    # pour qu'il survive à la fin de ce script
    creationflags = 0
    if platform.system() == 'Windows':
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    
    subprocess.Popen(
        [sys.executable, server_script] + run_args,
        creationflags=creationflags,
        # Rediriger vers des fichiers pour permettre de voir les logs
        stdout=open('server_output.log', 'w'),
        stderr=open('server_error.log', 'w')
    )
    
    print("Serveur démarré en arrière-plan")
    print("Les logs sont disponibles dans server_output.log et server_error.log")

def is_port_open(host, port, timeout=1):
    """Vérifie si un port est ouvert sur l'hôte spécifié"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def wait_for_server(host='localhost', port=5000, max_attempts=30):
    """Attend que le serveur soit disponible"""
    print(f"Attente du démarrage du serveur sur {host}:{port}...")
    
    for attempt in range(1, max_attempts + 1):
        print(f"Tentative {attempt}/{max_attempts}...", end='\r')
        if is_port_open(host, port):
            print(f"\nServeur prêt sur {host}:{port}!")
            return True
        time.sleep(1)
    
    print(f"\nServeur non disponible après {max_attempts} tentatives")
    return False

def open_browser():
    """Ouvre le navigateur vers l'interface web"""
    url = "http://localhost:5000"
    
    print(f"Ouverture du navigateur à l'adresse: {url}")
    
    try:
        # Tenter d'ouvrir le navigateur par défaut
        webbrowser.open(url)
    except Exception as e:
        print(f"Erreur lors de l'ouverture du navigateur: {e}")
        print(f"Veuillez ouvrir manuellement l'URL: {url}")

def main():
    """Fonction principale"""
    action = 'start'
    if len(sys.argv) > 1 and sys.argv[1] in ['stop', 'restart']:
        action = sys.argv[1]
        # Supprimer l'argument d'action
        sys.argv.pop(1)
    
    try:
        if action in ['stop', 'restart']:
            kill_all_python()
            if action == 'stop':
                print("Serveur arrêté avec succès")
                return 0
        
        # Démarrer le serveur
        start_server()
        
        # Attendre que le serveur soit prêt
        if wait_for_server():
            # Ouvrir le navigateur
            open_browser()
            
            print("\nServeur en cours d'exécution en arrière-plan.")
            print("Pour arrêter le serveur, exécutez: python kill_and_start.py stop")
        else:
            print("Le serveur n'a pas pu démarrer correctement, vérifiez les logs.")
            return 1
            
    except KeyboardInterrupt:
        print("\nInterruption détectée, arrêt en cours...")
        kill_all_python()
    except Exception as e:
        print(f"Erreur: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
