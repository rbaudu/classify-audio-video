#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de démarrage rapide pour classify-audio-video
Ce script lance le serveur et ouvre un navigateur sans essayer de corriger quoi que ce soit
"""

import os
import sys
import subprocess
import threading
import webbrowser
import time
import logging
import signal

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("quick_start.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def is_port_in_use(port, host='localhost'):
    """Vérifie si un port est déjà utilisé"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, int(port)))
    sock.close()
    return result == 0

def open_browser(url, delay=5):
    """Ouvre un navigateur après un délai"""
    logger.info(f"Le navigateur s'ouvrira automatiquement dans {delay} secondes...")
    time.sleep(delay)
    try:
        webbrowser.open(url)
        logger.info(f"Navigateur ouvert vers {url}")
    except Exception as e:
        logger.error(f"Erreur lors de l'ouverture du navigateur: {e}")
        logger.info(f"Veuillez ouvrir manuellement: {url}")

def main():
    """Fonction principale"""
    print("\n" + "="*70)
    print(" "*15 + "DÉMARRAGE RAPIDE - CLASSIFY AUDIO VIDEO")
    print("="*70)
    print("\nCe script lance simple_fixed_run.py (version corrigée de run.py)")
    print("et ouvre automatiquement un navigateur vers l'interface.")
    print("\nAppuyez sur Ctrl+C pour arrêter le serveur.")
    print("="*70 + "\n")
    
    # Vérifier si le port 5000 est déjà utilisé
    if is_port_in_use(5000):
        logger.warning("Le port 5000 est déjà utilisé!")
        logger.warning("Un serveur est probablement déjà en cours d'exécution.")
        
        response = input("Voulez-vous ouvrir un navigateur vers l'interface? (o/n): ")
        if response.lower() in ('o', 'oui', 'y', 'yes'):
            webbrowser.open("http://localhost:5000")
        
        response = input("Voulez-vous essayer de tuer les processus existants? (o/n): ")
        if response.lower() in ('o', 'oui', 'y', 'yes'):
            if sys.platform == 'win32':
                # Windows
                os.system('taskkill /F /IM python.exe /T')
                logger.info("Commande taskkill exécutée")
            else:
                # Linux/Mac
                os.system('pkill -9 python')
                logger.info("Commande pkill exécutée")
            
            # Attendre un peu
            time.sleep(2)
            
            # Vérifier si le port est maintenant libre
            if is_port_in_use(5000):
                logger.error("Le port 5000 est toujours utilisé!")
                logger.error("Vous devrez libérer ce port manuellement avant de continuer.")
                return 1
            else:
                logger.info("Port 5000 libéré avec succès, on continue...")
        else:
            return 0
    
    try:
        # Utiliser simple_fixed_run.py s'il existe, sinon run.py
        script_path = 'simple_fixed_run.py'
        if not os.path.exists(script_path):
            logger.warning(f"{script_path} n'existe pas, utilisation de run.py à la place")
            script_path = 'run.py'
        
        # Lancer le serveur
        logger.info(f"Lancement de {script_path}...")
        
        # Configurer le gestionnaire de signal pour l'arrêt propre
        original_handler = signal.getsignal(signal.SIGINT)
        
        def handle_interrupt(sig, frame):
            logger.info("Interruption détectée. Arrêt du serveur...")
            if sys.platform == 'win32':
                # Windows
                os.system('taskkill /F /IM python.exe /T')
            else:
                # Linux/Mac
                os.system('pkill -9 python')
            
            # Restaurer le gestionnaire original et propager le signal
            signal.signal(signal.SIGINT, original_handler)
            os.kill(os.getpid(), signal.SIGINT)
        
        signal.signal(signal.SIGINT, handle_interrupt)
        
        # Lancer le processus
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Thread pour afficher la sortie en temps réel
        def print_output():
            for line in process.stdout:
                print(line, end='')
        
        output_thread = threading.Thread(target=print_output)
        output_thread.daemon = True
        output_thread.start()
        
        # Thread pour ouvrir le navigateur après un délai
        browser_thread = threading.Thread(
            target=open_browser,
            args=("http://localhost:5000",),
            daemon=True
        )
        browser_thread.start()
        
        # Attendre que le processus se termine
        process.wait()
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("\nInterruption détectée. Arrêt du serveur...")
        return 0
    except Exception as e:
        logger.error(f"Erreur: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
