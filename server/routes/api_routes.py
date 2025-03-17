import time
import json
import logging
import os
import io
import csv
import uuid
import threading
from flask import request, jsonify, Response
from server.utils.formatting import format_time

logger = logging.getLogger(__name__)

# Stocker les tâches d'analyse en cours (variable globale)
analysis_tasks = {}

def register_api_routes(app, sync_manager, activity_classifier, db_manager, analysis_dir):
    """
    Enregistre les routes API dans l'application Flask
    """
    
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
                    # Créer une activité par défaut plutôt que de retourner une erreur
                    default_activity = {
                        'activity': 'inactif',
                        'confidence': 0.5,
                        'timestamp': int(time.time()),
                        'features': {
                            'video': {
                                'motion_percent': 0.0,
                                'skin_percent': 0.0,
                                'hsv_means': (0.0, 0.0, 0.0)
                            },
                            'audio': {
                                'rms_level': 0.0,
                                'zero_crossing_rate': 0.0,
                                'dominant_frequency': 0.0,
                                'mid_freq_ratio': 0.0
                            }
                        }
                    }
                    return jsonify(default_activity)
                
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
            # Retourner une activité par défaut en cas d'erreur plutôt qu'une erreur 500
            default_activity = {
                'activity': 'inactif',
                'confidence': 0.5,
                'timestamp': int(time.time()),
                'features': {},
                'error': str(e)
            }
            return jsonify(default_activity)

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
            return jsonify({
                "error": str(e),
                "activities": []
            }), 500

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
            return jsonify({
                "error": str(e),
                "activity_counts": {},
                "activity_durations": {},
                "period": "day"
            }), 500

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
                # Renvoyer une classification par défaut plutôt qu'une erreur
                default_result = {
                    'activity': 'inactif',
                    'confidence': 0.5,
                    'timestamp': int(time.time()),
                    'features': {}
                }
                return jsonify(default_result)
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Erreur lors de la classification: {str(e)}")
            return jsonify({
                'activity': 'inactif',
                'confidence': 0.5,
                'timestamp': int(time.time()),
                'features': {},
                'error': str(e)
            })

    # Routes API pour les flux vidéo/audio
    @app.route('/api/video-feed-url', methods=['GET'])
    def get_video_feed_url():
        """Récupère l'URL du flux vidéo (simulation)"""
        return jsonify({"url": "/api/video-feed"})

    @app.route('/api/audio-feed-url', methods=['GET'])
    def get_audio_feed_url():
        """Récupère l'URL du flux audio (simulation)"""
        return jsonify({"url": "/api/audio-feed"})

    # Routes API pour les sources média
    @app.route('/api/media-sources', methods=['GET'])
    def get_media_sources():
        """Récupère la liste des sources média disponibles"""
        try:
            sources = sync_manager.obs_capture.get_media_sources()
            return jsonify(sources)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sources média: {str(e)}")
            return jsonify({"error": str(e), "sources": []}), 500

    @app.route('/api/audio-devices', methods=['GET'])
    def get_audio_devices():
        """Récupère la liste des périphériques audio disponibles"""
        try:
            devices = sync_manager.get_audio_devices()
            return jsonify(devices)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des périphériques audio: {str(e)}")
            return jsonify({"error": str(e), "devices": []}), 500

    @app.route('/api/set-audio-device', methods=['POST'])
    def set_audio_device():
        """Change le périphérique audio de capture"""
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
        """Sélectionne une source média"""
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
        """Récupère les propriétés d'une source média"""
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
        """Contrôle la lecture d'une source média"""
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
        """Récupère le temps actuel d'une source média"""
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
        """Sauvegarde un clip synchronisé audio/vidéo"""
        try:
            data = request.json
            duration = data.get('duration', 5)
            prefix = data.get('prefix', 'clip')
            
            result = sync_manager.save_synchronized_clip(duration, prefix)
            
            if not result or not result.get('success'):
                return jsonify({"error": "Impossible de sauvegarder le clip", "partial_result": result}), 400
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du clip: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/analyze-full-video', methods=['POST'])
    def analyze_full_video():
        """Lance l'analyse complète d'une vidéo"""
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
            
            # Initialiser l'entrée dans analysis_tasks
            analysis_tasks[analysis_id] = {
                'status': 'running',
                'progress': 0,
                'source_name': source_name,
                'start_time': time.time(),
                'results': []
            }
            
            # Lancer l'analyse en arrière-plan
            thread = threading.Thread(
                target=analyze_video,
                args=(analysis_id, source_name, sync_manager, activity_classifier, 
                      db_manager, analysis_dir, analysis_tasks, save_analysis, 
                      generate_timeline, sample_interval)
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
        """Récupère l'état d'une analyse en cours"""
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
        """Exporte les résultats d'une analyse dans différents formats"""
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
                response = Response(
                    json.dumps(analysis, indent=2),
                    status=200,
                    mimetype='application/json'
                )
                response.headers["Content-Disposition"] = f"attachment; filename={analysis_id}.json"
                return response
                
            elif format == 'csv':
                # Créer un buffer pour écrire le CSV en mémoire
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Écrire l'en-tête avec des colonnes détaillées
                header = [
                    'timestamp',
                    'formatted_time',
                    'activity',
                    'confidence'
                ]
                
                # Ajouter des colonnes pour les scores de confiance de chaque activité
                confidence_keys = set()
                for result in analysis.get('results', []):
                    if result.get('confidence_scores'):
                        confidence_keys.update(result['confidence_scores'].keys())
                
                # Ajouter des colonnes pour chaque type d'activité
                for key in sorted(confidence_keys):
                    header.append(f'score_{key}')
                
                # Ajouter des colonnes pour les caractéristiques principales
                feature_columns = [
                    'audio_volume',
                    'audio_frequency',
                    'movement_intensity',
                    'scene_brightness',
                    'pose_confidence'
                ]
                
                for feature in feature_columns:
                    header.append(feature)
                
                # Écrire l'en-tête
                writer.writerow(header)
                
                # Écrire les données
                for result in analysis.get('results', []):
                    row = [
                        result.get('timestamp', ''),
                        result.get('formatted_time', ''),
                        result.get('activity', ''),
                        result.get('confidence', '')
                    ]
                    
                    # Ajouter les scores de confiance
                    for key in sorted(confidence_keys):
                        row.append(result.get('confidence_scores', {}).get(key, ''))
                    
                    # Ajouter les caractéristiques audio/vidéo
                    video_features = result.get('features', {}).get('video', {})
                    audio_features = result.get('features', {}).get('audio', {})
                    
                    # Extraire les valeurs des caractéristiques principales
                    row.append(audio_features.get('volume', ''))
                    row.append(audio_features.get('frequency', ''))
                    row.append(video_features.get('movement', ''))
                    row.append(video_features.get('brightness', ''))
                    row.append(video_features.get('pose_confidence', ''))
                    
                    # Écrire la ligne
                    writer.writerow(row)
                
                # Retourner le CSV
                output.seek(0)
                
                response = Response(
                    output.getvalue(),
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

def analyze_video(analysis_id, source_name, sync_manager, activity_classifier, 
                 db_manager, analysis_dir, analysis_tasks, save_analysis=True, 
                 generate_timeline=False, sample_interval=5):
    """
    Fonction pour analyser une vidéo complète
    (Exécutée dans un thread séparé)
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
