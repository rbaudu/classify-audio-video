import time
import logging
import threading
import json
from server import ANALYSIS_INTERVAL

logger = logging.getLogger(__name__)

# Variable globale pour contrôler la boucle d'analyse
analysis_running = False
analysis_thread = None

# Événement pour l'arrêt propre
stop_event = threading.Event()

def analysis_loop(activity_classifier, db_manager, external_service):
    """
    Fonction exécutée dans un thread pour analyser périodiquement l'activité
    """
    global analysis_running
    logger.info("Démarrage de la boucle d'analyse périodique")
    
    while analysis_running and not stop_event.is_set():
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
        
        # Attendre jusqu'à la prochaine analyse avec support d'interruption
        # Utiliser un court sleep pour permettre des interruptions plus rapides
        for _ in range(int(ANALYSIS_INTERVAL * 10)):
            if not analysis_running or stop_event.is_set():
                break
            time.sleep(0.1)  # Dormir par petits intervalles pour être réactif

def start_analysis_loop(activity_classifier, db_manager, external_service):
    """
    Démarre la boucle d'analyse dans un thread séparé
    """
    global analysis_running, analysis_thread
    
    if analysis_thread and analysis_thread.is_alive():
        logger.warning("La boucle d'analyse est déjà en cours d'exécution")
        return False
    
    analysis_running = True
    # Réinitialiser l'événement d'arrêt
    stop_event.clear()
    
    analysis_thread = threading.Thread(
        target=analysis_loop,
        args=(activity_classifier, db_manager, external_service)
    )
    analysis_thread.daemon = True
    analysis_thread.start()
    
    logger.info("Boucle d'analyse démarrée")
    return True

def stop_analysis_loop(timeout=2.0):
    """
    Arrête la boucle d'analyse
    
    Args:
        timeout (float): Temps maximum d'attente en secondes
    
    Returns:
        bool: True si arrêté avec succès, False sinon
    """
    global analysis_running, analysis_thread
    
    if not analysis_thread or not analysis_thread.is_alive():
        logger.warning("La boucle d'analyse n'est pas en cours d'exécution")
        return False
    
    logger.info("Arrêt de la boucle d'analyse...")
    analysis_running = False
    
    # Signaler à tous les threads de s'arrêter
    stop_event.set()
    
    # Attendre la fin du thread (avec timeout)
    analysis_thread.join(timeout=timeout)
    
    if analysis_thread.is_alive():
        logger.warning(f"Le thread d'analyse ne s'est pas terminé dans le délai imparti ({timeout}s)")
        return False
    
    logger.info("Boucle d'analyse arrêtée avec succès")
    return True
