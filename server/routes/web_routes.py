# -*- coding: utf-8 -*-
"""
Routes Web pour le serveur Flask
"""

import logging
import os
from flask import render_template, redirect, url_for, current_app

logger = logging.getLogger(__name__)

def register_web_routes(app):
    """Enregistre les routes Web pour l'application Flask
    
    Args:
        app (Flask): Application Flask
    """
    
    @app.route('/')
    def index():
        """Page d'accueil
        
        Returns:
            Response: Rendu du template index.html
        """
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Erreur lors du rendu de index.html: {str(e)}")
            return render_template('error.html', message="Impossible de charger la page d'accueil."), 500
    
    @app.route('/dashboard')
    def dashboard():
        """Tableau de bord des activités
        
        Returns:
            Response: Rendu du template dashboard.html
        """
        try:
            return render_template('dashboard.html')
        except Exception as e:
            logger.error(f"Erreur lors du rendu de dashboard.html: {str(e)}")
            return render_template('error.html', message="Impossible de charger le tableau de bord."), 500
    
    @app.route('/statistics')
    def statistics():
        """Statistiques des activités
        
        Returns:
            Response: Rendu du template statistics.html
        """
        try:
            return render_template('statistics.html')
        except Exception as e:
            logger.error(f"Erreur lors du rendu de statistics.html: {str(e)}")
            return render_template('error.html', message="Impossible de charger les statistiques."), 500
    
    @app.route('/history')
    def history():
        """Historique des activités
        
        Returns:
            Response: Rendu du template history.html
        """
        try:
            return render_template('history.html')
        except Exception as e:
            logger.error(f"Erreur lors du rendu de history.html: {str(e)}")
            return render_template('error.html', message="Impossible de charger l'historique."), 500
    
    @app.route('/model_testing')
    def model_testing():
        """Page de test du modèle
        
        Returns:
            Response: Rendu du template model_testing.html
        """
        try:
            return render_template('model_testing.html')
        except Exception as e:
            logger.error(f"Erreur lors du rendu de model_testing.html: {str(e)}")
            return render_template('error.html', message="Impossible de charger le test du modèle."), 500
    
    @app.route('/settings')
    def settings():
        """Page de paramètres
        
        Returns:
            Response: Rendu du template settings.html
        """
        try:
            return render_template('settings.html')
        except Exception as e:
            logger.error(f"Erreur lors du rendu de settings.html: {str(e)}")
            return render_template('error.html', message="Impossible de charger les paramètres."), 500
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Gestionnaire d'erreur 404
        
        Args:
            e (Exception): Exception d'erreur
        
        Returns:
            Response: Rendu du template 404.html ou error.html
        """
        try:
            return render_template('404.html'), 404
        except Exception as ex:
            logger.error(f"Erreur lors du rendu de 404.html, utilisation de error.html: {str(ex)}")
            return render_template('error.html', message="Page non trouvée."), 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Gestionnaire d'erreur 500
        
        Args:
            e (Exception): Exception d'erreur
        
        Returns:
            Response: Rendu du template 500.html ou error.html
        """
        logger.error(f"Erreur serveur: {str(e)}")
        try:
            return render_template('500.html'), 500
        except Exception as ex:
            logger.error(f"Erreur lors du rendu de 500.html, utilisation de error.html: {str(ex)}")
            return render_template('error.html', message="Erreur serveur interne."), 500
