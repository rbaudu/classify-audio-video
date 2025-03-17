/**
 * Script principal pour la page de statistiques
 * Coordonne les différents modules pour l'affichage et l'export des statistiques d'activité
 */

// Gestionnaire des statistiques
const Statistics = {
    // État des statistiques
    state: {
        currentPeriod: 'day' // 'day', 'week', 'month', 'year'
    },
    
    /**
     * Initialise la page de statistiques
     */
    init: function() {
        console.log('Initialisation de la page de statistiques...');
        
        // Initialiser les modules
        if (window.ChartManager) {
            window.ChartManager.init(CONFIG.ACTIVITY_COLORS);
        }
        
        // Initialiser les écouteurs pour les sélecteurs de période
        this.initPeriodSelectors();
        
        // Initialiser les écouteurs pour les boutons d'export
        this.initExportButtons();
        
        // Charger les données pour la période actuelle
        this.loadCurrentPeriodData();
        
        console.log('Initialisation terminée');
    },
    
    /**
     * Initialise les écouteurs pour les sélecteurs de période
     */
    initPeriodSelectors: function() {
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
    },
    
    /**
     * Initialise les écouteurs pour les boutons d'export
     */
    initExportButtons: function() {
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
    },
    
    /**
     * Change la période affichée
     * @param {string} period - Période à afficher ('day', 'week', 'month', 'year')
     */
    changePeriod: function(period) {
        if (period === this.state.currentPeriod) return;
        
        this.state.currentPeriod = period;
        
        // Mettre à jour la période dans le gestionnaire de graphiques
        if (window.ChartManager) {
            window.ChartManager.setPeriod(period);
        }
        
        // Charger les données pour la nouvelle période
        this.loadCurrentPeriodData();
    },
    
    /**
     * Charge les données pour la période actuelle
     */
    loadCurrentPeriodData: function() {
        // Afficher un état de chargement
        this.showLoading();
        
        // Utiliser le module DataLoader s'il est disponible
        if (window.DataLoader) {
            window.DataLoader.loadData(
                this.state.currentPeriod,
                this.onDataLoadSuccess.bind(this),
                this.onDataLoadError.bind(this)
            );
        } else {
            // Simulation de chargement si le module n'est pas disponible
            setTimeout(() => {
                this.onDataLoadError(new Error('Module DataLoader non disponible'));
            }, 1000);
        }
    },
    
    /**
     * Callback en cas de succès du chargement des données
     * @param {Object} data - Données chargées
     */
    onDataLoadSuccess: function(data) {
        // Mettre à jour les graphiques
        if (window.ChartManager) {
            window.ChartManager.updateCharts(data);
        }
        
        // Mettre à jour le résumé
        if (window.SummaryManager) {
            window.SummaryManager.updateSummary(data);
        }
    },
    
    /**
     * Callback en cas d'erreur du chargement des données
     * @param {Error} error - Erreur survenue
     */
    onDataLoadError: function(error) {
        console.error('Erreur lors du chargement des données:', error);
        
        // Afficher un message d'erreur
        this.showError();
    },
    
    /**
     * Affiche un état de chargement
     */
    showLoading: function() {
        // Utiliser les modules pour afficher l'état de chargement
        if (window.ChartManager) {
            window.ChartManager.showLoading();
        }
        
        if (window.SummaryManager) {
            window.SummaryManager.showLoading();
        }
    },
    
    /**
     * Affiche un message d'erreur
     */
    showError: function() {
        // Utiliser les modules pour afficher l'état d'erreur
        if (window.ChartManager) {
            window.ChartManager.showError();
        }
        
        if (window.SummaryManager) {
            window.SummaryManager.showError();
        }
    },
    
    /**
     * Exporte les données statistiques
     * @param {string} format - Format d'export ('csv', 'json', 'pdf')
     */
    exportData: function(format) {
        // Utiliser le module ExportManager s'il est disponible
        if (window.ExportManager && window.DataLoader) {
            const data = window.DataLoader.getCachedData(this.state.currentPeriod);
            window.ExportManager.exportData(data, format, this.state.currentPeriod);
        } else {
            console.error('Module d\'exportation ou de chargement non disponible');
            if (window.Utils && Utils.showError) {
                Utils.showError('Fonction d\'exportation non disponible');
            } else {
                alert('Fonction d\'exportation non disponible');
            }
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Charger d'abord les modules
    const moduleUrls = [
        '/static/js/modules/data-loader.js',
        '/static/js/modules/chart-manager.js',
        '/static/js/modules/export-manager.js',
        '/static/js/modules/summary-manager.js'
    ];
    
    let modulesLoaded = 0;
    
    // Fonction à exécuter une fois tous les modules chargés
    const initApp = () => {
        Statistics.init();
    };
    
    // Charger chaque module de manière asynchrone
    moduleUrls.forEach(url => {
        const script = document.createElement('script');
        script.src = url;
        script.onload = () => {
            modulesLoaded++;
            if (modulesLoaded === moduleUrls.length) {
                // Tous les modules sont chargés, initialiser l'application
                initApp();
            }
        };
        script.onerror = (error) => {
            console.error(`Erreur lors du chargement du module ${url}:`, error);
            // Essayer d'initialiser quand même, certaines fonctionnalités pourraient ne pas être disponibles
            modulesLoaded++;
            if (modulesLoaded === moduleUrls.length) {
                initApp();
            }
        };
        document.head.appendChild(script);
    });
});
