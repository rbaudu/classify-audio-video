#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# Ajout du chemin du projet au sys.path pour résoudre les problèmes d'importation
project_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_path)

# Affichage des informations de débogage
print(f"Chemin du projet ajouté: {project_path}")
print(f"sys.path contient maintenant: {sys.path}")

# Importation et exécution de l'application Flask
from server.main import app

if __name__ == "__main__":
    print("Démarrage du serveur classify-audio-video...")
    print("Accédez à l'interface via http://localhost:5000")
    print("Appuyez sur Ctrl+C pour arrêter le serveur")
    
    # Lancement du serveur Flask en mode debug
    app.run(host='0.0.0.0', port=5000, debug=True)
