#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour corriger les problèmes de routes Flask
"""

import os
import sys
import shutil
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_routes.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def backup_file(file_path):
    """Créer une sauvegarde d'un fichier"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.bak"
        try:
            # Vérifier si une sauvegarde existe déjà
            if not os.path.exists(backup_path):
                shutil.copy2(file_path, backup_path)
                logger.info(f"Sauvegarde créée: {backup_path}")
            else:
                logger.info(f"Sauvegarde existe déjà: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sauvegarde: {e}")
    else:
        logger.error(f"Le fichier {file_path} n'existe pas")
    return False

def fix_flask_app_py():
    """Corrige flask_app.py pour traiter correctement l'enregistrement des routes"""
    file_path = "server/flask_app.py"
    
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ajouter une méthode explicite d'enregistrement des routes
        if "def register_routes(app):" not in content:
            # Trouver l'endroit où insérer le nouveau code
            insert_after = "app.config['TEMPLATES_AUTO_RELOAD'] = True"
            insert_index = content.find(insert_after)
            
            if insert_index > 0:
                insert_index += len(insert_after)
                
                new_code = """
    
    # Enregistrement explicite des routes pour s'assurer qu'elles sont disponibles
    from server.routes.web_routes import register_web_routes
    from server.routes.api_routes import register_api_routes
    
    # Enregistrer les routes web de base sans dépendances
    try:
        register_web_routes(app)
        logger.info("Routes web enregistrées avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement des routes web: {e}")
        # Ajouter des routes de secours en cas d'échec
        @app.route('/')
        def index_fallback():
            return \"\"\"
            <html>
                <head><title>Classify Audio Video</title></head>
                <body>
                    <h1>Classify Audio Video</h1>
                    <p>Page d'accueil de secours (fallback)</p>
                    <p>La page normale n'a pas pu être chargée.</p>
                    <p><a href="/dashboard">Tableau de bord</a> | 
                       <a href="/statistics">Statistiques</a> | 
                       <a href="/history">Historique</a></p>
                </body>
            </html>
            \"\"\"
"""
                
                content = content[:insert_index] + new_code + content[insert_index:]
                logger.info("Ajout d'un enregistrement de routes explicite dans flask_app.py")
        
        # Écrire les modifications
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Fichier {file_path} modifié avec succès")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de la modification de {file_path}: {e}")
        return False

def fix_web_routes_py():
    """Corrige web_routes.py pour assurer que les routes fonctionnent même sans dépendances"""
    file_path = "server/routes/web_routes.py"
    
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ajouter un gestionnaire d'erreurs global pour les routes
        if "except Exception as e:" not in content:
            modified_content = ""
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                modified_content += line + '\n'
                
                # Trouver les fonctions de route
                if "@app.route(" in line and "def " in lines[i+1]:
                    route_name = lines[i+1].strip()
                    if "except Exception as e:" not in ''.join(lines[i:i+15]):
                        j = i + 2
                        indent = ""
                        # Trouver l'indentation
                        while j < len(lines) and (not lines[j].strip() or lines[j].startswith(' ')):
                            if lines[j].strip():
                                indent = ' ' * (len(lines[j]) - len(lines[j].lstrip()))
                                break
                            j += 1
                        
                        # Si on trouve une ligne qui retourne quelque chose, ajoutez un try-except
                        if j < len(lines) and "return" in lines[j]:
                            indented_return = lines[j]
                            modified_content += f"{indent}try:\n"
                            modified_content += f"{indent}    {indented_return.strip()}\n"
                            modified_content += f"{indent}except Exception as e:\n"
                            modified_content += f"{indent}    logger.error(f\"Erreur dans {route_name}: {{e}}\")\n"
                            modified_content += f"{indent}    return render_template('error.html', message=f\"Erreur lors du chargement de la page: {{e}}\"), 500\n"
                            # Sauter la ligne de retour originale
                            i += 1
                            continue
            
            if modified_content != content:
                content = modified_content
                logger.info("Ajout de gestionnaires d'erreurs pour les routes dans web_routes.py")
        
        # Écrire les modifications
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Fichier {file_path} modifié avec succès")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de la modification de {file_path}: {e}")
        return False

