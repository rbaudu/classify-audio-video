#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour corriger l'indentation dans run.py
"""

import os
import sys
import re
import shutil

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

def fix_indentation():
    """Corrige l'indentation dans run.py"""
    filepath = 'run.py'
    
    if not os.path.exists(filepath):
        print(f"Erreur: {filepath} n'existe pas")
        return False
    
    # Créer une sauvegarde
    if not backup_file(filepath):
        return False
    
    try:
        # Lire le contenu ligne par ligne
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        in_main_loop = False
        
        for i, line in enumerate(lines):
            # Détecter la boucle principale
            if "while True:" in line:
                in_main_loop = True
                # Trouver l'indentation actuelle
                indentation_match = re.match(r'^(\s+)', line)
                if indentation_match:
                    indentation = indentation_match.group(1)
                else:
                    indentation = ""
                
                # Ajouter le bloc try correctement indenté
                fixed_lines.append(f"{indentation}try:\n")
                fixed_lines.append(line)
                continue
            
            # Si on est dans la boucle principale et qu'on trouve un "except"
            # ou si l'indentation revient au niveau précédent, sortir du mode boucle
            if in_main_loop:
                if "except KeyboardInterrupt:" in line or (i > 0 and line.strip() and len(line) - len(line.lstrip()) <= len(indentation)):
                    in_main_loop = False
            
            fixed_lines.append(line)
        
        # Écrire le contenu corrigé
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"L'indentation dans {filepath} a été corrigée avec succès")
        
        # Alternative: Au lieu de corriger l'indentation, remplacer directement le bloc problématique
        # C'est plus fiable mais moins "intelligent"
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Trouver et remplacer le bloc problématique
        pattern = r'# Maintenir le thread principal en vie[^\n]*\ntry:\n\s*while True:[^\n]*\n'
        replacement = """# Maintenir le thread principal en vie jusqu'à un CTRL+C ou une erreur
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interruption clavier détectée dans la boucle principale. Arrêt du serveur...")
            shutdown_server()
    """
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            
            # Écrire le contenu modifié
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Le bloc problématique dans {filepath} a été remplacé avec succès")
        
        return True
    
    except Exception as e:
        print(f"Erreur lors de la correction de {filepath}: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def direct_fix():
    """Correction directe du fichier run.py"""
    filepath = 'run.py'
    
    if not os.path.exists(filepath):
        print(f"Erreur: {filepath} n'existe pas")
        return False
    
    # Créer une sauvegarde
    if not backup_file(filepath):
        return False
    
    try:
        # Lire le contenu
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Corriger os._exit
        if 'os._exit(0)' in content:
            content = content.replace('os._exit(0)', 'sys.exit(0)')
            print("• Correction: os._exit(0) -> sys.exit(0)")
        
        # Corriger daemon=True
        if 'daemon=True' in content:
            content = content.replace('daemon=True', 'daemon=False')
            print("• Correction: daemon=True -> daemon=False")
        
        # Remplacer la boucle principale
        main_loop_replacement = """        # Maintenir le thread principal en vie jusqu'à un CTRL+C ou une erreur
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            # Cette partie sera exécutée si CTRL+C est pressé
            logger.info("Interruption clavier détectée. Arrêt du serveur...")
            shutdown_server()"""
        
        # Trouver la boucle principale (plusieurs possibilités)
        patterns = [
            r"# Maintenir le thread principal[^\n]*\n\s*while True:[^\n]*\n\s*time\.sleep\(1\)",
            r"# Maintenir le thread principal[^\n]*\n\s*try:[^\n]*\n\s*while True:",
            r"while True:[^\n]*\n\s*time\.sleep\(1\)"
        ]
        
        for pattern in patterns:
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, main_loop_replacement, content, flags=re.DOTALL)
                print(f"• Correction: Remplacement de la boucle principale")
                break
        
        # Écrire le contenu corrigé
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\nLe fichier {filepath} a été corrigé avec succès")
        return True
    
    except Exception as e:
        print(f"Erreur lors de la correction directe de {filepath}: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Fonction principale"""
    print("\n=== Correction de l'indentation dans run.py ===\n")
    
    # Essayer d'abord la correction directe (plus fiable)
    if direct_fix():
        print("\nCorrection directe réussie.")
    # Si ça échoue, essayer la correction d'indentation
    elif fix_indentation():
        print("\nCorrection d'indentation réussie.")
    else:
        print("\nÉchec de la correction.")
        return 1
    
    print("\nVous pouvez maintenant utiliser:")
    print("  python simple_start.py")
    print("pour lancer l'application.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
