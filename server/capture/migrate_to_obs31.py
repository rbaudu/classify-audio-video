# -*- coding: utf-8 -*-
"""
Script utilitaire pour faciliter la migration de OBSCapture vers OBS31Capture
"""

import importlib
import logging
import os
import re
import sys

logger = logging.getLogger(__name__)

def analyze_imports(file_path):
    """Analyse les imports d'un fichier Python pour détecter les références à OBSCapture
    
    Args:
        file_path (str): Chemin du fichier à analyser
        
    Returns:
        dict: Informations sur les imports détectés
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Détecter les imports de OBSCapture
        obs_capture_import = re.findall(r'from\s+server\.capture\.obs_capture\s+import\s+OBSCapture', content)
        obs_capture_aliases = re.findall(r'import\s+server\.capture\.obs_capture\s+as\s+(\w+)', content)
        
        # Détecter les imports de modules associés
        obs_events_import = re.findall(r'from\s+server\.capture\.obs_events\s+import', content)
        obs_media_import = re.findall(r'from\s+server\.capture\.obs_media\s+import', content)
        obs_sources_import = re.findall(r'from\s+server\.capture\.obs_sources\s+import', content)
        
        # Détecter les instanciations de OBSCapture
        instances = re.findall(r'=\s*OBSCapture\(', content)
        
        return {
            'file': file_path,
            'obs_capture_import': bool(obs_capture_import),
            'obs_capture_aliases': obs_capture_aliases,
            'obs_events_import': bool(obs_events_import),
            'obs_media_import': bool(obs_media_import),
            'obs_sources_import': bool(obs_sources_import),
            'instances': len(instances)
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du fichier {file_path}: {e}")
        return {
            'file': file_path,
            'error': str(e)
        }

def suggest_migration(analysis):
    """Suggère des modifications pour migrer vers OBS31Capture
    
    Args:
        analysis (dict): Résultat de l'analyse du fichier
        
    Returns:
        list: Liste de suggestions de modifications
    """
    suggestions = []
    
    if 'error' in analysis:
        suggestions.append(f"ERREUR lors de l'analyse: {analysis['error']}")
        return suggestions
    
    file_path = analysis['file']
    
    # Import direct de OBSCapture
    if analysis['obs_capture_import']:
        suggestions.append(f"Modifier l'import dans {file_path} :")
        suggestions.append("  from server.capture.obs_capture import OBSCapture")
        suggestions.append("  ↓")
        suggestions.append("  from server.capture.obs_31_capture import OBS31Capture as OBSCapture  # Compatible OBS 31.0.2+")
    
    # Import avec alias
    if analysis['obs_capture_aliases']:
        for alias in analysis['obs_capture_aliases']:
            suggestions.append(f"Modifier l'import avec alias dans {file_path} :")
            suggestions.append(f"  import server.capture.obs_capture as {alias}")
            suggestions.append("  ↓")
            suggestions.append(f"  import server.capture.obs_31_capture as {alias}  # Compatible OBS 31.0.2+")
    
    # Utilisation des modules associés
    if analysis['obs_events_import']:
        suggestions.append(f"Remplacer l'utilisation de obs_events par obs_events_31 dans {file_path}")
    
    if analysis['obs_media_import']:
        suggestions.append(f"Remplacer l'utilisation de obs_media par obs_media_31 dans {file_path}")
    
    if analysis['obs_sources_import']:
        suggestions.append(f"Remplacer l'utilisation de obs_sources par obs_sources_31 dans {file_path}")
    
    # Instanciations
    if analysis['instances'] > 0:
        suggestions.append(f"Remplacer {analysis['instances']} instanciations de OBSCapture par OBS31Capture dans {file_path}")
        suggestions.append("  obs = OBSCapture(...)")
        suggestions.append("  ↓")
        suggestions.append("  obs = OBS31Capture(...)  # Compatible OBS 31.0.2+")
    
    # Si plusieurs modules sont utilisés, suggérer l'adaptateur
    if sum([analysis['obs_capture_import'] or len(analysis['obs_capture_aliases']) > 0,
           analysis['obs_events_import'], 
           analysis['obs_media_import'], 
           analysis['obs_sources_import']]) > 1:
        suggestions.append(f"Ce fichier utilise plusieurs modules OBS. Envisager d'utiliser OBS31Adapter:")
        suggestions.append("  from server.capture.obs_31_adapter import OBS31Adapter")
        suggestions.append("  obs = OBS31Adapter(host, port, password)  # Simplifie la gestion de tous les modules OBS 31.0.2+")
    
    return suggestions

def scan_directory(directory, extensions=None):
    """Analyse tous les fichiers d'un répertoire pour détecter les références à OBSCapture
    
    Args:
        directory (str): Répertoire à analyser
        extensions (list, optional): Extensions de fichiers à analyser. Par défaut ['.py']
        
    Returns:
        list: Liste des analyses de fichiers contenant des références à OBSCapture
    """
    if extensions is None:
        extensions = ['.py']
    
    results = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                analysis = analyze_imports(file_path)
                
                # Garder seulement les fichiers qui contiennent des références à OBSCapture
                if ('error' in analysis or 
                    analysis['obs_capture_import'] or 
                    analysis['obs_capture_aliases'] or 
                    analysis['obs_events_import'] or 
                    analysis['obs_media_import'] or 
                    analysis['obs_sources_import'] or 
                    analysis['instances']):
                    results.append(analysis)
    
    return results

def generate_migration_report(directory, output_file=None):
    """Génère un rapport de migration pour un répertoire
    
    Args:
        directory (str): Répertoire à analyser
        output_file (str, optional): Fichier de sortie pour le rapport. Par défaut None (affichage dans la console)
        
    Returns:
        str: Rapport de migration
    """
    try:
        # Scanner le répertoire
        results = scan_directory(directory)
        
        # Générer le rapport
        report = []
        report.append("=== Rapport de migration OBSCapture vers OBS31Capture ===")
        report.append(f"Répertoire analysé : {directory}")
        report.append(f"Fichiers avec références à OBSCapture : {len(results)}")
        report.append("")
        
        for analysis in results:
            if 'error' in analysis:
                report.append(f"ERREUR dans {analysis['file']} : {analysis['error']}")
                continue
            
            report.append(f"Fichier : {analysis['file']}")
            
            details = []
            if analysis['obs_capture_import']:
                details.append("- Import direct de OBSCapture")
            if analysis['obs_capture_aliases']:
                details.append(f"- Import avec alias : {', '.join(analysis['obs_capture_aliases'])}")
            if analysis['obs_events_import']:
                details.append("- Utilisation de obs_events")
            if analysis['obs_media_import']:
                details.append("- Utilisation de obs_media")
            if analysis['obs_sources_import']:
                details.append("- Utilisation de obs_sources")
            if analysis['instances'] > 0:
                details.append(f"- {analysis['instances']} instanciations de OBSCapture")
            
            for detail in details:
                report.append(detail)
            
            report.append("Suggestions :")
            suggestions = suggest_migration(analysis)
            for suggestion in suggestions:
                report.append(suggestion)
            
            report.append("")
        
        report.append("=== Fin du rapport ===")
        report_text = "\n".join(report)
        
        # Écrire dans un fichier ou afficher dans la console
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"Rapport écrit dans {output_file}")
        else:
            print(report_text)
        
        return report_text
    except Exception as e:
        error_message = f"Erreur lors de la génération du rapport : {e}"
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(error_message)
        print(error_message)
        return error_message

def apply_migration(file_path, backup=True):
    """Applique les modifications suggérées à un fichier
    
    Args:
        file_path (str): Chemin du fichier à modifier
        backup (bool, optional): Si True, crée une copie de sauvegarde avant modification. Par défaut True.
        
    Returns:
        bool: True si les modifications ont été appliquées avec succès
    """
    try:
        # Lire le contenu du fichier
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Créer une copie de sauvegarde
        if backup:
            backup_path = f"{file_path}.bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Sauvegarde créée : {backup_path}")
        
        # Remplacer les imports
        new_content = content
        
        # Import direct de OBSCapture
        new_content = re.sub(
            r'from\s+server\.capture\.obs_capture\s+import\s+OBSCapture',
            'from server.capture.obs_31_capture import OBS31Capture as OBSCapture  # Compatible OBS 31.0.2+',
            new_content
        )
        
        # Import avec alias
        new_content = re.sub(
            r'import\s+server\.capture\.obs_capture\s+as\s+(\w+)',
            r'import server.capture.obs_31_capture as \1  # Compatible OBS 31.0.2+',
            new_content
        )
        
        # Modules associés
        new_content = re.sub(
            r'from\s+server\.capture\.obs_events\s+import',
            'from server.capture.obs_events_31 import',
            new_content
        )
        
        new_content = re.sub(
            r'from\s+server\.capture\.obs_media\s+import',
            'from server.capture.obs_media_31 import',
            new_content
        )
        
        new_content = re.sub(
            r'from\s+server\.capture\.obs_sources\s+import',
            'from server.capture.obs_sources_31 import',
            new_content
        )
        
        # Instanciations
        new_content = re.sub(
            r'=\s*OBSCapture\(',
            '= OBS31Capture(',
            new_content
        )
        
        # Écrire le contenu modifié
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Modifications appliquées à {file_path}")
        return True
    
    except Exception as e:
        print(f"Erreur lors de l'application des migrations à {file_path} : {e}")
        return False

if __name__ == "__main__":
    # Configurer le logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_obs31.py <directory> [--apply] [--output=report.txt]")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    # Vérifier si l'option --apply est spécifiée
    apply_mode = "--apply" in sys.argv
    
    # Vérifier si l'option --output est spécifiée
    output_file = None
    for arg in sys.argv:
        if arg.startswith("--output="):
            output_file = arg.split("=", 1)[1]
    
    if apply_mode:
        print(f"Mode application des migrations pour le répertoire: {directory}")
        
        # Scanner le répertoire
        results = scan_directory(directory)
        
        # Appliquer les migrations
        for analysis in results:
            if 'error' not in analysis:
                apply_migration(analysis['file'])
    else:
        # Générer le rapport de migration
        generate_migration_report(directory, output_file)
