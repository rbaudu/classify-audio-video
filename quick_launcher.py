#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de démarrage rapide pour classify-audio-video.
Lance le serveur combiné et ouvre automatiquement le navigateur.
"""

import os
import sys
import subprocess
import signal
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("launcher.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Variable globale pour le processus
server_process = None

def signal_handler(sig, frame):
    """Gestionnaire de signal pour arrêter proprement le serveur avec CTRL+C"""
    global server_process
    
    logger.info("Interruption détectée. Arrêt du serveur...")
    
    if server_process:
        if sys.platform == 'win32':
            # Sous Windows, nous utilisons TASKKILL pour être sûr de tout arrêter
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(server_process.pid)])
        else:
            # Sous Unix, nous transmettons le signal SIGINT
            os.kill(server_process.pid, signal.SIGINT)
    
    sys.exit(0)

def main():
    """Fonction principale du lanceur"""
    global server_process
    
    # Installation du gestionnaire de signal
    signal.signal(signal.SIGINT, signal_handler)
    
    print("="*70)
    print("               DÉMARRAGE RAPIDE - CLASSIFY AUDIO VIDEO")
    print("="*70)
    print("")
    print("Ce script lance le serveur combiné et ouvre automatiquement un navigateur")
    print("vers l'interface.")
    print("")
    print("Appuyez sur Ctrl+C pour arrêter proprement le serveur.")
    print("="*70)
    print("")
    
    # Vérifier l'existence du script du serveur combiné
    server_script = "combined_server.py"
    if not os.path.exists(server_script):
        logger.error(f"Script {server_script} non trouvé!")
        print(f"ERREUR: Le script {server_script} n'a pas été trouvé.")
        print("Assurez-vous que les deux scripts se trouvent dans le même répertoire.")
        return 1
    
    # Lancer le serveur combiné
    logger.info(f"Lancement du serveur: {server_script}")
    
    try:
        # Utiliser CREATE_NEW_PROCESS_GROUP sous Windows pour gérer CTRL+C correctement
        if sys.platform == 'win32':
            # Utiliser shell=True pour éviter les problèmes avec les chemins contenant des espaces
            command = f'"{sys.executable}" "{server_script}" --open-browser'
            server_process = subprocess.Popen(
                command,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # Sous Unix, nous pouvons passer directement les arguments
            server_process = subprocess.Popen(
                [sys.executable, server_script, "--open-browser"]
            )
        
        logger.info(f"Serveur démarré avec PID: {server_process.pid}")
        
        # Attendre que le processus se termine (ce qui ne devrait arriver que si l'utilisateur le ferme)
        server_process.wait()
        
    except KeyboardInterrupt:
        # Cette partie ne devrait pas être atteinte grâce au gestionnaire de signal,
        # mais c'est une précaution supplémentaire
        signal_handler(signal.SIGINT, None)
        
    except Exception as e:
        logger.error(f"Erreur lors du lancement du serveur: {e}")
        print(f"ERREUR: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
