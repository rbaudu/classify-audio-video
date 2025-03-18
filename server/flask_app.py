# -*- coding: utf-8 -*-
"""
Initialisation de l'application Flask
"""

import os
import logging
from flask import Flask, url_for, render_template
from server.config import Config

logger = logging.getLogger(__name__)

def create_app():
    """
    Crée et configure l'application Flask
    
    Returns:
        Flask: L'application Flask configurée
    """
    # Déterminer le chemin absolu du répertoire racine du projet
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Vérifier l'existence des dossiers
    templates_dir = os.path.join(root_dir, 'web', 'templates')
    static_dir = os.path.join(root_dir, 'web', 'static')
    
    logger.info(f"Chemin du répertoire racine: {root_dir}")
    logger.info(f"Chemin du répertoire des templates: {templates_dir}")
    logger.info(f"Chemin du répertoire statique: {static_dir}")
    
    # Vérifier si les dossiers existent
    if not os.path.exists(templates_dir):
        logger.error(f"Le répertoire des templates n'existe pas: {templates_dir}")
        # Créer le répertoire s'il n'existe pas
        try:
            os.makedirs(templates_dir, exist_ok=True)
            logger.info(f"Répertoire des templates créé: {templates_dir}")
        except Exception as e:
            logger.error(f"Impossible de créer le répertoire des templates: {e}")
    else:
        logger.info(f"Les templates disponibles: {os.listdir(templates_dir)}")
    
    if not os.path.exists(static_dir):
        logger.error(f"Le répertoire statique n'existe pas: {static_dir}")
        # Créer le répertoire s'il n'existe pas
        try:
            os.makedirs(static_dir, exist_ok=True)
            logger.info(f"Répertoire statique créé: {static_dir}")
        except Exception as e:
            logger.error(f"Impossible de créer le répertoire statique: {e}")
    
    # Création de l'application Flask avec les paramètres absolus
    app = Flask(
        __name__,
        static_folder=static_dir,
        template_folder=templates_dir
    )
    
    # Configuration de l'application
    app.config['DEBUG'] = Config.DEBUG
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Ajouter une route de base pour s'assurer que Flask fonctionne
    @app.route('/test')
    def test_page():
        """Page de test simple pour vérifier que l'application fonctionne"""
        return render_template('index.html') if os.path.exists(os.path.join(templates_dir, 'index.html')) else \
               """
               <html>
                 <head><title>Classify Audio Video - Test Page</title></head>
                 <body>
                   <h1>Le serveur fonctionne!</h1>
                   <p>Cette page confirme que le serveur Flask est en cours d'exécution.</p>
                   <p>Mais les templates ne sont pas disponibles.</p>
                 </body>
               </html>
               """
    
    # Gestion des erreurs
    @app.errorhandler(404)
    def page_not_found(e):
        """Page 404 personnalisée"""
        return render_template('404.html') if os.path.exists(os.path.join(templates_dir, '404.html')) else \
               "<h1>Page non trouvée (404)</h1><p>La page demandée n'existe pas.</p>", 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Page 500 personnalisée"""
        logger.error(f"Erreur 500: {e}")
        return render_template('500.html') if os.path.exists(os.path.join(templates_dir, '500.html')) else \
               "<h1>Erreur serveur (500)</h1><p>Une erreur s'est produite sur le serveur.</p>", 500
    
    return app
