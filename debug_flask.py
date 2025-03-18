#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de débogage spécifique pour le serveur Flask
Ce script se concentre uniquement sur le démarrage de Flask avec une configuration minimale
"""

import os
import sys
import logging
import webbrowser
import time
import threading
import requests
from flask import Flask, render_template

# Configuration du logging pour voir tous les détails
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flask_debug.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Variables globales
FLASK_HOST = '0.0.0.0'  # Écouter sur toutes les interfaces
FLASK_PORT = 5000       # Port standard Flask

def create_minimal_app():
    """Crée une application Flask minimale pour tester le démarrage du serveur"""
    
    # Trouver le chemin des templates
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(script_dir, 'web', 'templates')
    static_dir = os.path.join(script_dir, 'web', 'static')
    
    # Vérifier si les dossiers existent
    logger.info(f"Chemin des templates: {templates_dir}")
    logger.info(f"Chemin des fichiers statiques: {static_dir}")
    
    if not os.path.exists(templates_dir):
        logger.error(f"Le dossier des templates n'existe pas: {templates_dir}")
        # Créer un dossier minimal de templates
        try:
            os.makedirs(templates_dir, exist_ok=True)
            with open(os.path.join(templates_dir, 'debug.html'), 'w') as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Debug Flask</title>
</head>
<body>
    <h1>Flask fonctionne!</h1>
    <p>Cette page confirme que le serveur Flask démarre correctement.</p>
</body>
</html>""")
            logger.info(f"Créé un template de débogage: {os.path.join(templates_dir, 'debug.html')}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du template de débogage: {e}")
    
    # Créer l'application Flask
    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir
    )
    
    # Route de débogage
    @app.route('/debug')
    def debug_page():
        logger.info("Route /debug appelée")
        if os.path.exists(os.path.join(templates_dir, 'debug.html')):
            return render_template('debug.html')
        else:
            return """
            <html>
                <head><title>Debug Flask</title></head>
                <body>
                    <h1>Flask fonctionne!</h1>
                    <p>Cette page confirme que le serveur Flask démarre correctement.</p>
                </body>
            </html>
            """
    
    # Route principale
    @app.route('/')
    def index():
        logger.info("Route / appelée")
        try:
            if os.path.exists(os.path.join(templates_dir, 'index.html')):
                return render_template('index.html')
            else:
                return """
                <html>
                    <head><title>Debug Flask</title></head>
                    <body>
                        <h1>Flask fonctionne!</h1>
                        <p>Cette page confirme que le serveur Flask démarre correctement.</p>
                        <p>Note: Le template index.html n'a pas été trouvé.</p>
                    </body>
                </html>
                """
        except Exception as e:
            logger.error(f"Erreur lors du rendu de la page index: {str(e)}")
            return f"<h1>Erreur</h1><p>{str(e)}</p>"
    
    return app

def open_browser_when_ready(url, max_attempts=30):
    """Tente d'ouvrir le navigateur une fois que le serveur est prêt"""
    logger.info(f"Tentative d'ouverture du navigateur à {url}")
    
    for i in range(max_attempts):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                logger.info(f"Serveur prêt après {i+1} tentatives, ouverture du navigateur")
                webbrowser.open(url)
                break
        except requests.exceptions.RequestException:
            logger.info(f"Tentative {i+1}/{max_attempts} : serveur pas encore prêt")
            time.sleep(1)
    else:
        logger.error(f"Impossible d'accéder au serveur après {max_attempts} tentatives")

def main():
    """Fonction principale"""
    try:
        logger.info("Démarrage du script de débogage Flask")
        
        # Créer l'application Flask
        app = create_minimal_app()
        
        # Démarrer un thread pour ouvrir le navigateur quand le serveur est prêt
        browser_url = f"http://localhost:{FLASK_PORT}/debug"
        browser_thread = threading.Thread(target=open_browser_when_ready, args=(browser_url,))
        browser_thread.daemon = True
        browser_thread.start()
        
        # Démarrer le serveur Flask
        logger.info(f"Démarrage du serveur Flask sur {FLASK_HOST}:{FLASK_PORT}")
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True, use_reloader=False)
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur Flask: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
