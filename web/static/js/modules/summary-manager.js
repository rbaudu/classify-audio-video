/**
 * Module de gestion des résumés statistiques
 * Met à jour l'affichage du résumé statistique à partir des données
 */

const SummaryManager = {
    /**
     * Met à jour le résumé des statistiques dans l'interface
     * @param {Object} data - Données de statistiques
     */
    updateSummary: function(data) {
        if (!data) return;
        
        // Activité principale (celle avec la plus longue durée)
        this.updateMainActivity(data);
        
        // Activité la plus fréquente (celle avec le plus d'occurrences)
        this.updateMostFrequentActivity(data);
        
        // Temps actif et total
        this.updateTimeStats(data);
    },
    
    /**
     * Met à jour l'affichage de l'activité principale
     * @param {Object} data - Données de statistiques
     */
    updateMainActivity: function(data) {
        const mainActivity = document.getElementById('main-activity');
        const mainActivityPercent = document.getElementById('main-activity-percent');
        
        if (!mainActivity || !mainActivityPercent || !data.activity_durations) return;
        
        const activities = Object.entries(data.activity_durations);
        if (activities.length > 0) {
            const sorted = activities.sort((a, b) => b[1] - a[1]);
            const [activity, duration] = sorted[0];
            const totalDuration = activities.reduce((sum, [, d]) => sum + d, 0);
            const percent = totalDuration > 0 ? Math.round((duration / totalDuration) * 100) : 0;
            
            mainActivity.textContent = this.getActivityWithIcon(activity);
            mainActivityPercent.textContent = percent;
        } else {
            mainActivity.textContent = '-';
            mainActivityPercent.textContent = '0';
        }
    },
    
    /**
     * Met à jour l'affichage de l'activité la plus fréquente
     * @param {Object} data - Données de statistiques
     */
    updateMostFrequentActivity: function(data) {
        const mostFrequentActivity = document.getElementById('most-frequent-activity');
        const mostFrequentActivityCount = document.getElementById('most-frequent-activity-count');
        
        if (!mostFrequentActivity || !mostFrequentActivityCount || !data.activity_counts) return;
        
        const activities = Object.entries(data.activity_counts);
        if (activities.length > 0) {
            const sorted = activities.sort((a, b) => b[1] - a[1]);
            const [activity, count] = sorted[0];
            
            mostFrequentActivity.textContent = this.getActivityWithIcon(activity);
            mostFrequentActivityCount.textContent = count;
        } else {
            mostFrequentActivity.textContent = '-';
            mostFrequentActivityCount.textContent = '0';
        }
    },
    
    /**
     * Met à jour l'affichage des statistiques de temps
     * @param {Object} data - Données de statistiques
     */
    updateTimeStats: function(data) {
        const activeTime = document.getElementById('active-time');
        const activeTimePercent = document.getElementById('active-time-percent');
        const totalTime = document.getElementById('total-time');
        const totalClassifications = document.getElementById('total-classifications');
        
        if (!activeTime || !activeTimePercent || !totalTime || !totalClassifications || !data.activity_durations) return;
        
        let totalActiveSeconds = 0;
        let totalInactiveSeconds = 0;
        
        for (const [activity, duration] of Object.entries(data.activity_durations)) {
            if (activity === 'inactif' || activity === 'endormi') {
                totalInactiveSeconds += duration;
            } else {
                totalActiveSeconds += duration;
            }
        }
        
        const totalSeconds = totalActiveSeconds + totalInactiveSeconds;
        const activePercent = totalSeconds > 0 ? Math.round((totalActiveSeconds / totalSeconds) * 100) : 0;
        
        // Formatage des durées
        activeTime.textContent = this.formatDuration(totalActiveSeconds);
        activeTimePercent.textContent = activePercent;
        totalTime.textContent = this.formatDuration(totalSeconds);
        
        // Nombre total de classifications
        totalClassifications.textContent = data.total_classifications || '0';
    },
    
    /**
     * Formatte une durée en secondes en format heures/minutes
     * @param {number} seconds - Durée en secondes
     * @returns {string} Durée formatée
     */
    formatDuration: function(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    },
    
    /**
     * Retourne une activité avec son icône
     * @param {string} activity - Nom de l'activité
     * @returns {string} Activité avec son icône
     */
    getActivityWithIcon: function(activity) {
        // Utiliser la fonction Utils.getActivityIcon si disponible
        if (window.Utils && typeof Utils.getActivityIcon === 'function') {
            return `${Utils.getActivityIcon(activity)} ${activity}`;
        }
        
        // Sinon, utiliser des icônes par défaut
        const defaultIcons = {
            'travail sur ordinateur': '💻',
            'en conversation': '💬',
            'à table': '🍽️',
            'au téléphone': '📱',
            'endormi': '😴',
            'inactif': '⏸️',
            'occupé': '🔄',
            'lisant': '📖'
        };
        
        const icon = defaultIcons[activity] || '📊';
        return `${icon} ${activity}`;
    },
    
    /**
     * Affiche un état de chargement dans le résumé
     */
    showLoading: function() {
        const summaryValues = document.querySelectorAll('.summary-value, .summary-info span');
        summaryValues.forEach(value => {
            value.textContent = '...';
        });
    },
    
    /**
     * Affiche un état d'erreur dans le résumé
     */
    showError: function() {
        const summaryValues = document.querySelectorAll('.summary-value');
        summaryValues.forEach(value => {
            value.textContent = '-';
        });
        
        const summarySpans = document.querySelectorAll('.summary-info span');
        summarySpans.forEach(span => {
            span.textContent = '0';
        });
    }
};

// Exporter le module
window.SummaryManager = SummaryManager;
