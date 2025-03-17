# -*- coding: utf-8 -*-
"""
Initialisation de l'application Flask
"""

import os
import logging
from flask import Flask

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
    else:
        logger.info(f"Les templates disponibles: {os.listdir(templates_dir)}")
    
    if not os.path.exists(static_dir):
        logger.error(f"Le répertoire statique n'existe pas: {static_dir}")
    
    # Création de l'application Flask avec les paramètres absolus
    app = Flask(
        __name__,
        static_folder=static_dir,
        template_folder=templates_dir
    )
    
    # Configuration de l'application
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    return app
