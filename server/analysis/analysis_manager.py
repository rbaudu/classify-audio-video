import time
import logging
import threading
import json
from server import ANALYSIS_INTERVAL

logger = logging.getLogger(__name__)

# Variable globale pour contrôler la boucle d'analyse
analysis_running = False
analysis_thread = None

def analysis_loop(activity_classifier, db_manager, external_service):
    """
    Fonction exécutée dans un thread pour analyser périodiquement l'activité
    """
    global analysis_running
    logger.info("Démarrage de la boucle d'analyse périodique")
    
    while analysis_running:
        try:
            # Capturer et analyser
            result = activity_classifier.analyze_current_activity()
            
            if result:
                # Enregistrer en base de données
                activity_id = db_manager.add_activity(
                    result['activity'],
                    result['confidence'],
                    result['timestamp'],
                    json.dumps(result['features'])
                )
                
                # Envoyer au service externe
                external_service.send_activity(result)
                
                logger.info(f"Activité {result['activity']} détectée et enregistrée (ID: {activity_id})")
            
        except Exception as e:
            logger.error(f"Erreur dans la boucle d'analyse: {str(e)}")
        
        # Attendre jusqu'à la prochaine analyse
        time.sleep(ANALYSIS_INTERVAL)

def start_analysis_loop(activity_classifier, db_manager, external_service):
    """
    Démarre la boucle d'analyse dans un thread séparé
    """
    global analysis_running, analysis_thread
    
    if analysis_thread and analysis_thread.is_alive():
        logger.warning("La boucle d'analyse est déjà en cours d'exécution")
        return False
    
    analysis_running = True
    analysis_thread = threading.Thread(
        target=analysis_loop,
        args=(activity_classifier, db_manager, external_service)
    )
    analysis_thread.daemon = True
    analysis_thread.start()
    
    logger.info("Boucle d'analyse démarrée")
    return True

def stop_analysis_loop():
    """
    Arrête la boucle d'analyse
    """
    global analysis_running, analysis_thread
    
    if not analysis_thread or not analysis_thread.is_alive():
        logger.warning("La boucle d'analyse n'est pas en cours d'exécution")
        return False
    
    logger.info("Arrêt de la boucle d'analyse...")
    analysis_running = False
    
    # Attendre la fin du thread (avec timeout)
    analysis_thread.join(timeout=2.0)
    
    if analysis_thread.is_alive():
        logger.warning("Le thread d'analyse ne s'est pas terminé proprement")
        return False
    
    logger.info("Boucle d'analyse arrêtée avec succès")
    return True
