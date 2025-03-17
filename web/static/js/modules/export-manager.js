/**
 * Module de gestion des exportations de données statistiques
 * Gère l'exportation des données dans différents formats
 */

const ExportManager = {
    /**
     * Exporte les données statistiques dans le format spécifié
     * @param {Object} data - Données à exporter
     * @param {string} format - Format d'export ('csv', 'json', 'pdf')
     * @param {string} period - Période des données ('day', 'week', 'month', 'year')
     */
    exportData: function(data, format, period) {
        if (!data) {
            if (window.Utils && Utils.showError) {
                Utils.showError('Aucune donnée à exporter');
            } else {
                alert('Aucune donnée à exporter');
            }
            return;
        }
        
        try {
            switch (format) {
                case 'csv':
                    this.exportCSV(data, period);
                    break;
                case 'json':
                    this.exportJSON(data, period);
                    break;
                case 'pdf':
                    this.exportPDF(data, period);
                    break;
                default:
                    throw new Error(`Format d'export non reconnu: ${format}`);
            }
        } catch (error) {
            console.error(`Erreur lors de l'exportation en ${format}:`, error);
            if (window.Utils && Utils.showError) {
                Utils.showError(`Erreur lors de l'exportation en ${format}`);
            } else {
                alert(`Erreur lors de l'exportation en ${format}`);
            }
        }
    },
    
    /**
     * Exporte les données en CSV
     * @param {Object} data - Données à exporter
     * @param {string} period - Période des données ('day', 'week', 'month', 'year')
     */
    exportCSV: function(data, period) {
        // Récupérer la liste des activités
        const activities = Object.keys(data.activity_counts || {});
        
        // Créer le contenu CSV pour les activités
        let csvContent = 'Activité,Occurrences,Durée (secondes)\n';
        
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
        
        // Ajouter une section pour les tendances si disponibles
        if (data.trends && data.trends.length > 0) {
            csvContent += '\nTendances\n';
            csvContent += 'Date,' + activities.join(',') + '\n';
            
            data.trends.forEach(trend => {
                csvContent += `"${trend.date}"`;
                
                activities.forEach(activity => {
                    csvContent += `,${trend.activities[activity] || 0}`;
                });
                
                csvContent += '\n';
            }); 
        }
        
        // Télécharger le fichier CSV
        this.downloadFile(
            csvContent, 
            `statistiques_${period}_${new Date().toISOString().slice(0, 10)}.csv`, 
            'text/csv;charset=utf-8;'
        );
    },
    
    /**
     * Exporte les données en JSON
     * @param {Object} data - Données à exporter
     * @param {string} period - Période des données ('day', 'week', 'month', 'year')
     */
    exportJSON: function(data, period) {
        const jsonString = JSON.stringify(data, null, 2);
        
        // Télécharger le fichier JSON
        this.downloadFile(
            jsonString, 
            `statistiques_${period}_${new Date().toISOString().slice(0, 10)}.json`, 
            'application/json'
        );
    },
    
    /**
     * Exporte les données en PDF (simulation)
     * @param {Object} data - Données à exporter
     * @param {string} period - Période des données ('day', 'week', 'month', 'year')
     */
    exportPDF: function(data, period) {
        // Dans une vraie application, on utiliserait une bibliothèque comme jsPDF
        // Pour cet exemple, on affiche simplement un message
        if (window.Utils && Utils.showError) {
            Utils.showError('Génération de PDF en cours...', 2000);
            
            setTimeout(() => {
                Utils.showError('La fonctionnalité d\'export PDF sera disponible dans une prochaine mise à jour.', 5000);
            }, 2000);
        } else {
            alert('La fonctionnalité d\'export PDF sera disponible dans une prochaine mise à jour.');
        }
    },
    
    /**
     * Télécharge un fichier avec le contenu spécifié
     * @param {string} content - Contenu du fichier
     * @param {string} filename - Nom du fichier
     * @param {string} contentType - Type MIME du contenu
     */
    downloadFile: function(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Libérer l'URL
        setTimeout(() => {
            URL.revokeObjectURL(url);
        }, 100);
    }
};

// Exporter le module
window.ExportManager = ExportManager;
