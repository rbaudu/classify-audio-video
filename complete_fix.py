#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script qui combine toutes les corrections en une seule étape
"""

import os
import sys
import subprocess
import importlib.util
import logging
import time
import webbrowser

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("complete_fix.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_script_exists(script_name):
    """Vérifie si un script existe"""
    return os.path.exists(script_name)

def run_script(script_name, args=None):
    """Exécute un script Python"""
    logger.info(f"Exécution de {script_name}...")
    
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, 
                             check=True, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             universal_newlines=True)
        logger.info(f"Script {script_name} exécuté avec succès")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'exécution de {script_name}: {e}")
        logger.error(f"Sortie standard: {e.stdout}")
        logger.error(f"Sortie d'erreur: {e.stderr}")
        return False, e.stderr
    except Exception as e:
        logger.error(f"Exception lors de l'exécution de {script_name}: {e}")
        return False, str(e)

def import_and_run_function(script_path, function_name):
    """Importe un script et exécute une fonction spécifique"""
    try:
        spec = importlib.util.spec_from_file_location("module.name", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, function_name):
            func = getattr(module, function_name)
            result = func()
            return True, result
        else:
            logger.error(f"Fonction {function_name} non trouvée dans {script_path}")
            return False, None
    except Exception as e:
        logger.error(f"Erreur lors de l'importation ou l'exécution de {script_path}: {e}")
        return False, None

def create_combined_solution():
    """Crée un script autonome qui combine toutes les corrections"""
    output_path = "classify_audio_video_fixed.py"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-

\"\"\"
Version autonome et corrigée de classify-audio-video
Ce script combine les corrections et améliorations en une seule solution
\"\"\"

import os
import sys
import logging
import threading
import time
import webbrowser
import signal
import subprocess
import platform

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("classify_audio_video.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def kill_python_processes():
    \"\"\"Tue tous les processus Python en cours sauf celui-ci\"\"\"
    logger.info("Arrêt des processus Python existants...")
    
    if platform.system() == 'Windows':
        try:
            subprocess.run(
                ['taskkill', '/F', '/FI', f'PID ne {os.getpid()}', '/IM', 'python.exe'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                shell=True
            )
            logger.info("Processus Python arrêtés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt des processus Python: {e}")
    else:
        try:
            # Sur Unix, utiliser pkill mais exclure le PID actuel
            subprocess.run(['pkill', '-9', '-f', f'^(?!.*{os.getpid()}).*python'])
            logger.info("Processus Python arrêtés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt des processus Python: {e}")
    
    # Attendre un peu pour que les processus se terminent
    time.sleep(1)

def run_server():
    \"\"\"Exécute le serveur avec les corrections\"\"\"
    logger.info("Démarrage du serveur corrigé...")
    
    # Utiliser le script original mais avec des arguments spécifiques
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run.py')
    
    try:
        # Créer un environnement pour run.py avec les paramètres corrects
        env = os.environ.copy()
        env['BYPASS_ROUTES_CHECK'] = 'true'  # Flag pour indiquer d'utiliser les routes de secours
        
        # Démarrer le processus en arrière-plan
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
                print(line, end='')
        
        output_thread = threading.Thread(target=print_output)
        output_thread.daemon = True
        output_thread.start()
        
        return process
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur: {e}")
        return None

def open_browser_when_ready(url, max_attempts=30, interval=1):
    \"\"\"Tente d'ouvrir le navigateur une fois que le serveur est prêt\"\"\"
    logger.info(f"Attente du démarrage du serveur...")
    
    import socket
    
    def is_port_open(host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    
    host, port = url.split('//')[1].split(':')
    if '/' in port:
        port = port.split('/')[0]
    port = int(port)
    
    # Attendre que le port soit ouvert
    for i in range(max_attempts):
        if is_port_open(host, port):
            logger.info(f"Serveur prêt après {i+1} tentatives")
            time.sleep(1)  # Attendre un peu plus pour que Flask soit vraiment prêt
            try:
                webbrowser.open(url)
                logger.info(f"Navigateur ouvert à l'adresse {url}")
                return True
            except Exception as e:
                logger.error(f"Erreur lors de l'ouverture du navigateur: {e}")
                logger.info(f"Veuillez ouvrir manuellement: {url}")
                return False
        
        logger.info(f"Tentative {i+1}/{max_attempts}... Serveur pas encore prêt")
        time.sleep(interval)
    
    logger.error(f"Impossible d'accéder au serveur après {max_attempts} tentatives")
    logger.info(f"Veuillez vérifier si le serveur fonctionne et ouvrir manuellement: {url}")
    return False

def signal_handler(sig, frame, server_process=None):
    \"\"\"Gestionnaire de signal pour l'arrêt propre\"\"\"
    logger.info(f"Signal d'interruption reçu ({sig}). Arrêt du serveur...")
    
    if server_process and server_process.poll() is None:
        try:
            server_process.terminate()
            server_process.wait(timeout=5)  # Attendre jusqu'à 5 secondes
        except subprocess.TimeoutExpired:
            logger.warning("Le serveur ne répond pas à terminate(), utilisation de kill()")
            server_process.kill()
    
    # Arrêter tous les autres processus Python au cas où
    kill_python_processes()
    
    logger.info("Arrêt terminé")
    sys.exit(0)

def main():
    \"\"\"Fonction principale\"\"\"
    try:
        # Afficher le titre
        print("="*60)
        print("  CLASSIFY AUDIO VIDEO - VERSION CORRIGÉE")
        print("="*60)
        print("Ce script lance une version corrigée de l'application avec:")
        print("  - Gestion améliorée de l'arrêt CTRL+C")
        print("  - Lancement automatique de l'interface web")
        print("  - Corrections des problèmes de routes")
        print("="*60)
        
        # Arrêter les processus Python existants
        kill_python_processes()
        
        # Démarrer le serveur
        server_process = run_server()
        if not server_process:
            logger.error("Échec du démarrage du serveur")
            return 1
        
        # Configurer le gestionnaire de signal
        handler = lambda sig, frame: signal_handler(sig, frame, server_process)
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)
        
        # Tenter d'ouvrir le navigateur
        open_browser_when_ready("http://localhost:5000/flask-test")
        
        # Attendre que le serveur se termine
        server_process.wait()
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Interruption clavier détectée")
        return 0
    except Exception as e:
        logger.error(f"Erreur: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
""")
        logger.info(f"Script combiné créé: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création du script combiné: {e}")
        return False

