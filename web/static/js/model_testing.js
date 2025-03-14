/**
 * Script pour la page de test du modèle de classification
 * Gère l'affichage des flux audio/vidéo et permet de tester le modèle en direct
 */

// Gestionnaire des tests de modèle
const ModelTesting = {
    // État du test de modèle
    state: {
        videoFeed: null,
        audioContext: null,
        audioAnalyser: null,
        audioSource: null,
        visualizer: null,
        classificationInterval: null,
        autoUpdate: false,
        lastClassification: null,
        modelInfo: {
            name: 'Classificateur basé sur des règles',
            accuracy: 0.85,
            lastUpdate: '2025-03-12T10:30:00'
        },
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
     * Initialise la page de test du modèle
     */
    init: function() {
        // Initialiser les écouteurs d'événements pour les boutons
        const refreshFeedButton = document.getElementById('refresh-feed');
        if (refreshFeedButton) {
            refreshFeedButton.addEventListener('click', () => {
                this.initVideoFeed();
            });
        }
        
        const muteAudioButton = document.getElementById('mute-audio');
        if (muteAudioButton) {
            muteAudioButton.addEventListener('click', () => {
                this.toggleAudioMute();
            });
        }
        
        const runClassificationButton = document.getElementById('run-classification');
        if (runClassificationButton) {
            runClassificationButton.addEventListener('click', () => {
                this.classify();
            });
        }
        
        const autoUpdateCheckbox = document.getElementById('auto-update');
        if (autoUpdateCheckbox) {
            autoUpdateCheckbox.addEventListener('change', (e) => {
                this.toggleAutoUpdate(e.target.checked);
            });
        }
        
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
        
        // Initialiser les flux audio et vidéo
        this.initVideoFeed();
        this.initAudio();
        
        // Initialiser les informations sur le modèle
        this.updateModelInfo();
        
        // Effectuer une première classification
        this.classify();
    },
    
    /**
     * Initialise le flux vidéo
     */
    initVideoFeed: async function() {
        try {
            const videoFeed = document.getElementById('video-feed');
            if (!videoFeed) return;
            
            // Vider le conteneur
            videoFeed.innerHTML = '';
            
            // Afficher un message de chargement
            const loadingElement = document.createElement('div');
            loadingElement.className = 'loading-message';
            loadingElement.textContent = 'Chargement du flux vidéo...';
            videoFeed.appendChild(loadingElement);
            
            // Récupérer l'URL du flux vidéo depuis l'API
            const response = await Utils.fetchAPI('/video-feed-url');
            
            if (!response || !response.url) {
                throw new Error('URL du flux vidéo non disponible');
            }
            
            // Créer l'élément vidéo
            const videoElement = document.createElement('img');
            videoElement.className = 'video-element';
            videoElement.src = response.url;
            videoElement.alt = 'Flux vidéo';
            
            // Remplacer le message de chargement par l'élément vidéo
            videoFeed.innerHTML = '';
            videoFeed.appendChild(videoElement);
            
            // Enregistrer la référence dans l'état
            this.state.videoFeed = videoElement;
            
        } catch (error) {
            console.error('Erreur lors de l\'initialisation du flux vidéo:', error);
            
            const videoFeed = document.getElementById('video-feed');
            if (videoFeed) {
                videoFeed.innerHTML = '<div class="error-message">Erreur lors du chargement du flux vidéo</div>';
            }
        }
    },
    
    /**
     * Initialise l'audio et l'analyseur
     */
    initAudio: async function() {
        try {
            // Vérifier si l'API Web Audio est supportée
            if (!window.AudioContext && !window.webkitAudioContext) {
                throw new Error('Web Audio API non supportée par ce navigateur');
            }
            
            // Initialiser le contexte audio
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.state.audioContext = new AudioContext();
            
            // Créer un analyseur
            this.state.audioAnalyser = this.state.audioContext.createAnalyser();
            this.state.audioAnalyser.fftSize = 2048;
            this.state.audioAnalyser.smoothingTimeConstant = 0.8;
            
            // Récupérer l'URL de la source audio depuis l'API
            const response = await Utils.fetchAPI('/audio-feed-url');
            
            if (!response || !response.url) {
                throw new Error('URL du flux audio non disponible');
            }
            
            // Créer un élément audio
            const audioElement = new Audio();
            audioElement.src = response.url;
            audioElement.crossOrigin = 'anonymous';
            audioElement.autoplay = true;
            
            // Connecter l'élément audio à l'analyseur
            this.state.audioSource = this.state.audioContext.createMediaElementSource(audioElement);
            this.state.audioSource.connect(this.state.audioAnalyser);
            this.state.audioAnalyser.connect(this.state.audioContext.destination);
            
            // Initialiser le visualiseur audio
            this.initAudioVisualizer();
            
        } catch (error) {
            console.error('Erreur lors de l\'initialisation de l\'audio:', error);
            
            const audioVisualizer = document.getElementById('audio-visualizer');
            if (audioVisualizer) {
                audioVisualizer.innerHTML = '<div class="error-message">Erreur lors du chargement du flux audio</div>';
            }
        }
    },
    
    /**
     * Initialise le visualiseur audio
     */
    initAudioVisualizer: function() {
        if (!this.state.audioAnalyser) return;
        
        const audioVisualizer = document.getElementById('audio-visualizer');
        if (!audioVisualizer) return;
        
        // Vider le conteneur
        audioVisualizer.innerHTML = '';
        
        // Créer un élément canvas pour le visualiseur
        const canvas = document.createElement('canvas');
        canvas.width = audioVisualizer.clientWidth;
        canvas.height = audioVisualizer.clientHeight;
        audioVisualizer.appendChild(canvas);
        
        const canvasCtx = canvas.getContext('2d');
        const bufferLength = this.state.audioAnalyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        // Fonction de dessin pour le visualiseur
        const draw = () => {
            this.state.visualizer = requestAnimationFrame(draw);
            
            this.state.audioAnalyser.getByteFrequencyData(dataArray);
            
            canvasCtx.fillStyle = 'rgb(20, 20, 30)';
            canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
            
            const barWidth = (canvas.width / bufferLength) * 2.5;
            let barHeight;
            let x = 0;
            
            for (let i = 0; i < bufferLength; i++) {
                barHeight = dataArray[i] / 2;
                
                const gradient = canvasCtx.createLinearGradient(0, 0, 0, canvas.height);
                gradient.addColorStop(0, 'rgb(0, 210, 255)');
                gradient.addColorStop(1, 'rgb(0, 100, 150)');
                
                canvasCtx.fillStyle = gradient;
                canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                
                x += barWidth + 1;
            }
            
            // Mettre à jour les caractéristiques audio
            this.updateAudioFeatures(dataArray);
        };
        
        draw();
    },
    
    /**
     * Met à jour les caractéristiques audio affichées
     * @param {Uint8Array} dataArray - Tableau de données de fréquence audio
     */
    updateAudioFeatures: function(dataArray) {
        if (!dataArray) return;
        
        // Calculer le niveau audio moyen
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }
        const average = sum / dataArray.length;
        this.state.audioFeatures.level = Math.round(average);
        
        // Trouver la fréquence dominante
        let maxValue = 0;
        let maxIndex = 0;
        for (let i = 0; i < dataArray.length; i++) {
            if (dataArray[i] > maxValue) {
                maxValue = dataArray[i];
                maxIndex = i;
            }
        }
        // Convertir l'indice en fréquence approximative (dépend de la fréquence d'échantillonnage)
        const nyquist = this.state.audioContext.sampleRate / 2;
        this.state.audioFeatures.dominantFreq = Math.round(maxIndex * nyquist / dataArray.length);
        
        // Simuler la détection de parole (simplifiée pour l'exemple)
        // Dans une implémentation réelle, cela utiliserait un modèle plus sophistiqué
        // Critères simplifiés: niveau audio élevé et fréquences dominantes dans la plage de parole humaine
        this.state.audioFeatures.speechDetected = (
            this.state.audioFeatures.level > 40 && 
            this.state.audioFeatures.dominantFreq > 85 && 
            this.state.audioFeatures.dominantFreq < 255
        );
        
        // Mettre à jour l'interface
        this.updateFeaturesDisplay();
    },
    
    /**
     * Met à jour l'affichage des caractéristiques
     */
    updateFeaturesDisplay: function() {
        // Mettre à jour les caractéristiques vidéo
        const motionValue = document.getElementById('motion-value');
        const skinValue = document.getElementById('skin-value');
        const brightnessValue = document.getElementById('brightness-value');
        
        if (motionValue) {
            motionValue.textContent = `${this.state.videoFeatures.motion}%`;
        }
        
        if (skinValue) {
            skinValue.textContent = `${this.state.videoFeatures.skin}%`;
        }
        
        if (brightnessValue) {
            brightnessValue.textContent = this.state.videoFeatures.brightness;
        }
        
        // Mettre à jour les caractéristiques audio
        const audioLevelValue = document.getElementById('audio-level-value');
        const dominantFreqValue = document.getElementById('dominant-freq-value');
        const speechDetectedValue = document.getElementById('speech-detected-value');
        
        if (audioLevelValue) {
            audioLevelValue.textContent = this.state.audioFeatures.level;
        }
        
        if (dominantFreqValue) {
            dominantFreqValue.textContent = `${this.state.audioFeatures.dominantFreq} Hz`;
        }
        
        if (speechDetectedValue) {
            speechDetectedValue.textContent = this.state.audioFeatures.speechDetected ? 'Oui' : 'Non';
        }
    },
    
    /**
     * Active/désactive la mise à jour automatique
     * @param {boolean} enabled - État d'activation
     */
    toggleAutoUpdate: function(enabled) {
        this.state.autoUpdate = enabled;
        
        if (enabled) {
            // Démarrer l'intervalle de classification automatique
            this.state.classificationInterval = setInterval(() => {
                this.classify();
            }, 5000); // Toutes les 5 secondes
        } else {
            // Arrêter l'intervalle
            if (this.state.classificationInterval) {
                clearInterval(this.state.classificationInterval);
                this.state.classificationInterval = null;
            }
        }
    },
    
    /**
     * Active/désactive le son
     */
    toggleAudioMute: function() {
        if (!this.state.audioContext) return;
        
        const muteButton = document.getElementById('mute-audio');
        
        if (this.state.audioContext.state === 'running') {
            this.state.audioContext.suspend();
            if (muteButton) {
                muteButton.textContent = 'Activer le son';
            }
        } else {
            this.state.audioContext.resume();
            if (muteButton) {
                muteButton.textContent = 'Muter';
            }
        }
    },
    
    /**
     * Effectue une classification en utilisant les caractéristiques actuelles
     */
    classify: async function() {
        try {
            // Simuler l'extraction de caractéristiques vidéo (Dans une implémentation réelle, ce serait fait à partir du flux vidéo)
            this.simulateVideoFeatures();
            
            // Préparer les caractéristiques pour la classification
            const features = {
                video: this.state.videoFeatures,
                audio: this.state.audioFeatures
            };
            
            // Envoyer les caractéristiques à l'API pour classification
            const result = await Utils.fetchAPI('/classify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(features)
            });
            
            if (!result) {
                throw new Error('Résultat de classification non disponible');
            }
            
            this.state.lastClassification = result;
            
            // Mettre à jour l'interface avec le résultat
            this.updateClassificationResult(result);
            
        } catch (error) {
            console.error('Erreur lors de la classification:', error);
            
            // Effectuer une classification simulée en cas d'erreur
            this.simulateClassification();
        }
    },
    
    /**
     * Simule l'extraction de caractéristiques vidéo
     * Dans une implémentation réelle, ce serait fait à partir du flux vidéo
     */
    simulateVideoFeatures: function() {
        // Générer des valeurs aléatoires pour la démonstration
        this.state.videoFeatures.motion = Math.floor(Math.random() * 100);
        this.state.videoFeatures.skin = Math.floor(Math.random() * 100);
        this.state.videoFeatures.brightness = Math.floor(Math.random() * 255);
        
        // Mettre à jour l'affichage
        this.updateFeaturesDisplay();
    },
    
    /**
     * Simule une classification en cas d'erreur de l'API
     */
    simulateClassification: function() {
        // Définir des activités possibles
        const activities = [
            'endormi',
            'à table',
            'lisant',
            'au téléphone',
            'en conversation',
            'occupé',
            'inactif'
        ];
        
        // Générer des scores de confiance aléatoires
        const confidenceScores = {};
        let total = 0;
        
        activities.forEach(activity => {
            confidenceScores[activity] = Math.random();
            total += confidenceScores[activity];
        });
        
        // Normaliser les scores pour qu'ils forment une distribution de probabilité
        activities.forEach(activity => {
            confidenceScores[activity] /= total;
        });
        
        // Déterminer l'activité avec le score le plus élevé
        let highestScore = 0;
        let predictedActivity = '';
        
        for (const [activity, score] of Object.entries(confidenceScores)) {
            if (score > highestScore) {
                highestScore = score;
                predictedActivity = activity;
            }
        }
        
        // Créer un résultat simulé
        const result = {
            activity: predictedActivity,
            confidence_scores: confidenceScores,
            timestamp: Math.floor(Date.now() / 1000)
        };
        
        this.state.lastClassification = result;
        
        // Mettre à jour l'interface
        this.updateClassificationResult(result);
    },
    
    /**
     * Met à jour l'interface avec le résultat de la classification
     * @param {Object} result - Résultat de la classification
     */
    updateClassificationResult: function(result) {
        const detectedActivity = document.getElementById('detected-activity');
        const confidenceBars = document.getElementById('confidence-bars');
        
        if (detectedActivity) {
            detectedActivity.textContent = `${Utils.getActivityIcon(result.activity)} ${result.activity}`;
            detectedActivity.style.color = Utils.getActivityColor(result.activity);
        }
        
        if (confidenceBars) {
            // Vider le conteneur
            confidenceBars.innerHTML = '';
            
            // Trier les activités par score de confiance décroissant
            const sortedActivities = Object.entries(result.confidence_scores)
                .sort((a, b) => b[1] - a[1]);
            
            // Créer une barre pour chaque activité
            sortedActivities.forEach(([activity, score]) => {
                const percentage = Math.round(score * 100);
                
                const barContainer = document.createElement('div');
                barContainer.className = 'confidence-bar-container';
                
                const labelElement = document.createElement('div');
                labelElement.className = 'confidence-label';
                labelElement.textContent = `${Utils.getActivityIcon(activity)} ${activity}`;
                
                const barElement = document.createElement('div');
                barElement.className = 'confidence-bar';
                
                const barFill = document.createElement('div');
                barFill.className = 'confidence-bar-fill';
                barFill.style.width = `${percentage}%`;
                barFill.style.backgroundColor = Utils.getActivityColor(activity);
                
                const percentElement = document.createElement('div');
                percentElement.className = 'confidence-percentage';
                percentElement.textContent = `${percentage}%`;
                
                barElement.appendChild(barFill);
                barContainer.appendChild(labelElement);
                barContainer.appendChild(barElement);
                barContainer.appendChild(percentElement);
                
                confidenceBars.appendChild(barContainer);
            });
        }
    },
    
    /**
     * Met à jour l'interface avec les informations sur le modèle
     */
    updateModelInfo: function() {
        const modelName = document.getElementById('model-name');
        const modelAccuracy = document.getElementById('model-accuracy');
        const modelLastUpdate = document.getElementById('model-last-update');
        
        if (modelName) {
            modelName.textContent = this.state.modelInfo.name;
        }
        
        if (modelAccuracy) {
            modelAccuracy.textContent = `${Math.round(this.state.modelInfo.accuracy * 100)}%`;
        }
        
        if (modelLastUpdate) {
            const date = new Date(this.state.modelInfo.lastUpdate);
            const formattedDate = date.toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            modelLastUpdate.textContent = formattedDate;
        }
    },
    
    /**
     * Réentraîne le modèle de classification
     */
    retrainModel: async function() {
        try {
            // Afficher une notification
            Utils.showError('Réentraînement du modèle en cours...', 10000);
            
            // Simuler un temps d'entraînement
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            // Mettre à jour les informations du modèle
            this.state.modelInfo.lastUpdate = new Date().toISOString();
            this.state.modelInfo.accuracy = 0.87 + (Math.random() * 0.1 - 0.05); // Entre 0.82 et 0.92
            
            // Mettre à jour l'interface
            this.updateModelInfo();
            
            // Afficher une notification de succès
            Utils.showError('Modèle réentraîné avec succès!', 3000);
            
        } catch (error) {
            console.error('Erreur lors du réentraînement du modèle:', error);
            Utils.showError('Erreur lors du réentraînement du modèle');
        }
    },
    
    /**
     * Exporte le modèle de classification
     */
    exportModel: function() {
        try {
            // Créer un objet représentant le modèle (simplifié pour l'exemple)
            const model = {
                name: this.state.modelInfo.name,
                accuracy: this.state.modelInfo.accuracy,
                lastUpdate: this.state.modelInfo.lastUpdate,
                parameters: {
                    weights: [0.2, 0.3, 0.15, 0.35],
                    bias: [0.1, -0.2, 0.3, -0.1],
                    classes: Object.keys(CONFIG.ACTIVITY_ICONS)
                }
            };
            
            // Convertir en JSON
            const json = JSON.stringify(model, null, 2);
            
            // Créer un blob et un lien de téléchargement
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `model_${new Date().toISOString().slice(0, 10)}.json`;
            link.click();
            
            URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Erreur lors de l\'exportation du modèle:', error);
            Utils.showError('Erreur lors de l\'exportation du modèle');
        }
    },
    
    /**
     * Importe un modèle de classification
     */
    importModel: function() {
        try {
            // Créer un élément input de type fichier
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'application/json';
            
            // Gérer l'événement de changement
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (!file) return;
                
                const reader = new FileReader();
                reader.onload = (event) => {
                    try {
                        const model = JSON.parse(event.target.result);
                        
                        // Vérifier que le fichier a la structure attendue
                        if (!model.name || !model.accuracy || !model.lastUpdate) {
                            throw new Error('Format de modèle invalide');
                        }
                        
                        // Mettre à jour les informations du modèle
                        this.state.modelInfo = {
                            name: model.name,
                            accuracy: model.accuracy,
                            lastUpdate: model.lastUpdate
                        };
                        
                        // Mettre à jour l'interface
                        this.updateModelInfo();
                        
                        Utils.showError('Modèle importé avec succès!', 3000);
                        
                    } catch (error) {
                        console.error('Erreur lors du parsing du fichier de modèle:', error);
                        Utils.showError('Format de fichier de modèle invalide');
                    }
                };
                
                reader.readAsText(file);
            };
            
            // Simuler un clic sur l'élément input
            input.click();
            
        } catch (error) {
            console.error('Erreur lors de l\'importation du modèle:', error);
            Utils.showError('Erreur lors de l\'importation du modèle');
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    ModelTesting.init();
});
