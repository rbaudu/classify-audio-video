/**
 * Module d'informations sur le modèle
 * Gère les informations, l'entrainement et l'exportation du modèle
 */

const ModelInfo = {
    // État des informations du modèle
    state: {
        modelInfo: {
            name: 'Classificateur basé sur des règles',
            accuracy: 0.85,
            lastUpdate: '2025-03-12T10:30:00'
        }
    },

    /**
     * Initialise le module d'informations sur le modèle
     */
    init: function() {
        // Initialiser les écouteurs d'événements pour les boutons
        const retrainModelButton = document.getElementById('retrain-model');
        if (retrainModelButton) {
            retrainModelButton.addEventListener('click', () => {
                this.retrainModel();
            });
        }
        
        const exportModelButton = document.getElementById('export-model');
        if (exportModelButton) {
            exportModelButton.addEventListener('click', () => {
                this.exportModel();
            });
        }
        
        const importModelButton = document.getElementById('import-model');
        if (importModelButton) {
            importModelButton.addEventListener('click', () => {
                this.importModel();
            });
        }
        
        // Mettre à jour l'affichage des informations
        this.updateDisplay();
    },
    
    /**
     * Met à jour l'affichage des informations du modèle
     */
    updateDisplay: function() {
        document.getElementById('model-name')?.textContent = this.state.modelInfo.name;
        document.getElementById('model-accuracy')?.textContent = `${Math.round(this.state.modelInfo.accuracy * 100)}%`;
        
        const lastUpdate = new Date(this.state.modelInfo.lastUpdate);
        const formattedDate = lastUpdate.toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        document.getElementById('model-last-update')?.textContent = formattedDate;
    },
    
    /**
     * Simule le réentraînement du modèle
     */
    retrainModel: function() {
        // Afficher un indicateur de chargement
        const modelName = document.getElementById('model-name');
        const modelAccuracy = document.getElementById('model-accuracy');
        const modelLastUpdate = document.getElementById('model-last-update');
        
        if (modelName) modelName.textContent = 'Réentraînement en cours...';
        if (modelAccuracy) modelAccuracy.textContent = '...';
        if (modelLastUpdate) modelLastUpdate.textContent = '...';
        
        // Simuler un délai pour le réentraînement
        setTimeout(() => {
            // Mettre à jour les informations du modèle
            this.state.modelInfo = {
                name: 'Classificateur réentraîné',
                accuracy: Math.random() * 0.1 + 0.85, // Entre 0.85 et 0.95
                lastUpdate: new Date().toISOString()
            };
            
            // Mettre à jour l'affichage
            this.updateDisplay();
        }, 2000);
    },
    
    /**
     * Simule l'exportation du modèle
     */
    exportModel: function() {
        alert('Fonctionnalité d\'exportation du modèle non implémentée');
    },
    
    /**
     * Simule l'importation d'un modèle
     */
    importModel: function() {
        alert('Fonctionnalité d\'importation du modèle non implémentée');
    },
    
    /**
     * Obtient les informations actuelles du modèle
     * @returns {Object} Informations du modèle
     */
    getModelInfo: function() {
        return { ...this.state.modelInfo };
    }
};

// Exporter le module
window.ModelInfo = ModelInfo;
