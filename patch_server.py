#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de correction des problèmes du serveur Flask et de la gestion CTRL+C
"""

import os
import sys
import shutil
import subprocess
import time
import platform

def backup_file(file_path):
    """Créer une sauvegarde d'un fichier"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.bak"
        try:
            shutil.copy2(file_path, backup_path)
            print(f"Sauvegarde créée: {backup_path}")
            return True
        except Exception as e:
            print(f"Erreur lors de la création de la sauvegarde: {e}")
    else:
        print(f"Le fichier {file_path} n'existe pas")
    return False

def patch_run_py():
    """Corrige le fichier run.py pour résoudre le problème CTRL+C"""
    file_path = "run.py"
    
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Correction 1: Modification de shutdown_server pour utiliser sys.exit
        if "os._exit(0)" in content:
            content = content.replace(
                "os._exit(0)", 
                "sys.exit(0)"
            )
            print("Correction appliquée: Remplacement de os._exit(0) par sys.exit(0)")
        
        # Correction 2: Modification du thread daemon
        if "daemon=True" in content:
            content = content.replace(
                "daemon=True", 
                "daemon=False"
            )
            print("Correction appliquée: Changement du thread Flask en non-daemon")
        
        # Écrire les modifications
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fichier {file_path} patché avec succès")
        return True
    
    except Exception as e:
        print(f"Erreur lors du patch de {file_path}: {e}")
        return False

def patch_flask_app_py():
    """Corrige le fichier flask_app.py pour résoudre le problème de l'IHM"""
    file_path = "server/flask_app.py"
    
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ajout d'une méthode de test pour Flask
        if "def test_page" not in content:
            # Trouver l'endroit où insérer le nouveau code (juste avant le return app)
            insert_index = content.rfind("return app")
            if insert_index > 0:
                new_code = """
    # Ajouter une route de test spécifique
    @app.route('/flask-test')
    def test_page_patched():
        \"\"\"Page de test pour vérifier que l'application fonctionne\"\"\"
        return \"\"\"
        <html>
            <head><title>Flask Test (Patched)</title></head>
            <body>
                <h1>Le serveur Flask fonctionne!</h1>
                <p>Cette page confirme que le serveur Flask est correctement patché et en cours d'exécution.</p>
                <p><a href="/">Aller à la page d'accueil</a></p>
            </body>
        </html>
        \"\"\"
    
    """
                # Insérer la nouvelle route avant le return
                content = content[:insert_index] + new_code + content[insert_index:]
                print("Correction appliquée: Ajout d'une route de test Flask")
        
        # Écrire les modifications
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fichier {file_path} patché avec succès")
        return True
    
    except Exception as e:
        print(f"Erreur lors du patch de {file_path}: {e}")
        return False

def create_missing_templates():
    """Crée les templates manquants si nécessaire"""
    templates_dir = os.path.join("web", "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    # Liste des templates basiques à créer s'ils n'existent pas
    basic_templates = {
        "index.html": """<!DOCTYPE html>
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
    <p>Le serveur fonctionne correctement (patché).</p>
    <p><a href="/dashboard">Accéder au tableau de bord</a></p>
</body>
</html>""",
        
        "error.html": """<!DOCTYPE html>
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
</html>"""
    }
    
    # Créer chaque template s'il n'existe pas
    for template_name, content in basic_templates.items():
        template_path = os.path.join(templates_dir, template_name)
        if not os.path.exists(template_path):
            try:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Template créé: {template_path}")
            except Exception as e:
                print(f"Erreur lors de la création du template {template_name}: {e}")
    
    print("Vérification des templates terminée")

def main():
    """Fonction principale"""
    print("=== Script de correction des problèmes du serveur ===")
    
    # Vérifier si les fichiers cibles existent
    if not os.path.exists("run.py"):
        print("Erreur: run.py introuvable dans le répertoire courant")
        return 1
    
    if not os.path.exists("server/flask_app.py"):
        print("Erreur: server/flask_app.py introuvable")
        return 1
    
    # Appliquer les patchs
    run_patched = patch_run_py()
    flask_patched = patch_flask_app_py()
    
    # Créer les templates manquants si nécessaire
    create_missing_templates()
    
    if run_patched and flask_patched:
        print("\nPatchs appliqués avec succès!")
        print("Vous pouvez maintenant démarrer le serveur avec:")
        print("  python run.py")
        print("Ou utiliser l'une des méthodes alternatives:")
        print("  python flask_server_only.py  (serveur Flask uniquement)")
        print("  python debug_flask.py         (débogage minimal de Flask)")
        print("  python kill_and_start.py      (solution radicale)")
        
        # Demander si l'utilisateur veut tester le serveur maintenant
        try:
            response = input("\nVoulez-vous tester le serveur maintenant? (o/n): ")
            if response.lower() in ['o', 'oui', 'y', 'yes']:
                print("\nDémarrage du serveur...")
                subprocess.run([sys.executable, "flask_server_only.py"])
        except KeyboardInterrupt:
            print("\nTest annulé")
    else:
        print("\nDes erreurs sont survenues lors de l'application des patchs")
        print("Vérifiez les messages d'erreur et essayez de résoudre les problèmes manuellement")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
