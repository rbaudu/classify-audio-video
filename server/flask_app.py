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
            
            # Créer un fichier index.html de base s'il n'existe pas
            index_path = os.path.join(templates_dir, 'index.html')
            if not os.path.exists(index_path):
                with open(index_path, 'w') as f:
                    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Classify Audio Video</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Classify Audio Video</h1>
    <p>Le serveur fonctionne correctement.</p>
    <p><a href="/dashboard">Accéder au tableau de bord</a></p>
</body>
</html>""")
                logger.info(f"Fichier index.html de base créé: {index_path}")
            
            # Créer un fichier error.html de base
            error_path = os.path.join(templates_dir, 'error.html')
            if not os.path.exists(error_path):
                with open(error_path, 'w') as f:
                    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Erreur - Classify Audio Video</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #cc0000; }
    </style>
</head>
<body>
    <h1>Erreur</h1>
    <p>{{ message }}</p>
    <p><a href="/">Retour à l'accueil</a></p>
</body>
</html>""")
                logger.info(f"Fichier error.html de base créé: {error_path}")
            
            # Créer des templates basiques pour toutes les routes définies
            templates_basiques = {
                'dashboard.html': """<!DOCTYPE html>
<html>
<head>
    <title>Tableau de bord - Classify Audio Video</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Tableau de bord</h1>
    <p>Visualisation des activités courantes.</p>
    <p><a href="/">Retour à l'accueil</a></p>
</body>
</html>""",
                'statistics.html': """<!DOCTYPE html>
<html>
<head>
    <title>Statistiques - Classify Audio Video</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Statistiques</h1>
    <p>Statistiques des activités détectées.</p>
    <p><a href="/">Retour à l'accueil</a></p>
</body>
</html>""",
                'history.html': """<!DOCTYPE html>
<html>
<head>
    <title>Historique - Classify Audio Video</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Historique</h1>
    <p>Historique des activités détectées.</p>
    <p><a href="/">Retour à l'accueil</a></p>
</body>
</html>""",
                'model_testing.html': """<!DOCTYPE html>
<html>
<head>
    <title>Test du modèle - Classify Audio Video</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Test et entrainement du modèle</h1>
    <p>Interface de test du modèle de classification.</p>
    <p><a href="/">Retour à l'accueil</a></p>
</body>
</html>""",
                'settings.html': """<!DOCTYPE html>
<html>
<head>
    <title>Paramètres - Classify Audio Video</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Paramètres</h1>
    <p>Configuration de l'application.</p>
    <p><a href="/">Retour à l'accueil</a></p>
</body>
</html>""",
                '404.html': """<!DOCTYPE html>
<html>
<head>
    <title>Page non trouvée - Classify Audio Video</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #cc0000; }
    </style>
</head>
<body>
    <h1>Page non trouvée (404)</h1>
    <p>La page demandée n'existe pas.</p>
    <p><a href="/">Retour à l'accueil</a></p>
</body>
</html>""",
                '500.html': """<!DOCTYPE html>
<html>
<head>
    <title>Erreur serveur - Classify Audio Video</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #cc0000; }
    </style>
</head>
<body>
    <h1>Erreur serveur (500)</h1>
    <p>Une erreur s'est produite sur le serveur.</p>
    <p><a href="/">Retour à l'accueil</a></p>
</body>
</html>"""
            }
            
            # Créer chaque template basique
            for template_name, template_content in templates_basiques.items():
                template_path = os.path.join(templates_dir, template_name)
                if not os.path.exists(template_path):
                    with open(template_path, 'w') as f:
                        f.write(template_content)
                    logger.info(f"Fichier {template_name} de base créé: {template_path}")
            
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
            
            # Créer un fichier CSS de base
            css_dir = os.path.join(static_dir, 'css')
            os.makedirs(css_dir, exist_ok=True)
            with open(os.path.join(css_dir, 'style.css'), 'w') as f:
                f.write("""/* Style de base */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}
header {
    background-color: #333;
    color: white;
    padding: 10px 0;
}
""")
            
            # Créer un fichier JS de base
            js_dir = os.path.join(static_dir, 'js')
            os.makedirs(js_dir, exist_ok=True)
            with open(os.path.join(js_dir, 'main.js'), 'w') as f:
                f.write("""// Script principal
document.addEventListener('DOMContentLoaded', function() {
    console.log('Application chargée');
});
""")
            
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
        try:
            if os.path.exists(os.path.join(templates_dir, 'index.html')):
                return render_template('index.html')
            else:
                return """
                <html>
                  <head><title>Classify Audio Video - Test Page</title></head>
                  <body>
                    <h1>Le serveur fonctionne!</h1>
                    <p>Cette page confirme que le serveur Flask est en cours d'exécution.</p>
                    <p>Mais les templates ne sont pas disponibles.</p>
                  </body>
                </html>
                """
        except Exception as e:
            logger.error(f"Erreur lors du rendu de la page de test: {e}")
            return f"<h1>Erreur</h1><p>{str(e)}</p>"
    
    # Gestion des erreurs
    @app.errorhandler(404)
    def page_not_found(e):
        """Page 404 personnalisée"""
        try:
            if os.path.exists(os.path.join(templates_dir, '404.html')):
                return render_template('404.html'), 404
            else:
                return "<h1>Page non trouvée (404)</h1><p>La page demandée n'existe pas.</p>", 404
        except Exception as ex:
            logger.error(f"Erreur lors du rendu de la page 404: {ex}")
            return "<h1>Page non trouvée (404)</h1>", 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Page 500 personnalisée"""
        logger.error(f"Erreur 500: {e}")
        try:
            if os.path.exists(os.path.join(templates_dir, '500.html')):
                return render_template('500.html'), 500
            else:
                return "<h1>Erreur serveur (500)</h1><p>Une erreur s'est produite sur le serveur.</p>", 500
        except Exception as ex:
            logger.error(f"Erreur lors du rendu de la page 500: {ex}")
            return "<h1>Erreur serveur (500)</h1>", 500
    
    return app
