import time
import logging
import cv2
import numpy as np
from flask import Response

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
    while True:
        try:
            # Récupérer la frame actuelle depuis OBS
            if hasattr(sync_manager, 'obs_capture') and sync_manager.obs_capture:
                frame = sync_manager.obs_capture.get_current_frame()
                
                if frame is not None and frame.size > 0:
                    # Convertir en JPEG
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_bytes = buffer.tobytes()
                    
                    # Yield pour le stream MJPEG
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
                    # Limiter la fréquence d'images pour éviter une surcharge
                    time.sleep(0.1)  # ~10 FPS
                else:
                    # Si aucune frame n'est disponible, envoyer une image noire
                    dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                    _, buffer = cv2.imencode('.jpg', dummy_frame)
                    frame_bytes = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
                    # Attendre plus longtemps en cas d'erreur
                    time.sleep(0.5)
            else:
                # Si le gestionnaire de synchronisation n'est pas disponible, envoyer une image noire
                dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                _, buffer = cv2.imencode('.jpg', dummy_frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Attendre plus longtemps
                time.sleep(1.0)
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'image pour le flux vidéo: {str(e)}")
            
            # En cas d'erreur, envoyer une image noire
            dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', dummy_frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Attendre plus longtemps en cas d'erreur
            time.sleep(1.0)