def test_web_server():
    """Teste si le serveur web est accessible"""
    import socket
    
    def is_port_open(host, port, timeout=1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    
    host = 'localhost'
    port = 5000
    
    # Vérifie si le port est déjà utilisé
    if is_port_open(host, port):
        logger.warning(f"Le port {port} est déjà utilisé. Un serveur est peut-être déjà en cours d'exécution.")
        
        # Demander à l'utilisateur s'il veut ouvrir un navigateur
        try:
            response = input(f"Voulez-vous ouvrir un navigateur vers http://{host}:{port}/flask-test? (o/n): ")
            if response.lower() in ['o', 'oui', 'y', 'yes']:
                webbrowser.open(f"http://{host}:{port}/flask-test")
        except:
            pass
        
        return True
    
    return False

def main():
    """Fonction principale"""
    logger.info("=== Script de correction complète ===")
    
    # Vérifier si le serveur est déjà en cours d'exécution
    if test_web_server():
        logger.info("Un serveur web est déjà en cours d'exécution sur le port 5000.")
        logger.info("Exécution des corrections de routes uniquement...")
        
        # Exécuter uniquement les corrections de routes
        if check_script_exists("fix_routes.py"):
            success, _ = run_script("fix_routes.py")
            if not success:
                logger.error("Échec des corrections de routes")
                return 1
        else:
            logger.error("Script fix_routes.py introuvable")
            return 1
        
        return 0
    
    # Exécution des scripts dans l'ordre
    steps = [
        ("patch_server.py", "Correction des problèmes de shutdown et Flask"),
        ("fix_routes.py", "Correction des problèmes de routes"),
        ("flask_server_only.py", "Test du serveur Flask")
    ]
    
    # Vérifier que tous les scripts existent
    for script, _ in steps:
        if not check_script_exists(script):
            logger.error(f"Script {script} introuvable")
            return 1
    
    # Créer la solution combinée
    if create_combined_solution():
        logger.info("Solution combinée créée avec succès: classify_audio_video_fixed.py")
    
    # Exécuter les scripts un par un
    for i, (script, description) in enumerate(steps):
        logger.info(f"Étape {i+1}/{len(steps)}: {description}")
        
        if i < len(steps) - 1:  # Pour tous sauf le dernier
            success, _ = run_script(script)
            if not success:
                logger.error(f"Échec de l'étape {i+1}: {description}")
                return 1
        else:
            # Pour le dernier script (test du serveur), demander confirmation
            try:
                response = input(f"\nVoulez-vous tester le serveur Flask maintenant? (o/n): ")
                if response.lower() in ['o', 'oui', 'y', 'yes']:
                    if script == "flask_server_only.py":
                        # Exécuter ici plutôt que par subprocess pour voir les logs en temps réel
                        import_and_run_function(script, "main")
                    else:
                        run_script(script)
            except KeyboardInterrupt:
                logger.info("\nTest annulé")
    
    logger.info("\nToutes les corrections ont été appliquées avec succès!")
    logger.info("\nVous pouvez maintenant utiliser l'application de plusieurs façons:")
    logger.info("  1. python classify_audio_video_fixed.py    (solution tout-en-un)")
    logger.info("  2. python run.py                          (version originale corrigée)")
    logger.info("  3. python flask_server_only.py            (version Flask uniquement)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
