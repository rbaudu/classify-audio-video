#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script qui corrige directement le problème d'arrêt CTRL+C dans run.py
"""

import os
import sys
import shutil
import re

def backup_file(filepath):
    """Crée une sauvegarde du fichier s'il n'en existe pas déjà une"""
    backup_path = filepath + '.bak'
    if not os.path.exists(backup_path):
        print(f"Création d'une sauvegarde de {filepath}")
        shutil.copy2(filepath, backup_path)
        return True
    else:
        print(f"Une sauvegarde existe déjà: {backup_path}")
        return True
    return False

def fix_run_py():
    """Corrige les problèmes dans run.py"""
    filepath = 'run.py'
    
    if not os.path.exists(filepath):
        print(f"Erreur: {filepath} n'existe pas")
        return False
    
    # Créer une sauvegarde
    if not backup_file(filepath):
        return False
    
    try:
        # Lire le contenu du fichier
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Remplacer os._exit(0) par sys.exit(0)
        if 'os._exit(0)' in content:
            content = content.replace('os._exit(0)', 'sys.exit(0)')
            print("• Correction appliquée: Remplacement de os._exit(0) par sys.exit(0)")
        
        # 2. Remplacer daemon=True par daemon=False
        if 'daemon=True' in content:
            content = content.replace('daemon=True', 'daemon=False')
            print("• Correction appliquée: Thread Flask défini en non-daemon")
        
        # 3. Améliorer le gestionnaire de signaux
        signal_handler_pattern = r'def signal_handler\(sig, frame\):[^}]*?shutdown_server\(\)'
        improved_handler = """def signal_handler(sig, frame):
    """
    Gestionnaire de signal pour CTRL+C (SIGINT) et SIGTERM
    """
    logger.info(f"Signal d'interruption reçu ({sig}). Arrêt du serveur...")
    
    # Permettre l'arrêt même si d'autres threads sont en cours
    if server_thread and server_thread.is_alive():
        logger.info("Attente de la fin du thread serveur...")
    
    # Appeler shutdown_server pour nettoyer et arrêter
    shutdown_server()"""
        
        if re.search(signal_handler_pattern, content, re.DOTALL):
            content = re.sub(signal_handler_pattern, improved_handler, content, flags=re.DOTALL)
            print("• Correction appliquée: Amélioration du gestionnaire de signal")
        
        # 4. Améliorer la boucle principale pour capturer CTRL+C
        main_loop_pattern = r'while True:[^}]*?time\.sleep\(1\)'
        improved_loop = """# Maintenir le thread principal en vie jusqu'à un CTRL+C ou une erreur
        # Ce bloc est crucial car il permet de capturer le CTRL+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interruption clavier détectée dans la boucle principale. Arrêt du serveur...")
            shutdown_server()"""
        
        if re.search(main_loop_pattern, content, re.DOTALL):
            content = re.sub(main_loop_pattern, improved_loop, content, flags=re.DOTALL)
            print("• Correction appliquée: Amélioration de la boucle principale")
        
        # Écrire le contenu modifié
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Le fichier {filepath} a été corrigé avec succès")
        return True
    
    except Exception as e:
        print(f"Erreur lors de la correction de {filepath}: {e}")
        return False

def main():
    """Fonction principale"""
    print("\n=== Script de correction du problème CTRL+C ===\n")
    
    if fix_run_py():
        print("\nCorrections appliquées avec succès!")
        print("Vous pouvez maintenant démarrer l'application avec la commande suivante:")
        print("\n   python run.py\n")
        print("Pour lancer l'application avec l'interface web automatiquement ouverte:")
        print("\n   python simple_start.py\n")
        print("L'arrêt avec CTRL+C devrait maintenant fonctionner correctement.")
    else:
        print("\nDes erreurs se sont produites lors de l'application des corrections.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
