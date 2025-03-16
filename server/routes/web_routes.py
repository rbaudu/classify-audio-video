import time
import logging
from datetime import datetime
from flask import render_template
from server import ACTIVITY_ICONS, ACTIVITY_COLORS

logger = logging.getLogger(__name__)

def register_web_routes(app):
    """
    Enregistre les routes web dans l'application Flask
    """
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
        from server.routes.api_routes import analysis_tasks
        from server.database.db_manager import DBManager
        
        db_manager = DBManager()
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
