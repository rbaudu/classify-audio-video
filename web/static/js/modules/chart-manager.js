/**
 * Module de gestion des graphiques statistiques
 * Crée et met à jour les différents graphiques à partir des données
 */

const ChartManager = {
    // État du gestionnaire de graphiques
    state: {
        charts: {
            distribution: null,
            duration: null,
            hourly: null,
            trends: null
        },
        colors: null,
        currentPeriod: 'day'
    },

    /**
     * Initialise le gestionnaire de graphiques
     * @param {Object} colors - Couleurs associées aux activités
     */
    init: function(colors) {
        this.state.colors = colors || CONFIG.ACTIVITY_COLORS;
    },
    
    /**
     * Définit la période actuelle
     * @param {string} period - Période actuelle ('day', 'week', 'month', 'year')
     */
    setPeriod: function(period) {
        this.state.currentPeriod = period;
    },
    
    /**
     * Met à jour tous les graphiques avec les données
     * @param {Object} data - Données de statistiques
     */
    updateCharts: function(data) {
        if (!data) return;
        
        this.createDistributionChart(data);
        this.createDurationChart(data);
        this.createHourlyDistributionChart(data);
        this.createTrendsChart(data);
    },
    
    /**
     * Nettoie tous les graphiques
     */
    clearCharts: function() {
        for (const key in this.state.charts) {
            if (this.state.charts[key]) {
                this.state.charts[key].destroy();
                this.state.charts[key] = null;
            }
        }
    },
    
    /**
     * Crée le graphique de répartition des activités
     * @param {Object} data - Données de statistiques
     */
    createDistributionChart: function(data) {
        const canvas = document.getElementById('activity-distribution-chart');
        if (!canvas) return;
        
        // Récupérer les données de répartition
        const activities = Object.keys(data.activity_counts || {});
        const counts = activities.map(activity => data.activity_counts[activity] || 0);
        
        // Nettoyer le canvas si un graphique existe déjà
        if (this.state.charts.distribution) {
            this.state.charts.distribution.destroy();
        }
        
        // Créer le graphique
        this.state.charts.distribution = new Chart(canvas, {
            type: 'pie',
            data: {
                labels: activities,
                datasets: [{
                    data: counts,
                    backgroundColor: activities.map(activity => this.state.colors[activity] || '#cccccc'),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12
                            },
                            generateLabels: function(chart) {
                                const labels = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                                labels.forEach((label, i) => {
                                    const activity = activities[i];
                                    const icon = Utils.getActivityIcon ? Utils.getActivityIcon(activity) : '📊';
                                    label.text = `${icon} ${label.text}`;
                                });
                                return labels;
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = counts.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Crée le graphique de durée par activité
     * @param {Object} data - Données de statistiques
     */
    createDurationChart: function(data) {
        const canvas = document.getElementById('activity-duration-chart');
        if (!canvas) return;
        
        // Récupérer les données de durée
        const activities = Object.keys(data.activity_durations || {});
        const durations = activities.map(activity => {
            // Convertir en minutes pour une meilleure lisibilité
            return Math.round((data.activity_durations[activity] || 0) / 60);
        });
        
        // Nettoyer le canvas si un graphique existe déjà
        if (this.state.charts.duration) {
            this.state.charts.duration.destroy();
        }
        
        // Créer le graphique
        this.state.charts.duration = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: activities,
                datasets: [{
                    label: 'Durée (minutes)',
                    data: durations,
                    backgroundColor: activities.map(activity => this.state.colors[activity] || '#cccccc'),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const minutes = context.raw || 0;
                                const hours = Math.floor(minutes / 60);
                                const mins = minutes % 60;
                                return `Durée: ${hours}h ${mins}m`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Minutes'
                        }
                    },
                    y: {
                        ticks: {
                            callback: function(value, index) {
                                const activity = activities[index];
                                const icon = Utils.getActivityIcon ? Utils.getActivityIcon(activity) : '📊';
                                return `${icon} ${activity}`;
                            }
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Crée le graphique de distribution horaire
     * @param {Object} data - Données de statistiques
     */
    createHourlyDistributionChart: function(data) {
        const canvas = document.getElementById('hourly-distribution-chart');
        if (!canvas) return;
        
        // Nettoyer le canvas si un graphique existe déjà
        if (this.state.charts.hourly) {
            this.state.charts.hourly.destroy();
        }
        
        // Récupérer les données de distribution horaire
        const hourly = data.hourly_distribution || [];
        
        // Préparer les données pour le graphique
        const hours = Array.from({ length: 24 }, (_, i) => i);
        const activities = Object.keys(this.state.colors);
        
        const datasets = activities.map(activity => {
            return {
                label: activity,
                data: hours.map(hour => {
                    const hourData = hourly.find(h => h.hour === hour) || { activities: {} };
                    return hourData.activities[activity] || 0;
                }),
                backgroundColor: this.state.colors[activity] || '#cccccc',
                borderWidth: 1
            };
        });
        
        // Créer le graphique
        this.state.charts.hourly = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: hours.map(hour => `${hour}h`),
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12
                            },
                            generateLabels: function(chart) {
                                const labels = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                                labels.forEach((label, i) => {
                                    const activity = activities[i];
                                    const icon = Utils.getActivityIcon ? Utils.getActivityIcon(activity) : '📊';
                                    label.text = `${icon} ${label.text}`;
                                });
                                return labels;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Heure de la journée'
                        },
                        stacked: true
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Occurrences'
                        },
                        stacked: true
                    }
                }
            }
        });
    },
    
    /**
     * Crée le graphique de tendances d'activité
     * @param {Object} data - Données de statistiques
     */
    createTrendsChart: function(data) {
        const canvas = document.getElementById('activity-trends-chart');
        if (!canvas) return;
        
        // Nettoyer le canvas si un graphique existe déjà
        if (this.state.charts.trends) {
            this.state.charts.trends.destroy();
        }
        
        // Récupérer les données de tendances
        const trends = data.trends || [];
        
        // Préparer les données pour le graphique
        const timePoints = trends.map(t => t.date);
        const activities = Object.keys(this.state.colors);
        
        const datasets = activities.map(activity => {
            return {
                label: activity,
                data: trends.map(t => t.activities[activity] || 0),
                borderColor: this.state.colors[activity] || '#cccccc',
                backgroundColor: 'transparent',
                tension: 0.1
            };
        });
        
        // Créer le graphique
        this.state.charts.trends = new Chart(canvas, {
            type: 'line',
            data: {
                labels: timePoints,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12
                            },
                            generateLabels: function(chart) {
                                const labels = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                                labels.forEach((label, i) => {
                                    const activity = activities[i];
                                    const icon = Utils.getActivityIcon ? Utils.getActivityIcon(activity) : '📊';
                                    label.text = `${icon} ${label.text}`;
                                });
                                return labels;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: this.getPeriodTimeLabel()
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Durée (minutes)'
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Obtient le libellé de l'axe X en fonction de la période
     * @returns {string} Libellé de l'axe X
     */
    getPeriodTimeLabel: function() {
        switch (this.state.currentPeriod) {
            case 'day':
                return 'Heures';
            case 'week':
                return 'Jours';
            case 'month':
                return 'Jours du mois';
            case 'year':
                return 'Mois';
            default:
                return 'Temps';
        }
    },
    
    /**
     * Affiche un message de chargement sur tous les graphiques
     */
    showLoading: function() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.innerHTML = '<div class="loading-indicator">Chargement des données...</div>';
        });
    },
    
    /**
     * Affiche un message d'erreur sur tous les graphiques
     */
    showError: function() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.innerHTML = '<div class="error-message">Erreur lors du chargement des données</div>';
        });
    }
};

// Exporter le module
window.ChartManager = ChartManager;
