/**
 * Module de chargement des données statistiques
 * Gère la récupération et le traitement des données depuis l'API
 */

const DataLoader = {
    // État du chargeur de données
    state: {
        data: {
            day: null,
            week: null,
            month: null,
            year: null
        },
        isLoading: false
    },

    /**
     * Charge les données de statistiques depuis l'API
     * @param {string} period - Période à charger ('day', 'week', 'month', 'year')
     * @param {function} onSuccess - Fonction de rappel en cas de succès
     * @param {function} onError - Fonction de rappel en cas d'erreur
     */
    loadData: async function(period, onSuccess, onError) {
        try {
            // Vérifier si les données sont déjà en cache
            if (this.state.data[period]) {
                if (onSuccess) onSuccess(this.state.data[period]);
                return this.state.data[period];
            }
            
            // Marquer comme en cours de chargement
            this.state.isLoading = true;
            
            // Récupérer les données de l'API
            const data = await this.fetchStatistics(period);
            
            if (!data) {
                throw new Error('Données de statistiques non disponibles');
            }
            
            // Mettre en cache les données
            this.state.data[period] = data;
            this.state.isLoading = false;
            
            // Appeler la fonction de rappel de succès
            if (onSuccess) onSuccess(data);
            
            return data;
            
        } catch (error) {
            console.error(`Erreur lors du chargement des statistiques pour la période ${period}:`, error);
            this.state.isLoading = false;
            
            // Appeler la fonction de rappel d'erreur
            if (onError) onError(error);
            
            return null;
        }
    },
    
    /**
     * Récupère les données statistiques depuis l'API
     * @param {string} period - Période à récupérer ('day', 'week', 'month', 'year')
     * @returns {Promise<Object>} Données de statistiques
     */
    fetchStatistics: async function(period) {
        // Utiliser la fonction Utils.fetchAPI si disponible, sinon utiliser fetch directement
        if (window.Utils && typeof window.Utils.fetchAPI === 'function') {
            return await window.Utils.fetchAPI(`/statistics?period=${period}`);
        } else {
            const response = await fetch(`/api/statistics?period=${period}`);
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return await response.json();
        }
    },
    
    /**
     * Obtient les données mises en cache pour une période donnée
     * @param {string} period - Période à obtenir ('day', 'week', 'month', 'year')
     * @returns {Object|null} Données mises en cache ou null
     */
    getCachedData: function(period) {
        return this.state.data[period] || null;
    },
    
    /**
     * Vérifie si les données pour une période sont en cours de chargement
     * @returns {boolean} Vrai si en cours de chargement
     */
    isLoading: function() {
        return this.state.isLoading;
    },
    
    /**
     * Simule des données pour les cas où l'API ne répond pas
     * @param {string} period - Période pour laquelle simuler des données
     * @returns {Object} Données simulées
     */
    simulateData: function(period) {
        // Générer des données de base
        const data = {
            period: period,
            total_classifications: Math.floor(Math.random() * 1000) + 100,
            activity_counts: {},
            activity_durations: {},
        };
        
        // Activités possibles
        const activities = Object.keys(CONFIG.ACTIVITY_COLORS || {
            'travail sur ordinateur': '#4CAF50',
            'en conversation': '#2196F3',
            'à table': '#FF9800',
            'au téléphone': '#E91E63',
            'endormi': '#673AB7',
            'inactif': '#9E9E9E',
            'occupé': '#3F51B5',
            'lisant': '#009688'
        });
        
        // Générer des données pour chaque activité
        activities.forEach(activity => {
            data.activity_counts[activity] = Math.floor(Math.random() * 100);
            data.activity_durations[activity] = Math.floor(Math.random() * 3600) + 60;
        });
        
        // Ajouter des données de tendances
        data.trends = this.simulateTrendsData(period, activities);
        
        // Ajouter des données de distribution horaire
        data.hourly_distribution = this.simulateHourlyData(activities);
        
        return data;
    },
    
    /**
     * Simule des données de distribution horaire
     * @param {Array} activities - Liste des activités
     * @returns {Array} Données simulées de distribution horaire
     */
    simulateHourlyData: function(activities) {
        const hours = Array.from({ length: 24 }, (_, i) => i);
        
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
     * @param {string} period - Période pour laquelle simuler des tendances
     * @param {Array} activities - Liste des activités
     * @returns {Array} Données simulées de tendances
     */
    simulateTrendsData: function(period, activities) {
        let timePoints = [];
        
        // Générer des points temporels en fonction de la période
        switch (period) {
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
    }
};

// Exporter le module
window.DataLoader = DataLoader;
