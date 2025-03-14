/**
 * Script pour la page de tableau de bord
 * Gère l'affichage et les mises à jour des informations en temps réel
 */

// Gestionnaire du tableau de bord
const Dashboard = {
    // État du tableau de bord
    state: {
        currentActivity: null,
        lastUpdateTime: null,
        todayActivities: [],
        refreshInterval: null
    },
    
    /**
     * Initialise le tableau de bord
     */
    init: function() {
        // Démarrer la mise à jour automatique
        this.startAutoRefresh();
        
        // Charger les données initiales
        this.updateDashboard();
        
        // Ajouter un gestionnaire pour les reconnexions au serveur
        document.addEventListener('server-reconnected', () => {
            console.log('Reconnecté au serveur, mise à jour du tableau de bord');
            this.updateDashboard();
        });
    },
    
    /**
     * Démarre le rafraîchissement automatique du tableau de bord
     */
    startAutoRefresh: function() {
        // Nettoyer l'intervalle existant si nécessaire
        if (this.state.refreshInterval) {
            clearInterval(this.state.refreshInterval);
        }
        
        // Créer un nouvel intervalle
        this.state.refreshInterval = setInterval(() => {
            this.updateDashboard();
        }, CONFIG.REFRESH_INTERVAL);
    },
    
    /**
     * Met à jour toutes les informations du tableau de bord
     */
    updateDashboard: async function() {
        try {
            // Récupérer l'activité actuelle
            await this.updateCurrentActivity();
            
            // Récupérer les statistiques du jour
            await this.updateDailyStatistics();
            
            // Récupérer la chronologie des activités
            await this.updateActivityTimeline();
            
        } catch (error) {
            console.error('Erreur lors de la mise à jour du tableau de bord:', error);
        }
    },
    
    /**
     * Met à jour l'affichage de l'activité actuelle
     */
    updateCurrentActivity: async function() {
        try {
            const activity = await Utils.fetchAPI('/current-activity');
            
            if (!activity) {
                return;
            }
            
            this.state.currentActivity = activity;
            this.state.lastUpdateTime = new Date();
            
            // Mettre à jour l'interface
            const activityElement = document.getElementById('current-activity');
            if (activityElement) {
                const iconElement = activityElement.querySelector('.activity-icon');
                const nameElement = activityElement.querySelector('.activity-name');
                const timeElement = document.getElementById('last-update-time');
                
                if (iconElement && nameElement && timeElement) {
                    iconElement.textContent = Utils.getActivityIcon(activity.activity);
                    nameElement.textContent = activity.activity;
                    timeElement.textContent = Utils.formatDateTime(activity.timestamp);
                    
                    // Appliquer une couleur de fond légère basée sur l'activité
                    activityElement.style.backgroundColor = `${Utils.getActivityColor(activity.activity)}33`; // 33 = 20% d'opacité en hex
                }
            }
        } catch (error) {
            console.error('Erreur lors de la mise à jour de l\'activité actuelle:', error);
        }
    },
    
    /**
     * Met à jour les statistiques quotidiennes
     */
    updateDailyStatistics: async function() {
        try {
            const stats = await Utils.fetchAPI('/statistics?period=day');
            
            if (!stats) {
                return;
            }
            
            // Mettre à jour les compteurs
            const totalActivitiesElement = document.getElementById('total-activities-today');
            const mostCommonActivityElement = document.getElementById('most-common-activity');
            const activeTimeElement = document.getElementById('active-time');
            const inactiveTimeElement = document.getElementById('inactive-time');
            
            if (totalActivitiesElement && stats.activity_counts) {
                const totalCount = Object.values(stats.activity_counts).reduce((sum, count) => sum + count, 0);
                totalActivitiesElement.textContent = totalCount;
            }
            
            if (mostCommonActivityElement && stats.most_frequent_activity) {
                mostCommonActivityElement.textContent = stats.most_frequent_activity;
            }
            
            if (activeTimeElement && inactiveTimeElement && stats.activity_durations) {
                // Calculer le temps actif (tout sauf "inactif")
                let activeMinutes = 0;
                let inactiveMinutes = 0;
                
                for (const [activity, duration] of Object.entries(stats.activity_durations)) {
                    if (activity === 'inactif') {
                        inactiveMinutes += duration;
                    } else {
                        activeMinutes += duration;
                    }
                }
                
                activeTimeElement.textContent = `${Math.floor(activeMinutes / 60)}h ${Math.floor(activeMinutes % 60)}m`;
                inactiveTimeElement.textContent = `${Math.floor(inactiveMinutes / 60)}h ${Math.floor(inactiveMinutes % 60)}m`;
            }
            
        } catch (error) {
            console.error('Erreur lors de la mise à jour des statistiques quotidiennes:', error);
        }
    },
    
    /**
     * Met à jour la chronologie des activités
     */
    updateActivityTimeline: async function() {
        try {
            // Récupérer les activités des dernières 24 heures
            const now = Math.floor(Date.now() / 1000);
            const dayAgo = now - (24 * 60 * 60);
            
            const activities = await Utils.fetchAPI(`/activities?start=${dayAgo}&end=${now}&limit=30`);
            
            if (!activities || !activities.length) {
                return;
            }
            
            // Enregistrer les activités dans l'état
            this.state.todayActivities = activities;
            
            // Mettre à jour l'interface
            const timelineElement = document.getElementById('activity-timeline');
            
            if (timelineElement) {
                // Vider l'élément existant
                timelineElement.innerHTML = '';
                
                // Créer un élément SVG pour la timeline
                const svgNS = "http://www.w3.org/2000/svg";
                const svg = document.createElementNS(svgNS, "svg");
                svg.setAttribute("width", "100%");
                svg.setAttribute("height", "100%");
                svg.style.display = "block";
                
                // Ajouter un titre
                const title = document.createElementNS(svgNS, "text");
                title.setAttribute("x", "10");
                title.setAttribute("y", "20");
                title.setAttribute("fill", "#333");
                title.setAttribute("font-size", "14px");
                title.textContent = "Activités des dernières 24 heures";
                svg.appendChild(title);
                
                // Paramètres de dessin
                const startY = 50;
                const barHeight = 30;
                const width = timelineElement.clientWidth;
                const padding = 40;
                
                // Calculer l'échelle de temps
                const minTime = activities.reduce((min, act) => Math.min(min, act.timestamp), Infinity);
                const maxTime = activities.reduce((max, act) => Math.max(max, act.timestamp), 0);
                const timeRange = maxTime - minTime;
                const timeScale = (width - padding * 2) / timeRange;
                
                // Dessiner l'axe de temps
                const timeAxis = document.createElementNS(svgNS, "line");
                timeAxis.setAttribute("x1", padding);
                timeAxis.setAttribute("y1", startY + barHeight + 10);
                timeAxis.setAttribute("x2", width - padding);
                timeAxis.setAttribute("y2", startY + barHeight + 10);
                timeAxis.setAttribute("stroke", "#ccc");
                timeAxis.setAttribute("stroke-width", "1");
                svg.appendChild(timeAxis);
                
                // Ajouter des marqueurs de temps
                const hourMarkers = 6; // Un marqueur toutes les 4 heures
                for (let i = 0; i <= hourMarkers; i++) {
                    const markerTime = minTime + (timeRange / hourMarkers) * i;
                    const markerX = padding + (markerTime - minTime) * timeScale;
                    
                    // Ligne de marqueur
                    const markerLine = document.createElementNS(svgNS, "line");
                    markerLine.setAttribute("x1", markerX);
                    markerLine.setAttribute("y1", startY + barHeight + 10);
                    markerLine.setAttribute("x2", markerX);
                    markerLine.setAttribute("y2", startY + barHeight + 15);
                    markerLine.setAttribute("stroke", "#999");
                    markerLine.setAttribute("stroke-width", "1");
                    svg.appendChild(markerLine);
                    
                    // Texte du marqueur
                    const markerText = document.createElementNS(svgNS, "text");
                    markerText.setAttribute("x", markerX);
                    markerText.setAttribute("y", startY + barHeight + 30);
                    markerText.setAttribute("text-anchor", "middle");
                    markerText.setAttribute("fill", "#666");
                    markerText.setAttribute("font-size", "12px");
                    
                    const markerDate = new Date(markerTime * 1000);
                    const hours = markerDate.getHours().toString().padStart(2, '0');
                    const minutes = markerDate.getMinutes().toString().padStart(2, '0');
                    markerText.textContent = `${hours}:${minutes}`;
                    
                    svg.appendChild(markerText);
                }
                
                // Dessiner les barres d'activité
                activities.forEach((activity, index) => {
                    if (index === 0) return; // Ignorer la première activité pour éviter une barre sans fin connue
                    
                    const duration = activity.timestamp - activities[index - 1].timestamp;
                    const x = padding + (activities[index - 1].timestamp - minTime) * timeScale;
                    const width = duration * timeScale;
                    
                    // Barre de l'activité
                    const rect = document.createElementNS(svgNS, "rect");
                    rect.setAttribute("x", x);
                    rect.setAttribute("y", startY);
                    rect.setAttribute("width", width);
                    rect.setAttribute("height", barHeight);
                    rect.setAttribute("fill", Utils.getActivityColor(activities[index - 1].activity));
                    rect.setAttribute("rx", "4");
                    rect.setAttribute("ry", "4");
                    
                    // Ajouter un tooltip
                    rect.setAttribute("data-activity", activities[index - 1].activity);
                    rect.setAttribute("data-start", Utils.formatDateTime(activities[index - 1].timestamp));
                    rect.setAttribute("data-end", Utils.formatDateTime(activity.timestamp));
                    rect.setAttribute("data-duration", Utils.formatDuration(duration));
                    
                    // Gestionnaire d'événements pour afficher les détails au survol
                    rect.addEventListener('mouseover', function(event) {
                        const tooltip = document.createElementNS(svgNS, "g");
                        tooltip.setAttribute("id", "activity-tooltip");
                        
                        const tooltipRect = document.createElementNS(svgNS, "rect");
                        tooltipRect.setAttribute("x", event.clientX - timelineElement.getBoundingClientRect().left);
                        tooltipRect.setAttribute("y", startY - 60);
                        tooltipRect.setAttribute("width", "200");
                        tooltipRect.setAttribute("height", "50");
                        tooltipRect.setAttribute("fill", "white");
                        tooltipRect.setAttribute("stroke", "#ccc");
                        tooltipRect.setAttribute("rx", "4");
                        tooltipRect.setAttribute("ry", "4");
                        
                        const tooltipText1 = document.createElementNS(svgNS, "text");
                        tooltipText1.setAttribute("x", event.clientX - timelineElement.getBoundingClientRect().left + 10);
                        tooltipText1.setAttribute("y", startY - 40);
                        tooltipText1.setAttribute("fill", "#333");
                        tooltipText1.textContent = this.getAttribute("data-activity");
                        
                        const tooltipText2 = document.createElementNS(svgNS, "text");
                        tooltipText2.setAttribute("x", event.clientX - timelineElement.getBoundingClientRect().left + 10);
                        tooltipText2.setAttribute("y", startY - 20);
                        tooltipText2.setAttribute("fill", "#666");
                        tooltipText2.textContent = `Durée: ${this.getAttribute("data-duration")}`;
                        
                        tooltip.appendChild(tooltipRect);
                        tooltip.appendChild(tooltipText1);
                        tooltip.appendChild(tooltipText2);
                        svg.appendChild(tooltip);
                    });
                    
                    rect.addEventListener('mouseout', function() {
                        const tooltip = document.getElementById("activity-tooltip");
                        if (tooltip) {
                            svg.removeChild(tooltip);
                        }
                    });
                    
                    svg.appendChild(rect);
                    
                    // Ajouter une icône si la largeur le permet
                    if (width > 30) {
                        const icon = document.createElementNS(svgNS, "text");
                        icon.setAttribute("x", x + width / 2);
                        icon.setAttribute("y", startY + barHeight / 2 + 5);
                        icon.setAttribute("text-anchor", "middle");
                        icon.setAttribute("dominant-baseline", "middle");
                        icon.setAttribute("fill", "white");
                        icon.setAttribute("font-size", "14px");
                        icon.textContent = Utils.getActivityIcon(activities[index - 1].activity);
                        svg.appendChild(icon);
                    }
                });
                
                timelineElement.appendChild(svg);
            }
            
        } catch (error) {
            console.error('Erreur lors de la mise à jour de la chronologie des activités:', error);
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    Dashboard.init();
});
