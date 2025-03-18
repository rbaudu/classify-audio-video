#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Version ultra-simplifiée pour lancer l'application avec le minimum de complexité
"""

import os
import sys
import subprocess
import time
import webbrowser
import threading
import signal
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_start.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def is_port_in_use(port, host='localhost'):
    """Vérifie si un port est déjà utilisé"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0

def open_browser(url, delay=3):
    """Ouvre le navigateur après un certain délai"""
    logger.info(f"Ouverture du navigateur vers {url} dans {delay} secondes...")
    time.sleep(delay)
    webbrowser.open(url)

def run_server():
    """Lance le serveur en utilisant run.py avec des modifications pour CTRL+C"""
    # Vérifier que le port est disponible
    if is_port_in_use(5000):
        logger.warning("Le port 5000 est déjà utilisé. Un autre serveur est peut-être en cours d'exécution.")
        # Ouvrir quand même un navigateur vers le serveur existant
        threading.Thread(target=open_browser, args=('http://localhost:5000',)).start()
        return None
    
    # Variables d'environnement pour forcer la prise en compte des routes
    env = os.environ.copy()
    env['FLASK_RUN_PORT'] = '5000'
    env['FLASK_RUN_HOST'] = '0.0.0.0'
    
    # Lancer le script run.py directement (sans tuer les autres processus)
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run.py')
    
    logger.info(f"Lancement du serveur via {script_path}...")
    
    # Lancer le processus et capturer sa sortie
    process = subprocess.Popen(
        [sys.executable, script_path],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Thread pour afficher la sortie en temps réel
    def print_output():
        for line in process.stdout:
            print(line, end='', flush=True)
    
    output_thread = threading.Thread(target=print_output)
    output_thread.daemon = True
    output_thread.start()
    
    # Lancer le thread pour ouvrir le navigateur
    browser_thread = threading.Thread(target=open_browser, args=('http://localhost:5000',))
    browser_thread.daemon = True
    browser_thread.start()
    
    return process

def handle_exit(server_process):
    """Gère l'arrêt propre du serveur"""
    def signal_handler(sig, frame):
        logger.info(f"Signal d'interruption reçu. Arrêt du serveur...")
        if server_process and server_process.poll() is None:
            server_process.terminate()
            # Attendre que le processus se termine
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Le serveur ne répond pas, utilisation de kill")
                server_process.kill()
        sys.exit(0)
    
    return signal_handler

def main():
    """Fonction principale"""
    try:
        print("\n" + "="*60)
        print(" "*10 + "CLASSIFY AUDIO VIDEO - DÉMARRAGE SIMPLIFIÉ")
        print("="*60)
        print("• Lancement du serveur avec l'interface web")
        print("• Appuyez sur CTRL+C pour arrêter proprement le serveur")
        print("="*60 + "\n")
        
        # Lancer le serveur
        server_process = run_server()
        
        if server_process:
            # Configurer le gestionnaire de signal pour CTRL+C
            signal.signal(signal.SIGINT, handle_exit(server_process))
            signal.signal(signal.SIGTERM, handle_exit(server_process))
            
            # Attendre que le processus se termine
            server_process.wait()
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Interruption utilisateur détectée. Arrêt...")
        return 0
    except Exception as e:
        logger.error(f"Erreur: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
