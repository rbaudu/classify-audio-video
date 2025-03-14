/**
 * Script pour la page d'historique des activités
 * Gère l'affichage, le filtrage et l'exportation de l'historique des activités
 */

// Gestionnaire de l'historique
const History = {
    // État de l'historique
    state: {
        activities: [],
        filteredActivities: [],
        currentPage: 1,
        itemsPerPage: 10,
        totalPages: 1,
        filters: {
            startDate: null,
            endDate: null,
            activityType: 'all'
        }
    },
    
    /**
     * Initialise la page d'historique
     */
    init: function() {
        // Initialiser les sélecteurs de date
        const today = new Date();
        const weekAgo = new Date();
        weekAgo.setDate(today.getDate() - 7);
        
        const startDateInput = document.getElementById('start-date');
        const endDateInput = document.getElementById('end-date');
        
        if (startDateInput && endDateInput) {
            startDateInput.valueAsDate = weekAgo;
            endDateInput.valueAsDate = today;
            
            this.state.filters.startDate = weekAgo;
            this.state.filters.endDate = today;
            
            // Ajouter les écouteurs d'événements pour les filtres
            startDateInput.addEventListener('change', (e) => {
                this.state.filters.startDate = e.target.valueAsDate;
            });
            
            endDateInput.addEventListener('change', (e) => {
                this.state.filters.endDate = e.target.valueAsDate;
            });
        }
        
        // Initialiser le sélecteur de type d'activité
        const activityTypeSelect = document.getElementById('activity-type');
        if (activityTypeSelect) {
            activityTypeSelect.addEventListener('change', (e) => {
                this.state.filters.activityType = e.target.value;
            });
        }
        
        // Ajouter l'écouteur pour le bouton d'application des filtres
        const applyFiltersButton = document.getElementById('apply-filters');
        if (applyFiltersButton) {
            applyFiltersButton.addEventListener('click', () => {
                this.applyFilters();
            });
        }
        
        // Ajouter les écouteurs pour la pagination
        const prevPageButton = document.getElementById('prev-page');
        const nextPageButton = document.getElementById('next-page');
        
        if (prevPageButton) {
            prevPageButton.addEventListener('click', () => {
                if (this.state.currentPage > 1) {
                    this.state.currentPage--;
                    this.renderActivities();
                }
            });
        }
        
        if (nextPageButton) {
            nextPageButton.addEventListener('click', () => {
                if (this.state.currentPage < this.state.totalPages) {
                    this.state.currentPage++;
                    this.renderActivities();
                }
            });
        }
        
        // Ajouter l'écouteur pour le bouton d'exportation
        const exportButton = document.getElementById('export-history');
        if (exportButton) {
            exportButton.addEventListener('click', () => {
                this.exportHistory();
            });
        }
        
        // Charger les données initiales
        this.loadActivities();
    },
    
    /**
     * Charge l'historique des activités depuis l'API
     */
    loadActivities: async function() {
        try {
            const startTimestamp = Math.floor(this.state.filters.startDate.getTime() / 1000);
            const endTimestamp = Math.floor(this.state.filters.endDate.getTime() / 1000);
            
            // Afficher l'indicateur de chargement
            const activitiesList = document.getElementById('activities-list');
            if (activitiesList) {
                activitiesList.innerHTML = '<div class="loading-indicator">Chargement de l\'historique...</div>';
            }
            
            // Récupérer les activités depuis l'API
            const activities = await Utils.fetchAPI(`/activities?start=${startTimestamp}&end=${endTimestamp}&limit=1000`);
            
            if (!activities || !activities.length) {
                if (activitiesList) {
                    activitiesList.innerHTML = '<div class="no-data-message">Aucune activité trouvée pour cette période.</div>';
                }
                return;
            }
            
            // Traiter les activités pour calculer les durées
            this.state.activities = this.processActivities(activities);
            
            // Appliquer les filtres initiaux
            this.applyFilters();
            
        } catch (error) {
            console.error('Erreur lors du chargement des activités:', error);
            const activitiesList = document.getElementById('activities-list');
            if (activitiesList) {
                activitiesList.innerHTML = '<div class="error-message">Erreur lors du chargement des activités.</div>';
            }
        }
    },
    
    /**
     * Traite les activités pour calculer les durées
     * @param {Array} activities - Liste des activités à traiter
     * @returns {Array} Liste des activités avec durées calculées
     */
    processActivities: function(activities) {
        // Trier les activités par timestamp (de la plus récente à la plus ancienne)
        const sortedActivities = [...activities].sort((a, b) => b.timestamp - a.timestamp);
        
        // Calculer la durée de chaque activité
        for (let i = 0; i < sortedActivities.length - 1; i++) {
            sortedActivities[i].duration = sortedActivities[i].timestamp - sortedActivities[i + 1].timestamp;
        }
        
        // La dernière activité (la plus ancienne) n'a pas de durée connue, donc on lui attribue une durée de 0
        if (sortedActivities.length > 0) {
            sortedActivities[sortedActivities.length - 1].duration = 0;
        }
        
        return sortedActivities;
    },
    
    /**
     * Applique les filtres actuels et met à jour l'affichage
     */
    applyFilters: function() {
        // Filtrer les activités par type si nécessaire
        if (this.state.filters.activityType === 'all') {
            this.state.filteredActivities = [...this.state.activities];
        } else {
            this.state.filteredActivities = this.state.activities.filter(
                activity => activity.activity === this.state.filters.activityType
            );
        }
        
        // Réinitialiser la pagination
        this.state.currentPage = 1;
        this.state.totalPages = Math.ceil(this.state.filteredActivities.length / this.state.itemsPerPage);
        
        // Mettre à jour l'affichage
        this.renderActivities();
    },
    
    /**
     * Affiche les activités filtrées et paginées
     */
    renderActivities: function() {
        const activitiesList = document.getElementById('activities-list');
        if (!activitiesList) return;
        
        // Vider la liste
        activitiesList.innerHTML = '';
        
        if (this.state.filteredActivities.length === 0) {
            activitiesList.innerHTML = '<div class="no-data-message">Aucune activité trouvée pour ces filtres.</div>';
            return;
        }
        
        // Calculer les indices de début et de fin pour la pagination
        const startIndex = (this.state.currentPage - 1) * this.state.itemsPerPage;
        const endIndex = Math.min(startIndex + this.state.itemsPerPage, this.state.filteredActivities.length);
        
        // Afficher les activités de la page actuelle
        for (let i = startIndex; i < endIndex; i++) {
            const activity = this.state.filteredActivities[i];
            
            // Créer l'élément de ligne
            const activityRow = document.createElement('div');
            activityRow.className = 'timeline-row';
            
            // Date et heure
            const dateCell = document.createElement('div');
            dateCell.className = 'cell date-cell';
            dateCell.textContent = Utils.formatDateTime(activity.timestamp, false);
            
            // Activité
            const activityCell = document.createElement('div');
            activityCell.className = 'cell activity-cell';
            
            const activityIcon = document.createElement('span');
            activityIcon.className = 'activity-icon';
            activityIcon.textContent = Utils.getActivityIcon(activity.activity);
            
            const activityName = document.createElement('span');
            activityName.className = 'activity-name';
            activityName.textContent = activity.activity;
            
            activityCell.appendChild(activityIcon);
            activityCell.appendChild(activityName);
            
            // Durée
            const durationCell = document.createElement('div');
            durationCell.className = 'cell duration-cell';
            durationCell.textContent = Utils.formatDuration(activity.duration);
            
            // Confiance
            const confidenceCell = document.createElement('div');
            confidenceCell.className = 'cell confidence-cell';
            
            if (activity.confidence !== undefined) {
                const confidenceValue = Math.round(activity.confidence * 100);
                
                const confidenceBar = document.createElement('div');
                confidenceBar.className = 'confidence-bar';
                
                const confidenceIndicator = document.createElement('div');
                confidenceIndicator.className = 'confidence-indicator';
                confidenceIndicator.style.width = `${confidenceValue}%`;
                confidenceIndicator.style.backgroundColor = this.getConfidenceColor(confidenceValue);
                
                confidenceBar.appendChild(confidenceIndicator);
                
                const confidenceText = document.createElement('span');
                confidenceText.className = 'confidence-text';
                confidenceText.textContent = `${confidenceValue}%`;
                
                confidenceCell.appendChild(confidenceBar);
                confidenceCell.appendChild(confidenceText);
            } else {
                confidenceCell.textContent = '-';
            }
            
            // Actions
            const actionsCell = document.createElement('div');
            actionsCell.className = 'cell actions-cell';
            
            const detailsButton = document.createElement('button');
            detailsButton.className = 'btn small';
            detailsButton.textContent = 'Détails';
            detailsButton.addEventListener('click', () => {
                this.showActivityDetails(activity);
            });
            
            actionsCell.appendChild(detailsButton);
            
            // Assembler la ligne
            activityRow.appendChild(dateCell);
            activityRow.appendChild(activityCell);
            activityRow.appendChild(durationCell);
            activityRow.appendChild(confidenceCell);
            activityRow.appendChild(actionsCell);
            
            activitiesList.appendChild(activityRow);
        }
        
        // Mettre à jour les informations de pagination
        const pageInfo = document.getElementById('page-info');
        if (pageInfo) {
            pageInfo.textContent = `Page ${this.state.currentPage} sur ${this.state.totalPages}`;
        }
        
        // Mettre à jour l'état des boutons de pagination
        const prevPageButton = document.getElementById('prev-page');
        const nextPageButton = document.getElementById('next-page');
        
        if (prevPageButton) {
            prevPageButton.disabled = this.state.currentPage === 1;
        }
        
        if (nextPageButton) {
            nextPageButton.disabled = this.state.currentPage === this.state.totalPages;
        }
    },
    
    /**
     * Affiche les détails d'une activité dans une modale
     * @param {Object} activity - L'activité dont on veut afficher les détails
     */
    showActivityDetails: function(activity) {
        const detailDatetime = document.getElementById('detail-datetime');
        const detailActivity = document.getElementById('detail-activity');
        const detailDuration = document.getElementById('detail-duration');
        const detailConfidence = document.getElementById('detail-confidence');
        const detailMetadata = document.getElementById('detail-metadata');
        
        if (detailDatetime) {
            detailDatetime.textContent = Utils.formatDateTime(activity.timestamp);
        }
        
        if (detailActivity) {
            detailActivity.textContent = `${Utils.getActivityIcon(activity.activity)} ${activity.activity}`;
        }
        
        if (detailDuration) {
            detailDuration.textContent = Utils.formatDuration(activity.duration);
        }
        
        if (detailConfidence) {
            detailConfidence.textContent = activity.confidence !== undefined
                ? `${Math.round(activity.confidence * 100)}%`
                : '-';
        }
        
        if (detailMetadata) {
            try {
                const metadata = activity.metadata || {};
                detailMetadata.textContent = JSON.stringify(metadata, null, 2);
            } catch (error) {
                detailMetadata.textContent = 'Aucune métadonnée disponible';
            }
        }
        
        // Ouvrir la modale
        ModalManager.openModal('activity-details-modal');
    },
    
    /**
     * Obtient une couleur basée sur le niveau de confiance
     * @param {number} confidence - Valeur de confiance (0-100)
     * @returns {string} Code couleur hexadécimal
     */
    getConfidenceColor: function(confidence) {
        if (confidence >= 80) {
            return '#4caf50'; // Vert
        } else if (confidence >= 60) {
            return '#8bc34a'; // Vert-jaune
        } else if (confidence >= 40) {
            return '#ffc107'; // Jaune
        } else if (confidence >= 20) {
            return '#ff9800'; // Orange
        } else {
            return '#f44336'; // Rouge
        }
    },
    
    /**
     * Exporte l'historique filtré au format CSV
     */
    exportHistory: function() {
        if (this.state.filteredActivities.length === 0) {
            Utils.showError('Aucune activité à exporter');
            return;
        }
        
        try {
            // Créer le contenu CSV
            let csvContent = 'Date,Activité,Durée,Confiance\n';
            
            this.state.filteredActivities.forEach(activity => {
                const date = Utils.formatDateTime(activity.timestamp);
                const duration = Utils.formatDuration(activity.duration);
                const confidence = activity.confidence !== undefined
                    ? `${Math.round(activity.confidence * 100)}%`
                    : '-';
                
                csvContent += `"${date}","${activity.activity}","${duration}","${confidence}"\n`;
            });
            
            // Créer un blob et un lien de téléchargement
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            
            const startDate = this.state.filters.startDate.toISOString().split('T')[0];
            const endDate = this.state.filters.endDate.toISOString().split('T')[0];
            const filename = `historique_activites_${startDate}_a_${endDate}.csv`;
            
            const link = document.createElement('a');
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Erreur lors de l\'exportation de l\'historique:', error);
            Utils.showError('Erreur lors de l\'exportation de l\'historique');
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    History.init();
});
