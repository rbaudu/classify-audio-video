"""
Module de gestion des analyses vidéo
"""
import os
import time
import json
import logging
from server.utils.formatting import format_time

logger = logging.getLogger(__name__)

def analyze_video_task(analysis_id, source_name, sync_manager, activity_classifier, 
                      db_manager, analysis_dir, analysis_tasks, save_analysis=True, 
                      generate_timeline=False, sample_interval=5):
    """
    Tâche en arrière-plan pour analyser une vidéo complète
    
    Args:
        analysis_id (str): Identifiant unique de l'analyse
        source_name (str): Nom de la source vidéo
        sync_manager (SyncManager): Gestionnaire de synchronisation
        activity_classifier (ActivityClassifier): Classificateur d'activité
        db_manager (DBManager): Gestionnaire de base de données
        analysis_dir (str): Répertoire pour les analyses temporaires
        analysis_tasks (dict): Dictionnaire stockant toutes les tâches d'analyse
        save_analysis (bool): Indique s'il faut sauvegarder l'analyse en base de données
        generate_timeline (bool): Indique s'il faut générer une timeline
        sample_interval (int): Intervalle d'échantillonnage en secondes
    """
    try:
        logger.info(f"Démarrage de l'analyse vidéo {analysis_id} pour {source_name}")
        
        # Obtenir les propriétés de la vidéo
        obs_capture = sync_manager.obs_capture
        properties = obs_capture.get_media_properties(source_name)
        if not properties or not properties.get('duration'):
            raise ValueError(f"Impossible de récupérer les propriétés de la vidéo {source_name}")
        
        duration = properties.get('duration', 0)
        
        # Redémarrer la vidéo
        obs_capture.control_media(source_name, 'restart')
        time.sleep(1)  # Attendre le redémarrage
        
        # Boucle d'analyse
        results = []
        for current_time in range(0, int(duration), sample_interval):
            # Mettre à jour la progression
            progress = (current_time / duration) * 100
            analysis_tasks[analysis_id]['progress'] = progress
            
            # Positionner la vidéo
            obs_capture.control_media(source_name, 'seek', current_time)
            time.sleep(0.5)  # Attendre que l'image se stabilise
            
            # Récupérer des données synchronisées
            data = sync_manager.get_synchronized_data()
            
            if not data:
                logger.warning(f"Impossible de récupérer des données à {current_time}s")
                continue
                
            # Classifier l'activité
            classification = activity_classifier.classify_activity(
                data['video']['processed'],
                data['audio']['processed']
            )
            
            # Ajouter le temps à la classification
            result = {
                'activity': classification['activity'],
                'confidence': classification['confidence'],
                'confidence_scores': classification['confidence_scores'],
                'timestamp': current_time,
                'formatted_time': format_time(current_time),
                'features': {
                    'video': data['video']['processed'].get('features', {}),
                    'audio': data['audio']['processed'].get('features', {})
                }
            }
            
            results.append(result)
            
            # Mettre à jour les résultats
            analysis_tasks[analysis_id]['results'] = results
        
        # Arrêter la vidéo à la fin
        obs_capture.control_media(source_name, 'pause')
        
        # Enregistrer les résultats
        if save_analysis:
            # Sauvegarder dans la base de données
            db_manager.save_video_analysis(analysis_id, source_name, results)
        
        # Générer une timeline si demandé
        if generate_timeline:
            generate_timeline_visualization(analysis_id, results, analysis_dir)
        
        # Marquer comme terminé
        analysis_tasks[analysis_id]['status'] = 'completed'
        analysis_tasks[analysis_id]['end_time'] = time.time()
        analysis_tasks[analysis_id]['total_samples'] = len(results)
        
        logger.info(f"Analyse vidéo {analysis_id} terminée avec {len(results)} échantillons")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse vidéo {analysis_id}: {str(e)}")
        analysis_tasks[analysis_id]['status'] = 'error'
        analysis_tasks[analysis_id]['error'] = str(e)


def generate_timeline_visualization(analysis_id, results, analysis_dir):
    """
    Génère une visualisation de la timeline
    
    Args:
        analysis_id (str): Identifiant unique de l'analyse
        results (list): Résultats de l'analyse
        analysis_dir (str): Répertoire pour les analyses temporaires
    """
    # Implémentation simplifiée, à adapter selon vos besoins
    timeline_data = {
        'analysis_id': analysis_id,
        'timestamps': [r['timestamp'] for r in results],
        'activities': [r['activity'] for r in results],
        'formatted_times': [r['formatted_time'] for r in results],
        'confidences': [r['confidence'] for r in results]
    }
    
    # Sauvegarder les données pour utilisation ultérieure
    timeline_path = os.path.join(analysis_dir, f"{analysis_id}_timeline.json")
    with open(timeline_path, 'w') as f:
        json.dump(timeline_data, f)
        
    logger.info(f"Timeline visualisation générée pour l'analyse {analysis_id}")
