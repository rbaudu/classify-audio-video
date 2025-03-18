#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script qui exécute uniquement le serveur Flask de l'application
sans démarrer les composants de capture OBS et audio
"""

import os
import sys
import logging
import time
import threading
import webbrowser
from server.config import Config
from server.flask_app import create_app

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flask_server.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_flask_app(app, host, port):
    """Fonction pour exécuter Flask"""
    logger.info(f"Démarrage du serveur Flask sur {host}:{port}")
    try:
        app.run(host=host, port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de Flask: {e}")
        import traceback
        logger.error(traceback.format_exc())

def open_browser(url, delay=2):
    """Ouvre le navigateur après un délai"""
    logger.info(f"Attente de {delay} secondes avant d'ouvrir le navigateur...")
    time.sleep(delay)
    logger.info(f"Tentative d'ouverture du navigateur à {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Erreur lors de l'ouverture du navigateur: {e}")

def main():
    """Fonction principale"""
    try:
        logger.info("=== Démarrage Flask uniquement ===")
        
        # Charger la configuration
        host = Config.FLASK_HOST
        port = Config.FLASK_PORT
        
        # Afficher les chemins importants
        script_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(script_dir, 'web', 'templates')
        static_dir = os.path.join(script_dir, 'web', 'static')
        
        logger.info(f"Chemin du projet: {script_dir}")
        logger.info(f"Chemin des templates: {templates_dir}")
        logger.info(f"Chemin des fichiers statiques: {static_dir}")
        
        # Vérifier si les dossiers existent
        if os.path.exists(templates_dir):
            template_files = os.listdir(templates_dir)
            logger.info(f"Templates disponibles: {template_files}")
        else:
            logger.error(f"Le dossier des templates n'existe pas: {templates_dir}")
        
        # Créer l'application Flask directement via la fonction standard
        app = create_app()
        
        # Configurer l'application sans initialiser les autres composants
        app.config['BYPASS_INIT'] = True  # Flag pour indiquer qu'on ignore les composants de capture
        
        # Afficher les détails de configuration
        logger.info(f"Configuration Flask: host={host}, port={port}")
        logger.info(f"Template folder: {app.template_folder}")
        logger.info(f"Static folder: {app.static_folder}")
        
        # Ajouter une route de test pour être sûr que Flask fonctionne
        @app.route('/flask-test')
        def flask_test():
            """Page de test pour Flask"""
            logger.info("Route /flask-test appelée")
            return """
            <html>
                <head><title>Flask Test</title></head>
                <body>
                    <h1>Flask fonctionne correctement</h1>
                    <p>Cette page confirme que le serveur Flask démarre correctement.</p>
                    <p><a href="/">Aller à la page d'accueil</a></p>
                </body>
            </html>
            """
        
        # Démarrer un thread pour ouvrir le navigateur quand le serveur est prêt
        # Si FLASK_HOST est 0.0.0.0, utiliser localhost pour l'URL du navigateur
        browser_host = "localhost" if host == "0.0.0.0" else host
        browser_url = f"http://{browser_host}:{port}/flask-test"
        
        browser_thread = threading.Thread(target=open_browser, args=(browser_url, 3))
        browser_thread.daemon = True
        browser_thread.start()
        
        # Démarrer le serveur Flask dans le thread principal
        run_flask_app(app, host, port)
        
    except KeyboardInterrupt:
        logger.info("Interruption clavier détectée. Arrêt du serveur...")
    except Exception as e:
        logger.error(f"Erreur globale: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
