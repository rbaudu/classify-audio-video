/**
 * Module de classification
 * Gère l'analyse des données et la classification des activités
 */

const Classification = {
    // État de la classification
    state: {
        classificationInterval: null,
        autoUpdate: false,
        lastClassification: null,
        videoFeatures: {
            motion: 0,
            skin: 0,
            brightness: 0
        },
        audioFeatures: {
            level: 0,
            dominantFreq: 0,
            speechDetected: false
        }
    },

    /**
     * Initialise le module de classification
     */
    init: function() {
        // Initialiser le bouton de classification
        const runClassificationButton = document.getElementById('run-classification');
        if (runClassificationButton) {
            runClassificationButton.addEventListener('click', () => {
                this.classify();
            });
        }
        
        // Initialiser la case à cocher de mise à jour automatique
        const autoUpdateCheckbox = document.getElementById('auto-update');
        if (autoUpdateCheckbox) {
            autoUpdateCheckbox.addEventListener('change', (e) => {
                this.toggleAutoUpdate(e.target.checked);
            });
        }
    },

    /**
     * Active/désactive la mise à jour automatique de la classification
     * @param {boolean} enabled - État de la mise à jour automatique
     */
    toggleAutoUpdate: function(enabled) {
        this.state.autoUpdate = enabled;
        
        if (this.state.classificationInterval) {
            clearInterval(this.state.classificationInterval);
            this.state.classificationInterval = null;
        }
        
        if (enabled) {
            // Effectuer une classification immédiatement
            this.classify();
            
            // Configurer l'intervalle pour des classifications périodiques
            this.state.classificationInterval = setInterval(() => {
                this.classify();
            }, 5000); // Toutes les 5 secondes
        }
    },
    
    /**
     * Effectue une classification sur les données actuelles
     */
    classify: function() {
        console.log('Classification en cours...');
        
        // Simuler l'extraction de caractéristiques
        this.simulateVideoFeatures();
        this.simulateAudioFeatures();
        
        // Mettre à jour l'affichage des caractéristiques
        this.updateFeaturesDisplay();
        
        // Simuler la classification
        const activities = {
            'Travail sur ordinateur': 0.75,
            'Conversation': 0.15,
            'Pause café': 0.05,
            'Réunion': 0.03,
            'Inactif': 0.02
        };
        
        // Mettre à jour l'affichage du résultat
        this.updateClassificationResult(activities);
        
        console.log('Classification terminée');
    },
    
    /**
     * Simule l'extraction de caractéristiques vidéo
     */
    simulateVideoFeatures: function() {
        // Dans une implémentation réelle, ces valeurs seraient extraites de l'analyse du flux vidéo
        this.state.videoFeatures = {
            motion: Math.random() * 100,
            skin: Math.random() * 100,
            brightness: Math.random() * 255
        };
    },
    
    /**
     * Simule l'extraction de caractéristiques audio
     */
    simulateAudioFeatures: function() {
        // Dans une implémentation réelle, ces valeurs seraient extraites de l'analyse du flux audio
        // Ou récupérées depuis le module AudioVisualizer
        if (window.AudioVisualizer) {
            this.state.audioFeatures = window.AudioVisualizer.generateFeatures();
        } else {
            this.state.audioFeatures = {
                level: Math.random() * 100,
                dominantFreq: Math.random() * 2000 + 200,
                speechDetected: Math.random() > 0.5
            };
        }
    },
    
    /**
     * Met à jour l'affichage des caractéristiques
     */
    updateFeaturesDisplay: function() {
        // Mettre à jour les caractéristiques vidéo
        document.getElementById('motion-value')?.textContent = `${Math.round(this.state.videoFeatures.motion)}%`;
        document.getElementById('skin-value')?.textContent = `${Math.round(this.state.videoFeatures.skin)}%`;
        document.getElementById('brightness-value')?.textContent = Math.round(this.state.videoFeatures.brightness);
        
        // Mettre à jour les caractéristiques audio
        document.getElementById('audio-level-value')?.textContent = Math.round(this.state.audioFeatures.level);
        document.getElementById('dominant-freq-value')?.textContent = `${Math.round(this.state.audioFeatures.dominantFreq)} Hz`;
        document.getElementById('speech-detected-value')?.textContent = this.state.audioFeatures.speechDetected ? 'Oui' : 'Non';
    },
    
    /**
     * Met à jour l'affichage du résultat de classification
     * @param {Object} activities - Objet avec les activités et leurs scores de confiance
     */
    updateClassificationResult: function(activities) {
        const detectedActivity = document.getElementById('detected-activity');
        const confidenceBars = document.getElementById('confidence-bars');
        
        if (!detectedActivity || !confidenceBars) return;
        
        // Trouver l'activité avec le score le plus élevé
        let topActivity = '';
        let topScore = 0;
        
        Object.entries(activities).forEach(([activity, score]) => {
            if (score > topScore) {
                topActivity = activity;
                topScore = score;
            }
        });
        
        // Mettre à jour l'activité détectée
        detectedActivity.textContent = topActivity;
        
        // Générer les barres de confiance
        confidenceBars.innerHTML = '';
        
        // Trier les activités par score décroissant
        const sortedActivities = Object.entries(activities)
            .sort((a, b) => b[1] - a[1]);
        
        sortedActivities.forEach(([activity, score]) => {
            const percentage = Math.round(score * 100);
            
            const barContainer = document.createElement('div');
            barContainer.className = 'confidence-bar-container';
            
            const label = document.createElement('div');
            label.className = 'confidence-label';
            label.textContent = activity;
            
            const barWrapper = document.createElement('div');
            barWrapper.className = 'confidence-bar-wrapper';
            
            const bar = document.createElement('div');
            bar.className = 'confidence-bar';
            bar.style.width = `${percentage}%`;
            
            const value = document.createElement('div');
            value.className = 'confidence-value';
            value.textContent = `${percentage}%`;
            
            barWrapper.appendChild(bar);
            barContainer.appendChild(label);
            barContainer.appendChild(barWrapper);
            barContainer.appendChild(value);
            
            confidenceBars.appendChild(barContainer);
        });
    },
    
    /**
     * Nettoie les ressources du module
     */
    stop: function() {
        if (this.state.classificationInterval) {
            clearInterval(this.state.classificationInterval);
            this.state.classificationInterval = null;
        }
    }
};

// Exporter le module
window.Classification = Classification;
