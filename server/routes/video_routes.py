import time
import logging
import cv2
import numpy as np
from flask import Response, render_template, jsonify

logger = logging.getLogger(__name__)

def register_video_routes(app, sync_manager):
    """
    Enregistre les routes de flux vidéo dans l'application Flask
    """
    
    @app.route('/api/video-feed')
    def video_feed():
        """
        Génère un flux MJPEG pour afficher la vidéo en direct
        """
        return Response(generate_video_frames(sync_manager),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @app.route('/api/video-snapshot')
    def video_snapshot():
        """
        Fournit une seule image de la vidéo actuelle
        """
        try:
            # Récupérer la frame actuelle depuis OBS
            if hasattr(sync_manager, 'obs_capture') and sync_manager.obs_capture:
                frame = sync_manager.obs_capture.get_current_frame()
                
                if frame is not None and frame.size > 0:
                    # Ajouter un texte avec l'horodatage
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # Convertir en JPEG
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    frame_bytes = buffer.tobytes()
                    
                    return Response(frame_bytes, mimetype='image/jpeg')
                else:
                    # Si aucune frame n'est disponible, envoyer une image noire avec un message
                    dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                    cv2.putText(dummy_frame, "Aucun flux vidéo disponible", (50, 180),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    _, buffer = cv2.imencode('.jpg', dummy_frame)
                    frame_bytes = buffer.tobytes()
                    
                    return Response(frame_bytes, mimetype='image/jpeg')
            else:
                # Si le gestionnaire de synchronisation n'est pas disponible, envoyer une image noire
                dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(dummy_frame, "Gestionnaire vidéo non disponible", (50, 180),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                _, buffer = cv2.imencode('.jpg', dummy_frame)
                frame_bytes = buffer.tobytes()
                
                return Response(frame_bytes, mimetype='image/jpeg')
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération de snapshot: {str(e)}")
            
            # En cas d'erreur, envoyer une image noire avec le message d'erreur
            dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(dummy_frame, f"Erreur: {str(e)}", (50, 180),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            _, buffer = cv2.imencode('.jpg', dummy_frame)
            frame_bytes = buffer.tobytes()
            
            return Response(frame_bytes, mimetype='image/jpeg')
    
    @app.route('/api/video-status')
    def video_status():
        """
        Renvoie l'état de la capture vidéo
        """
        try:
            if not hasattr(sync_manager, 'obs_capture') or not sync_manager.obs_capture:
                return jsonify({"status": "error", "message": "Gestionnaire de capture non disponible"})
            
            if not sync_manager.obs_capture.connected:
                return jsonify({"status": "error", "message": "Non connecté à OBS"})
            
            # Vérifier si la source vidéo existe
            sources = []
            for src in sync_manager.obs_capture.video_sources:
                sources.append(src['name'])
            
            if not sources:
                return jsonify({"status": "error", "message": "Aucune source vidéo trouvée", "sources": []})
            
            return jsonify({
                "status": "ok",
                "message": "Capture vidéo disponible",
                "sources": sources,
                "currentSource": sync_manager.obs_capture.current_source
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut vidéo: {str(e)}")
            return jsonify({"status": "error", "message": str(e)})
    
    @app.route('/api/audio-feed')
    def audio_feed():
        """
        Route de placeholder pour l'audio (pour compatibilité)
        """
        return Response("Audio stream not implemented", mimetype='text/plain')

def generate_video_frames(sync_manager):
    """
    Fonction génératrice pour le flux vidéo MJPEG
    """
    error_count = 0
    last_successful_frame = None

    while True:
        try:
            # Récupérer la frame actuelle depuis OBS
            if hasattr(sync_manager, 'obs_capture') and sync_manager.obs_capture:
                frame = sync_manager.obs_capture.get_current_frame()
                
                if frame is not None and frame.size > 0:
                    # Ajouter un texte avec l'horodatage
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # Convertir en JPEG
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_bytes = buffer.tobytes()
                    
                    # Mémoriser cette frame en cas d'erreur future
                    last_successful_frame = frame.copy()
                    error_count = 0  # Réinitialiser le compteur d'erreurs
                    
                    # Yield pour le stream MJPEG
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
                    # Limiter la fréquence d'images pour éviter une surcharge
                    time.sleep(0.1)  # ~10 FPS
                else:
                    error_count += 1
                    # Si on a une frame précédente, l'utiliser avant de revenir à une image noire
                    if last_successful_frame is not None and error_count < 10:
                        # Ajouter un texte indiquant qu'il s'agit d'un frame mémorisée
                        frame_copy = last_successful_frame.copy()
                        cv2.putText(frame_copy, "Dernière image capturée", (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        _, buffer = cv2.imencode('.jpg', frame_copy)
                        frame_bytes = buffer.tobytes()
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    else:
                        # Si aucune frame n'est disponible, envoyer une image noire avec un message
                        dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                        cv2.putText(dummy_frame, "Aucun flux vidéo disponible", (50, 180),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        _, buffer = cv2.imencode('.jpg', dummy_frame)
                        frame_bytes = buffer.tobytes()
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
                    # Attendre plus longtemps en cas d'erreur
                    time.sleep(0.5)
            else:
                # Si le gestionnaire de synchronisation n'est pas disponible, envoyer une image noire
                dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(dummy_frame, "Gestionnaire vidéo non disponible", (50, 180),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                _, buffer = cv2.imencode('.jpg', dummy_frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Attendre plus longtemps
                time.sleep(1.0)
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'image pour le flux vidéo: {str(e)}")
            
            # En cas d'erreur, envoyer une image noire avec le message d'erreur
            dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(dummy_frame, f"Erreur: {str(e)}", (50, 180),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            _, buffer = cv2.imencode('.jpg', dummy_frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Attendre plus longtemps en cas d'erreur
            time.sleep(1.0)
