#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de solution finale qui applique toutes les corrections
et lance l'application corrigée
"""

import os
import sys
import time
import subprocess
import importlib.util
import webbrowser
import threading
import signal

def print_header(title):
    """Affiche un titre bien formaté"""
    width = 70
    print("\n" + "="*width)
    print(" " + title.center(width-2))
    print("="*width + "\n")

def run_script(script_path):
    """Exécute un script Python et retourne s'il a réussi"""
    if not os.path.exists(script_path):
        print(f"Erreur: Le script {script_path} n'existe pas")
        return False
    
    try:
        print(f"Exécution de {script_path}...")
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        print(f"✓ Le script {script_path} a réussi")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Erreur lors de l'exécution de {script_path}:")
        print(f"  Sortie standard: {e.stdout}")
        print(f"  Erreur: {e.stderr}")
        return False
    except Exception as e:
        print(f"✗ Exception lors de l'exécution de {script_path}: {e}")
        return False

def is_port_open(port, host='localhost'):
    """Vérifie si un port est ouvert"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, int(port)))
    sock.close()
    return result == 0

def wait_for_port(port, host='localhost', timeout=30):
    """Attend que le port soit ouvert"""
    print(f"Attente de l'ouverture du port {port}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_open(port, host):
            print(f"✓ Le port {port} est ouvert")
            return True
        time.sleep(1)
        print(".", end="", flush=True)
    print(f"\n✗ Timeout en attendant l'ouverture du port {port}")
    return False

def open_browser(url, delay=3):
    """Ouvre un navigateur après un délai"""
    print(f"Ouverture du navigateur dans {delay} secondes...")
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"✓ Navigateur ouvert vers {url}")
        return True
    except Exception as e:
        print(f"✗ Erreur lors de l'ouverture du navigateur: {e}")
        print(f"  Veuillez ouvrir manuellement: {url}")
        return False

def run_application():
    """Lance l'application et gère l'arrêt propre"""
    print("Lancement de l'application...")
    
    # Utiliser le script run.py directement avec les corrections appliquées
    run_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run.py')
    
    try:
        # Lancer le processus
        process = subprocess.Popen(
            [sys.executable, run_script_path],
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
        
        # Attendre que le serveur démarre et ouvrir le navigateur
        if wait_for_port(5000):
            threading.Thread(target=open_browser, args=("http://localhost:5000",), daemon=True).start()
        
        # Configurer le gestionnaire de signal pour l'arrêt propre
        original_handler = signal.getsignal(signal.SIGINT)
        
        def signal_handler(sig, frame):
            print("\nArrêt de l'application...")
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("L'application ne répond pas, utilisation de kill")
                    process.kill()
            signal.signal(signal.SIGINT, original_handler)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Attendre la fin du processus
        process.wait()
        
        return True
    
    except KeyboardInterrupt:
        print("\nInterruption détectée. Arrêt...")
        return True
    except Exception as e:
        print(f"Erreur lors du lancement de l'application: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Fonction principale"""
    print_header("SOLUTION FINALE POUR CLASSIFY AUDIO VIDEO")
    
    print("Ce script applique toutes les corrections nécessaires et lance l'application.")
    print("À la fin, vous pourrez utiliser CTRL+C pour arrêter proprement le serveur.")
    print("\nÉtapes de correction:")
    print("1. Correction des problèmes CTRL+C")
    print("2. Correction des routes web")
    print("3. Correction des routes API")
    print("4. Lancement de l'application\n")
    
    try:
        # Demander confirmation
        response = input("Voulez-vous continuer? (o/n): ")
        if response.lower() not in ('o', 'oui', 'y', 'yes'):
            print("Opération annulée")
            return 0
        
        # Appliquer les corrections
        corrections = [
            ('fix_ctrl_c.py', "Correction des problèmes CTRL+C"),
            ('fix_routes.py', "Correction des routes web"),
            ('fix_api_routes.py', "Correction des routes API")
        ]
        
        for script, description in corrections:
            print_header(description)
            if os.path.exists(script):
                if not run_script(script):
                    print(f"✗ La correction {description} a échoué")
                    if input("Voulez-vous continuer quand même? (o/n): ").lower() not in ('o', 'oui', 'y', 'yes'):
                        return 1
            else:
                print(f"Le script {script} n'existe pas. Étape ignorée.")
        
        # Lancer l'application
        print_header("Lancement de l'application corrigée")
        run_application()
        
        return 0
    
    except KeyboardInterrupt:
        print("\nOpération annulée par l'utilisateur")
        return 0
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
