import os
import time
import uuid
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
import threading

# Import des modules du projet
from server.capture import SyncManager
from server.capture.stream_processor import StreamProcessor
from server.analysis.activity_classifier import ActivityClassifier
from server.database.db_manager import DBManager
from server.api.external_service import ExternalServiceClient
from server import (
    WEB_PORT,
    ANALYSIS_INTERVAL,
    ACTIVITY_ICONS,
    ACTIVITY_COLORS
)

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("activity_classifier.log")
    ]
)
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__, 
           static_folder='../web/static',
           template_folder='../web/templates')

# Initialisation des classes principales
sync_manager = SyncManager()  # Nouveau gestionnaire de synchronisation audio/vidéo
stream_processor = StreamProcessor()
db_manager = DBManager()
activity_classifier = ActivityClassifier(sync_manager, stream_processor, db_manager)
external_service = ExternalServiceClient()

# Thread pour l'analyse périodique
analysis_thread = None
analysis_running = False

# Répertoire pour les analyses temporaires
ANALYSIS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'analyses')
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# Stocker les tâches d'analyse en cours
analysis_tasks = {}

def analysis_loop():
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

def analyze_video_task(analysis_id, source_name, save_analysis=True, generate_timeline=False, sample_interval=5):
    """
    Tâche en arrière-plan pour analyser une vidéo complète
    """
    try:
        logger.info(f"Démarrage de l'analyse vidéo {analysis_id} pour {source_name}")
        
        # Marquer l'analyse comme en cours
        analysis_tasks[analysis_id] = {
            'status': 'running',
            'progress': 0,
            'source_name': source_name,
            'start_time': time.time(),
            'results': []
        }
        
        # Obtenir les propriétés de la vidéo
        obs_capture = sync_manager.obs_capture  # Accès à l'objet OBSCapture via le SyncManager
        properties = obs_capture.get_media_properties(source_name)
        if not properties or not properties.get('duration'):
            raise ValueError(f"Impossible de récupérer les propriétés de la vidéo {source_name}")
        
        duration = properties.get('duration', 0)
        total_samples = int(duration / sample_interval)
        
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
                
            # Classifier l'activité en utilisant les données traitées
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
            generate_timeline_visualization(analysis_id, results)
        
        # Marquer comme terminé
        analysis_tasks[analysis_id]['status'] = 'completed'
        analysis_tasks[analysis_id]['end_time'] = time.time()
        analysis_tasks[analysis_id]['total_samples'] = len(results)
        
        logger.info(f"Analyse vidéo {analysis_id} terminée avec {len(results)} échantillons")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse vidéo {analysis_id}: {str(e)}")
        analysis_tasks[analysis_id]['status'] = 'error'
        analysis_tasks[analysis_id]['error'] = str(e)

def format_time(seconds):
    """
    Formate un temps en secondes en format lisible
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def generate_timeline_visualization(analysis_id, results):
    """
    Génère une visualisation de la timeline
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
    timeline_path = os.path.join(ANALYSIS_DIR, f"{analysis_id}_timeline.json")
    with open(timeline_path, 'w') as f:
        json.dump(timeline_data, f)

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Page de tableau de bord"""
    return render_template('dashboard.html')

@app.route('/statistics')
def statistics():
    """Page de statistiques"""
    return render_template('statistics.html')

@app.route('/history')
def history():
    """Page d'historique des activités"""
    return render_template('history.html')

@app.route('/model_testing')
def model_testing():
    """Page de test du modèle"""
    return render_template('model_testing.html')

@app.route('/analysis-results/<analysis_id>')
def analysis_results(analysis_id):
    """Page de résultats d'analyse vidéo"""
    analysis_data = db_manager.get_video_analysis(analysis_id)
    
    if not analysis_data:
        # Vérifier si l'analyse est toujours en cours
        if analysis_id in analysis_tasks and analysis_tasks[analysis_id]['status'] == 'running':
            return render_template('analysis_in_progress.html', 
                                   analysis_id=analysis_id,
                                   progress=analysis_tasks[analysis_id]['progress'])
        return render_template('error.html', message="Analyse non trouvée"), 404
    
    # Préparer les données pour le template
    source_name = analysis_data.get('source_name', 'Vidéo inconnue')
    results = analysis_data.get('results', [])
    timestamp = analysis_data.get('timestamp', time.time())
    
    # Calculer les statistiques récapitulatives
    activity_counts = {}
    for result in results:
        activity = result['activity']
        if activity not in activity_counts:
            activity_counts[activity] = 0
        activity_counts[activity] += 1
    
    # Trouver l'activité principale
    main_activity = max(activity_counts.items(), key=lambda x: x[1])[0] if activity_counts else None
    main_activity_percentage = int((activity_counts.get(main_activity, 0) / len(results)) * 100) if results else 0
    
    # Calculer la durée
    if results:
        max_timestamp = max(r['timestamp'] for r in results)
        formatted_duration = format_time(max_timestamp)
    else:
        formatted_duration = "00:00:00"
    
    # Formater la date d'analyse
    analysis_date = datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
    
    return render_template('analysis_results.html',
                          analysis_id=analysis_id,
                          source_name=source_name,
                          results=results,
                          activity_icons=ACTIVITY_ICONS,
                          activity_colors=ACTIVITY_COLORS,
                          main_activity=main_activity,
                          main_activity_percentage=main_activity_percentage,
                          total_samples=len(results),
                          formatted_duration=formatted_duration,
                          analysis_date=analysis_date)