def fix_main_py():
    """Corrige main.py pour éviter les problèmes d'initialisation des routes"""
    file_path = "server/main.py"
    
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ajouter une vérification pour le flag BYPASS_INIT
        if "app.config.get('BYPASS_INIT')" not in content:
            # Trouver l'endroit où les routes sont enregistrées
            register_api_routes_index = content.find("register_api_routes(app")
            register_web_routes_index = content.find("register_web_routes(app")
            
            if register_api_routes_index > 0 and register_web_routes_index > 0:
                # Modification pour les routes API
                api_routes_line = content[register_api_routes_index:content.find(")", register_api_routes_index) + 1]
                new_api_routes_line = f"# Enregistrement des routes API\n    if not app.config.get('BYPASS_INIT'):\n        {api_routes_line}"
                content = content.replace(api_routes_line, new_api_routes_line)
                
                # Modification pour les routes web
                web_routes_line = content[register_web_routes_index:content.find(")", register_web_routes_index) + 1]
                content = content.replace(web_routes_line, f"# Enregistrement des routes Web\n    {web_routes_line}")
                
                logger.info("Ajout d'une vérification BYPASS_INIT dans main.py")
                
                # Écrire les modifications
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"Fichier {file_path} modifié avec succès")
                return True
    
    except Exception as e:
        logger.error(f"Erreur lors de la modification de {file_path}: {e}")
    
    return False

def create_missing_static_files():
    """Crée les fichiers statiques manquants"""
    static_dir = os.path.join("web", "static")
    css_dir = os.path.join(static_dir, "css")
    js_dir = os.path.join(static_dir, "js")
    
    # Créer les dossiers s'ils n'existent pas
    os.makedirs(css_dir, exist_ok=True)
    os.makedirs(js_dir, exist_ok=True)
    
    # Créer style.css si manquant
    css_file = os.path.join(css_dir, "style.css")
    if not os.path.exists(css_file):
        try:
            with open(css_file, 'w', encoding='utf-8') as f:
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
.nav {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    justify-content: center;
}
.nav li {
    margin: 0 10px;
}
.nav a {
    color: white;
    text-decoration: none;
}
.nav a:hover {
    text-decoration: underline;
}
main {
    padding: 20px;
}
.card {
    background: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 20px;
    margin-bottom: 20px;
}
h1, h2, h3 {
    color: #333;
}
.btn {
    display: inline-block;
    padding: 8px 16px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-decoration: none;
}
.btn:hover {
    background-color: #45a049;
}""")
            logger.info(f"Fichier CSS créé: {css_file}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du fichier CSS: {e}")
    
    # Créer main.js si manquant
    js_file = os.path.join(js_dir, "main.js")
    if not os.path.exists(js_file):
        try:
            with open(js_file, 'w', encoding='utf-8') as f:
                f.write("""// Script principal
document.addEventListener('DOMContentLoaded', function() {
    console.log('Application classify-audio-video chargée');
    
    // Fonction pour afficher des messages d'erreur
    window.showError = function(message) {
        alert('Erreur: ' + message);
    };
    
    // Fonction pour afficher des messages de succès
    window.showSuccess = function(message) {
        alert('Succès: ' + message);
    };
});""")
            logger.info(f"Fichier JavaScript créé: {js_file}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du fichier JavaScript: {e}")

def main():
    """Fonction principale"""
    logger.info("=== Script de correction des routes Flask ===")
    
    # Vérifier les prérequis
    if not os.path.exists("server/flask_app.py"):
        logger.error("Erreur: server/flask_app.py introuvable")
        return 1
    
    if not os.path.exists("server/routes/web_routes.py"):
        logger.error("Erreur: server/routes/web_routes.py introuvable")
        return 1
    
    if not os.path.exists("server/main.py"):
        logger.error("Erreur: server/main.py introuvable")
        return 1
    
    # Créer les fichiers statiques manquants
    create_missing_static_files()
    
    # Appliquer les modifications
    flask_app_fixed = fix_flask_app_py()
    web_routes_fixed = fix_web_routes_py()
    main_fixed = fix_main_py()
    
    if flask_app_fixed and web_routes_fixed and main_fixed:
        logger.info("\nCorrections des routes appliquées avec succès!")
        logger.info("Vous pouvez maintenant démarrer le serveur avec une des méthodes suivantes:")
        logger.info("  1. python run.py             (serveur complet avec capture)")
        logger.info("  2. python flask_server_only.py  (serveur Flask uniquement)")
        
        # Demander si l'utilisateur veut tester le serveur maintenant
        try:
            response = input("\nVoulez-vous tester le serveur maintenant? (o/n): ")
            if response.lower() in ['o', 'oui', 'y', 'yes']:
                logger.info("\nDémarrage du serveur Flask uniquement...")
                import flask_server_only
                flask_server_only.main()
        except KeyboardInterrupt:
            logger.info("\nTest annulé")
    else:
        logger.error("\nDes erreurs sont survenues lors de l'application des corrections")
        logger.error("Consultez les logs pour plus de détails")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
