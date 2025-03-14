/**
 * Script pour la page de statistiques
 * Gère l'affichage et l'export des statistiques d'activité
 */

// Gestionnaire des statistiques
const Statistics = {
    // État des statistiques
    state: {
        currentPeriod: 'day', // 'day', 'week', 'month', 'year'
        charts: {
            distribution: null,
            duration: null,
            hourly: null,
            trends: null
        },
        data: {
            day: null,
            week: null,
            month: null,
            year: null
        },
        colors: CONFIG.ACTIVITY_COLORS
    },
    
    /**
     * Initialise la page de statistiques
     */
    init: function() {
        // Initialiser les écouteurs pour les sélecteurs de période
        const periodButtons = document.querySelectorAll('.period-btn');
        if (periodButtons.length) {
            periodButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    const period = e.target.getAttribute('data-period');
                    if (period) {
                        this.changePeriod(period);
                        
                        // Mettre à jour la classe active
                        periodButtons.forEach(btn => btn.classList.remove('active'));
                        e.target.classList.add('active');
                    }
                });
            });
        }
        
        // Initialiser les écouteurs pour les boutons d'export
        const exportCsvButton = document.getElementById('export-csv');
        const exportJsonButton = document.getElementById('export-json');
        const exportPdfButton = document.getElementById('export-pdf');
        
        if (exportCsvButton) {
            exportCsvButton.addEventListener('click', () => {
                this.exportData('csv');
            });
        }
        
        if (exportJsonButton) {
            exportJsonButton.addEventListener('click', () => {
                this.exportData('json');
            });
        }
        
        if (exportPdfButton) {
            exportPdfButton.addEventListener('click', () => {
                this.exportData('pdf');
            });
        }
        
        // Charger les données pour la période actuelle
        this.loadData(this.state.currentPeriod);
    },
    
    /**
     * Change la période affichée
     * @param {string} period - Période à afficher ('day', 'week', 'month', 'year')
     */
    changePeriod: function(period) {
        if (period === this.state.currentPeriod) return;
        
        this.state.currentPeriod = period;
        
        // Charger les données si elles ne sont pas déjà en cache
        if (!this.state.data[period]) {
            this.loadData(period);
        } else {
            // Sinon, mettre à jour les graphiques avec les données en cache
            this.updateCharts(this.state.data[period]);
            this.updateSummary(this.state.data[period]);
        }
    },
    
    /**
     * Charge les données de statistiques depuis l'API
     * @param {string} period - Période à charger ('day', 'week', 'month', 'year')
     */
    loadData: async function(period) {
        try {
            // Afficher un état de chargement
            this.showLoading();
            
            // Récupérer les données de l'API
            const data = await Utils.fetchAPI(`/statistics?period=${period}`);
            
            if (!data) {
                throw new Error('Données de statistiques non disponibles');
            }
            
            // Mettre en cache les données
            this.state.data[period] = data;
            
            // Mettre à jour les graphiques
            this.updateCharts(data);
            
            // Mettre à jour le résumé
            this.updateSummary(data);
            
        } catch (error) {
            console.error(`Erreur lors du chargement des statistiques pour la période ${period}:`, error);
            this.showError();
        }
    },
    
    /**
     * Affiche un état de chargement
     */
    showLoading: function() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.innerHTML = '<div class="loading-indicator">Chargement des données...</div>';
        });
        
        const summaryValues = document.querySelectorAll('.summary-value, .summary-info span');
        summaryValues.forEach(value => {
            value.textContent = '...';
        });
    },
    
    /**
     * Affiche un message d'erreur
     */
    showError: function() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.innerHTML = '<div class="error-message">Erreur lors du chargement des données</div>';
        });
        
        const summaryValues = document.querySelectorAll('.summary-value');
        summaryValues.forEach(value => {
            value.textContent = '-';
        });
        
        const summarySpans = document.querySelectorAll('.summary-info span');
        summarySpans.forEach(span => {
            span.textContent = '0';
        });
    },
    
    /**
     * Met à jour tous les graphiques avec les données
     * @param {Object} data - Données de statistiques
     */
    updateCharts: function(data) {
        this.createDistributionChart(data);
        this.createDurationChart(data);
        this.createHourlyDistributionChart(data);
        this.createTrendsChart(data);
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
                                    const icon = Utils.getActivityIcon(activity);
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
                                const icon = Utils.getActivityIcon(activity);
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
        
        // Récupérer ou simuler les données de distribution horaire
        const hourly = data.hourly_distribution || this.simulateHourlyData();
        
        // Préparer les données pour le graphique
        const hours = Array.from({ length: 24 }, (_, i) => i);
        const activities = Object.keys(CONFIG.ACTIVITY_COLORS);
        
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
                                    const icon = Utils.getActivityIcon(activity);
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
        
        // Récupérer ou simuler les données de tendances
        const trends = data.trends || this.simulateTrendsData();
        
        // Préparer les données pour le graphique
        const timePoints = trends.map(t => t.date);
        const activities = Object.keys(CONFIG.ACTIVITY_COLORS);
        
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
                                    const icon = Utils.getActivityIcon(activity);
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
     * Simule des données de distribution horaire
     * Utilisé seulement si l'API ne fournit pas ces données
     * @returns {Array} Données simulées
     */
    simulateHourlyData: function() {
        const hours = Array.from({ length: 24 }, (_, i) => i);
        const activities = Object.keys(CONFIG.ACTIVITY_COLORS);
        
        return hours.map(hour => {
            const activitiesData = {};
            activities.forEach(activity => {
                // Simuler des modèles réalistes
                if (hour >= 0 && hour < 6) {
                    // Nuit
                    activitiesData[activity] = activity === 'endormi' ? Math.floor(Math.random() * 10) + 10 : Math.floor(Math.random() * 3);
                } else if (hour >= 6 && hour < 9) {
                    // Matin
                    activitiesData[activity] = activity === 'à table' ? Math.floor(Math.random() * 10) + 5 : Math.floor(Math.random() * 5);
                } else if (hour >= 9 && hour < 12) {
                    // Milieu de matinée
                    activitiesData[activity] = activity === 'occupé' ? Math.floor(Math.random() * 10) + 5 : Math.floor(Math.random() * 5);
                } else if (hour >= 12 && hour < 14) {
                    // Midi
                    activitiesData[activity] = activity === 'à table' ? Math.floor(Math.random() * 10) + 5 : Math.floor(Math.random() * 5);
                } else if (hour >= 14 && hour < 18) {
                    // Après-midi
                    activitiesData[activity] = activity === 'occupé' ? Math.floor(Math.random() * 10) + 5 : Math.floor(Math.random() * 5);
                } else if (hour >= 18 && hour < 21) {
                    // Soir
                    activitiesData[activity] = activity === 'au téléphone' || activity === 'en conversation' ? 
                        Math.floor(Math.random() * 10) + 5 : Math.floor(Math.random() * 5);
                } else {
                    // Fin de soirée
                    activitiesData[activity] = activity === 'lisant' || activity === 'inactif' ? 
                        Math.floor(Math.random() * 10) + 5 : Math.floor(Math.random() * 5);
                }
            });
            
            return {
                hour: hour,
                activities: activitiesData
            };
        });
    },
    
    /**
     * Simule des données de tendances
     * Utilisé seulement si l'API ne fournit pas ces données
     * @returns {Array} Données simulées
     */
    simulateTrendsData: function() {
        const activities = Object.keys(CONFIG.ACTIVITY_COLORS);
        let timePoints = [];
        
        // Générer des points temporels en fonction de la période
        switch (this.state.currentPeriod) {
            case 'day':
                // Un point par heure
                timePoints = Array.from({ length: 24 }, (_, i) => `${i}h`);
                break;
            case 'week':
                // Un point par jour
                timePoints = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
                break;
            case 'month':
                // Un point tous les deux jours
                timePoints = Array.from({ length: 15 }, (_, i) => `Jour ${(i + 1) * 2}`);
                break;
            case 'year':
                // Un point par mois
                timePoints = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'];
                break;
            default:
                timePoints = Array.from({ length: 10 }, (_, i) => `Point ${i + 1}`);
        }
        
        return timePoints.map(date => {
            const activitiesData = {};
            activities.forEach(activity => {
                // Valeur de base pour l'activité (entre 0 et 60 minutes)
                activitiesData[activity] = Math.floor(Math.random() * 60);
            });
            
            return {
                date: date,
                activities: activitiesData
            };
        });
    },
    
    /**
     * Met à jour le résumé des statistiques
     * @param {Object} data - Données de statistiques
     */
    updateSummary: function(data) {
        // Activité principale (celle avec la plus longue durée)
        const mainActivity = document.getElementById('main-activity');
        const mainActivityPercent = document.getElementById('main-activity-percent');
        
        // Activité la plus fréquente (celle avec le plus d'occurrences)
        const mostFrequentActivity = document.getElementById('most-frequent-activity');
        const mostFrequentActivityCount = document.getElementById('most-frequent-activity-count');
        
        // Temps actif et total
        const activeTime = document.getElementById('active-time');
        const activeTimePercent = document.getElementById('active-time-percent');
        const totalTime = document.getElementById('total-time');
        const totalClassifications = document.getElementById('total-classifications');
        
        // Trouver l'activité avec la plus longue durée
        if (mainActivity && mainActivityPercent && data.activity_durations) {
            const activities = Object.entries(data.activity_durations);
            if (activities.length > 0) {
                const sorted = activities.sort((a, b) => b[1] - a[1]);
                const [activity, duration] = sorted[0];
                const totalDuration = activities.reduce((sum, [, d]) => sum + d, 0);
                const percent = totalDuration > 0 ? Math.round((duration / totalDuration) * 100) : 0;
                
                mainActivity.textContent = `${Utils.getActivityIcon(activity)} ${activity}`;
                mainActivityPercent.textContent = percent;
            } else {
                mainActivity.textContent = '-';
                mainActivityPercent.textContent = '0';
            }
        }
        
        // Trouver l'activité la plus fréquente
        if (mostFrequentActivity && mostFrequentActivityCount && data.activity_counts) {
            const activities = Object.entries(data.activity_counts);
            if (activities.length > 0) {
                const sorted = activities.sort((a, b) => b[1] - a[1]);
                const [activity, count] = sorted[0];
                
                mostFrequentActivity.textContent = `${Utils.getActivityIcon(activity)} ${activity}`;
                mostFrequentActivityCount.textContent = count;
            } else {
                mostFrequentActivity.textContent = '-';
                mostFrequentActivityCount.textContent = '0';
            }
        }
        
        // Calculer le temps actif et total
        if (activeTime && activeTimePercent && totalTime && totalClassifications && data.activity_durations) {
            let totalActiveSeconds = 0;
            let totalInactiveSeconds = 0;
            
            for (const [activity, duration] of Object.entries(data.activity_durations)) {
                if (activity === 'inactif') {
                    totalInactiveSeconds += duration;
                } else {
                    totalActiveSeconds += duration;
                }
            }
            
            const totalSeconds = totalActiveSeconds + totalInactiveSeconds;
            const activePercent = totalSeconds > 0 ? Math.round((totalActiveSeconds / totalSeconds) * 100) : 0;
            
            // Formatage des durées
            const activeHours = Math.floor(totalActiveSeconds / 3600);
            const activeMinutes = Math.floor((totalActiveSeconds % 3600) / 60);
            
            const totalHours = Math.floor(totalSeconds / 3600);
            const totalMinutes = Math.floor((totalSeconds % 3600) / 60);
            
            activeTime.textContent = `${activeHours}h ${activeMinutes}m`;
            activeTimePercent.textContent = activePercent;
            totalTime.textContent = `${totalHours}h ${totalMinutes}m`;
            
            // Nombre total de classifications
            totalClassifications.textContent = data.total_classifications || '0';
        }
    },
    
    /**
     * Exporte les données statistiques
     * @param {string} format - Format d'export ('csv', 'json', 'pdf')
     */
    exportData: function(format) {
        const data = this.state.data[this.state.currentPeriod];
        if (!data) {
            Utils.showError('Aucune donnée à exporter');
            return;
        }
        
        try {
            switch (format) {
                case 'csv':
                    this.exportCSV(data);
                    break;
                case 'json':
                    this.exportJSON(data);
                    break;
                case 'pdf':
                    this.exportPDF(data);
                    break;
            }
        } catch (error) {
            console.error(`Erreur lors de l'exportation en ${format}:`, error);
            Utils.showError(`Erreur lors de l'exportation en ${format}`);
        }
    },
    
    /**
     * Exporte les données en CSV
     * @param {Object} data - Données à exporter
     */
    exportCSV: function(data) {
        // Créer le contenu CSV pour les activités
        let csvContent = 'Activité,Occurrences,Durée (secondes)\n';
        
        const activities = Object.keys(CONFIG.ACTIVITY_COLORS);
        activities.forEach(activity => {
            const count = data.activity_counts?.[activity] || 0;
            const duration = data.activity_durations?.[activity] || 0;
            csvContent += `"${activity}",${count},${duration}\n`;
        });
        
        // Ajouter une section pour les tendances horaires si disponibles
        if (data.hourly_distribution && data.hourly_distribution.length > 0) {
            csvContent += '\nDistribution horaire\n';
            csvContent += 'Heure,' + activities.join(',') + '\n';
            
            for (let hour = 0; hour < 24; hour++) {
                const hourData = data.hourly_distribution.find(h => h.hour === hour) || { activities: {} };
                csvContent += `${hour}`;
                
                activities.forEach(activity => {
                    csvContent += `,${hourData.activities[activity] || 0}`;
                });
                
                csvContent += '\n';
            }
        }
        
        // Créer un blob et lancer le téléchargement
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        link.setAttribute('href', url);
        link.setAttribute('download', `statistiques_${this.state.currentPeriod}_${new Date().toISOString().slice(0, 10)}.csv`);
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    
    /**
     * Exporte les données en JSON
     * @param {Object} data - Données à exporter
     */
    exportJSON: function(data) {
        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        link.setAttribute('href', url);
        link.setAttribute('download', `statistiques_${this.state.currentPeriod}_${new Date().toISOString().slice(0, 10)}.json`);
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    
    /**
     * Exporte les données en PDF (simulation)
     * @param {Object} data - Données à exporter
     */
    exportPDF: function(data) {
        // Dans une vraie application, on utiliserait une bibliothèque comme jsPDF
        // Pour cet exemple, on affiche simplement un message
        Utils.showError('Génération de PDF en cours...', 2000);
        
        setTimeout(() => {
            Utils.showError('La fonctionnalité d\'export PDF sera disponible dans une prochaine mise à jour.', 5000);
        }, 2000);
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    Statistics.init();
});