# Routes API pour la récupération des données
@app.route('/api/current-activity', methods=['GET', 'HEAD'])
def get_current_activity():
    """
    Récupère l'activité actuelle
    - GET: Retourne les détails de l'activité
    - HEAD: Utilisé pour vérifier la connexion
    """
    if request.method == 'HEAD':
        return '', 200
    
    try:
        # Récupérer la dernière activité de la base de données
        activity = db_manager.get_latest_activity()
        
        if not activity:
            # Si aucune activité n'est trouvée, analyser en direct
            result = activity_classifier.analyze_current_activity()
            
            if not result:
                return jsonify({"error": "Aucune activité détectée"}), 404
            
            # Formater pour l'API
            activity_data = {
                'activity': result['activity'],
                'confidence': result['confidence'],
                'timestamp': result['timestamp'],
                'features': result['features']
            }
        else:
            # Formater pour l'API
            activity_data = {
                'activity': activity['activity'],
                'confidence': activity['confidence'],
                'timestamp': activity['timestamp'],
                'features': json.loads(activity['metadata']) if activity['metadata'] else {}
            }
        
        return jsonify(activity_data)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'activité: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/activities', methods=['GET'])
def get_activities():
    """
    Récupère l'historique des activités avec filtrage
    """
    try:
        # Récupérer les paramètres de requête
        start = request.args.get('start')
        end = request.args.get('end')
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Convertir les timestamps
        if start:
            start = int(start)
        if end:
            end = int(end)
        
        # Récupérer les activités
        activities = db_manager.get_activities(start, end, limit, offset)
        
        # Formater pour l'API
        result = []
        for activity in activities:
            result.append({
                'activity': activity['activity'],
                'confidence': activity['confidence'],
                'timestamp': activity['timestamp'],
                'metadata': json.loads(activity['metadata']) if activity['metadata'] else {}
            })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des activités: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Récupère les statistiques d'activité pour une période donnée
    """
    try:
        # Récupérer les paramètres de requête
        period = request.args.get('period', default='day')
        
        # Calculer les timestamps pour la période
        now = int(time.time())
        
        if period == 'day':
            start = now - (24 * 60 * 60)  # 24 heures
        elif period == 'week':
            start = now - (7 * 24 * 60 * 60)  # 7 jours
        elif period == 'month':
            start = now - (30 * 24 * 60 * 60)  # 30 jours
        elif period == 'year':
            start = now - (365 * 24 * 60 * 60)  # 365 jours
        else:
            start = now - (24 * 60 * 60)  # Par défaut: 24 heures
        
        # Récupérer les activités pour la période
        activities = db_manager.get_activities(start, now, 10000, 0)
        
        # Calculer les statistiques
        activity_counts = {}
        activity_durations = {}
        
        for i, activity in enumerate(activities):
            # Compter les occurrences
            act_type = activity['activity']
            if act_type not in activity_counts:
                activity_counts[act_type] = 0
            activity_counts[act_type] += 1
            
            # Calculer les durées
            if i < len(activities) - 1:
                duration = activities[i+1]['timestamp'] - activity['timestamp']
                
                if act_type not in activity_durations:
                    activity_durations[act_type] = 0
                activity_durations[act_type] += duration
        
        # Générer des données horaires (exemple simplifié)
        hourly_distribution = []
        for hour in range(24):
            hour_activities = {}
            for act_type in activity_counts.keys():
                hour_activities[act_type] = 0
            
            hourly_distribution.append({
                'hour': hour,
                'activities': hour_activities
            })
        
        # Simuler des tendances pour cet exemple
        trends = []
        for i in range(10):
            trend_activities = {}
            for act_type in activity_counts.keys():
                trend_activities[act_type] = 0
            
            trends.append({
                'date': f"Point {i+1}",
                'activities': trend_activities
            })
        
        # Formater pour l'API
        stats = {
            'activity_counts': activity_counts,
            'activity_durations': activity_durations,
            'hourly_distribution': hourly_distribution,
            'trends': trends,
            'total_classifications': len(activities),
            'period': period
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/classify', methods=['POST'])
def classify():
    """
    Effectue une classification à partir des caractéristiques fournies ou de l'état actuel
    """
    try:
        features = request.json
        
        if features:
            # Utiliser les caractéristiques fournies
            result = activity_classifier.classify_activity(
                features.get('video', {}),
                features.get('audio', {})
            )
        else:
            # Capturer et analyser l'état actuel
            result = activity_classifier.analyze_current_activity()
        
        if not result:
            return jsonify({"error": "Impossible de classifier l'activité"}), 400
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur lors de la classification: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Routes API pour les flux vidéo/audio
@app.route('/api/video-feed-url', methods=['GET'])
def get_video_feed_url():
    """
    Récupère l'URL du flux vidéo (simulation)
    """
    # Note: Dans une implémentation réelle, vous pourriez fournir une URL de streaming
    return jsonify({"url": "/api/video-feed"})

@app.route('/api/audio-feed-url', methods=['GET'])
def get_audio_feed_url():
    """
    Récupère l'URL du flux audio (simulation)
    """
    # Note: Dans une implémentation réelle, vous pourriez fournir une URL de streaming
    return jsonify({"url": "/api/audio-feed"})

# Routes API pour les sources média
@app.route('/api/media-sources', methods=['GET'])
def get_media_sources():
    """
    Récupère la liste des sources média disponibles
    """
    try:
        sources = sync_manager.obs_capture.get_media_sources()
        return jsonify(sources)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des sources média: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/audio-devices', methods=['GET'])
def get_audio_devices():
    """
    Récupère la liste des périphériques audio disponibles
    """
    try:
        devices = sync_manager.get_audio_devices()
        return jsonify(devices)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des périphériques audio: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/set-audio-device', methods=['POST'])
def set_audio_device():
    """
    Change le périphérique audio de capture
    """
    try:
        data = request.json
        device_index = data.get('deviceIndex')
        
        if device_index is None:
            return jsonify({"error": "Indice de périphérique requis"}), 400
        
        success = sync_manager.set_audio_device(int(device_index))
        
        if not success:
            return jsonify({"error": "Impossible de changer de périphérique audio"}), 400
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Erreur lors du changement de périphérique audio: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/select-media-source', methods=['POST'])
def select_media_source():
    """
    Sélectionne une source média
    """
    try:
        data = request.json
        source_name = data.get('sourceName')
        
        if not source_name:
            return jsonify({"error": "Nom de source requis"}), 400
        
        success = sync_manager.obs_capture.select_media_source(source_name)
        
        if not success:
            return jsonify({"error": "Impossible de sélectionner la source"}), 400
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Erreur lors de la sélection de la source: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/media-properties/<source_name>', methods=['GET'])
def get_media_properties(source_name):
    """
    Récupère les propriétés d'une source média
    """
    try:
        properties = sync_manager.obs_capture.get_media_properties(source_name)
        
        if not properties:
            return jsonify({"error": "Impossible de récupérer les propriétés"}), 400
        
        return jsonify(properties)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des propriétés: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/control-media', methods=['POST'])
def control_media():
    """
    Contrôle la lecture d'une source média
    """
    try:
        data = request.json
        source_name = data.get('sourceName')
        action = data.get('action')
        position = data.get('position')
        
        if not source_name or not action:
            return jsonify({"error": "Nom de source et action requis"}), 400
        
        success = sync_manager.obs_capture.control_media(source_name, action, position)
        
        if not success:
            return jsonify({"error": f"Impossible d'effectuer l'action {action}"}), 400
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Erreur lors du contrôle du média: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/media-time/<source_name>', methods=['GET'])
def get_media_time(source_name):
    """
    Récupère le temps actuel d'une source média
    """
    try:
        time_info = sync_manager.obs_capture.get_media_time(source_name)
        
        if not time_info:
            return jsonify({"error": "Impossible de récupérer le temps"}), 400
        
        return jsonify(time_info)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du temps: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/save-clip', methods=['POST'])
def save_clip():
    """
    Sauvegarde un clip synchronisé audio/vidéo
    """
    try:
        data = request.json
        duration = data.get('duration', 5)
        prefix = data.get('prefix', 'clip')
        
        result = sync_manager.save_synchronized_clip(duration, prefix)
        
        if not result or not result.get('success'):
            return jsonify({"error": "Impossible de sauvegarder le clip"}), 400
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du clip: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-full-video', methods=['POST'])
def analyze_full_video():
    """
    Lance l'analyse complète d'une vidéo
    """
    try:
        data = request.json
        source_name = data.get('sourceName')
        save_analysis = data.get('saveAnalysis', True)
        generate_timeline = data.get('generateTimeline', False)
        sample_interval = data.get('sampleInterval', 5)
        
        if not source_name:
            return jsonify({"error": "Nom de source requis"}), 400
        
        # Générer un ID d'analyse unique
        analysis_id = f"analysis_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Lancer l'analyse en arrière-plan
        thread = threading.Thread(
            target=analyze_video_task,
            args=(analysis_id, source_name, save_analysis, generate_timeline, sample_interval)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "analysisId": analysis_id,
            "status": "started",
            "sourceName": source_name
        })
    except Exception as e:
        logger.error(f"Erreur lors du lancement de l'analyse: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis-status/<analysis_id>', methods=['GET'])
def get_analysis_status(analysis_id):
    """
    Récupère l'état d'une analyse en cours
    """
    try:
        if analysis_id not in analysis_tasks:
            # Vérifier si l'analyse existe dans la base de données
            analysis = db_manager.get_video_analysis(analysis_id)
            
            if not analysis:
                return jsonify({"error": "Analyse non trouvée"}), 404
            
            return jsonify({
                "analysisId": analysis_id,
                "status": "completed",
                "sourceName": analysis.get('source_name', 'Unknown'),
                "timestamp": analysis.get('timestamp'),
                "totalSamples": len(analysis.get('results', []))
            })
        
        # Récupérer l'état de l'analyse en cours
        task = analysis_tasks[analysis_id]
        
        return jsonify({
            "analysisId": analysis_id,
            "status": task.get('status'),
            "progress": task.get('progress'),
            "sourceName": task.get('source_name'),
            "startTime": task.get('start_time'),
            "error": task.get('error')
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'état de l'analyse: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/export-analysis/<analysis_id>/<format>', methods=['GET'])
def export_analysis(analysis_id, format):
    """
    Exporte les résultats d'une analyse
    """
    try:
        # Récupérer l'analyse
        analysis = None
        
        if analysis_id in analysis_tasks and analysis_tasks[analysis_id]['status'] == 'completed':
            analysis = {
                'source_name': analysis_tasks[analysis_id]['source_name'],
                'timestamp': analysis_tasks[analysis_id]['start_time'],
                'results': analysis_tasks[analysis_id]['results']
            }
        else:
            analysis = db_manager.get_video_analysis(analysis_id)
        
        if not analysis:
            return jsonify({"error": "Analyse non trouvée"}), 404
        
        if format == 'json':
            # Exporter en JSON
            response = app.response_class(
                response=json.dumps(analysis, indent=2),
                status=200,
                mimetype='application/json'
            )
            response.headers["Content-Disposition"] = f"attachment; filename={analysis_id}.json"
            return response
            
        elif format == 'csv':
            # Exporter en CSV
            csv_content = "timestamp,formatted_time,activity,confidence\n"
            
            for result in analysis.get('results', []):
                csv_content += f"{result.get('timestamp', '')},{result.get('formatted_time', '')},{result.get('activity', '')},{result.get('confidence', '')}\n"
            
            response = app.response_class(
                response=csv_content,
                status=200,
                mimetype='text/csv'
            )
            response.headers["Content-Disposition"] = f"attachment; filename={analysis_id}.csv"
            return response
            
        else:
            return jsonify({"error": f"Format d'export non supporté: {format}"}), 400
            
    except Exception as e:
        logger.error(f"Erreur lors de l'export de l'analyse: {str(e)}")
        return jsonify({"error": str(e)}), 500

def start_server():
    """
    Démarre le serveur Flask et la boucle d'analyse
    """
    global analysis_thread, analysis_running
    
    # Démarrer la capture synchronisée
    if not sync_manager.start():
        logger.error("Impossible de démarrer la capture synchronisée")
    else:
        logger.info("Capture synchronisée démarrée avec succès")
    
    # Démarrer la boucle d'analyse dans un thread
    analysis_running = True
    analysis_thread = threading.Thread(target=analysis_loop)
    analysis_thread.daemon = True
    analysis_thread.start()
    
    # Démarrer le serveur Flask
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False)

if __name__ == "__main__":
    start_server()
