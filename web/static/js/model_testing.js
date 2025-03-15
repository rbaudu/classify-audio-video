/**
 * Script pour la page de test du modèle de classification
 * Gère l'affichage des flux audio/vidéo et permet de tester le modèle en direct
 * Prend également en charge les fichiers vidéo pour analyse
 */

// Gestionnaire des tests de modèle
const ModelTesting = {
    // État du test de modèle
    state: {
        // Flux en direct
        videoFeed: null,
        audioContext: null,
        audioAnalyser: null,
        audioSource: null,
        visualizer: null,
        classificationInterval: null,
        autoUpdate: false,
        lastClassification: null,
        
        // Informations sur le modèle
        modelInfo: {
            name: 'Classificateur basé sur des règles',
            accuracy: 0.85,
            lastUpdate: '2025-03-12T10:30:00'
        },
        
        // Caractéristiques extraites
        videoFeatures: {
            motion: 0,
            skin: 0,
            brightness: 0
        },
        audioFeatures: {
            level: 0,
            dominantFreq: 0,
            speechDetected: false
        },
        
        // Fichiers vidéo
        mediaSources: [],
        currentMediaSource: null,
        mediaUpdateInterval: null,
        mediaProperties: {
            duration: 0,
            currentTime: 0,
            isPlaying: false
        }
    },
    
    /**
     * Initialise la page de test du modèle
     */
    init: function() {
        // Initialiser les écouteurs d'événements pour les onglets
        this.initTabs();
        
        // Initialiser les écouteurs d'événements pour le flux en direct
        this.initLiveStreamTab();
        
        // Initialiser les écouteurs d'événements pour les fichiers vidéo
        this.initVideoFileTab();
        
        // Effectuer une première classification
        this.classify();
    },
    
    /**
     * Initialise les onglets
     */
    initTabs: function() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        if (tabButtons.length && tabContents.length) {
            tabButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const tabName = button.getAttribute('data-tab');
                    
                    // Masquer tous les contenus d'onglet
                    tabContents.forEach(content => {
                        content.classList.remove('active');
                    });
                    
                    // Désactiver tous les boutons d'onglet
                    tabButtons.forEach(btn => {
                        btn.classList.remove('active');
                    });
                    
                    // Activer l'onglet sélectionné
                    button.classList.add('active');
                    document.getElementById(tabName).classList.add('active');
                    
                    // Arrêter les mises à jour automatiques de l'onglet précédent
                    this.stopAllIntervals();
                    
                    // Initialiser l'onglet sélectionné
                    if (tabName === 'live-stream') {
                        this.initVideoFeed();
                        this.initAudio();
                    } else if (tabName === 'video-file') {
                        this.loadMediaSources();
                        this.startMediaTimeUpdate();
                    }
                });
            });
        }
    },
    
    /**
     * Arrête tous les intervalles de mise à jour
     */
    stopAllIntervals: function() {
        // Arrêter l'intervalle de classification
        if (this.state.classificationInterval) {
            clearInterval(this.state.classificationInterval);
            this.state.classificationInterval = null;
        }
        
        // Arrêter l'intervalle de mise à jour du média
        if (this.state.mediaUpdateInterval) {
            clearInterval(this.state.mediaUpdateInterval);
            this.state.mediaUpdateInterval = null;
        }
        
        // Arrêter le visualiseur audio
        if (this.state.visualizer) {
            cancelAnimationFrame(this.state.visualizer);
            this.state.visualizer = null;
        }
    },
    
    /**
     * Initialise l'onglet de flux en direct
     */
    initLiveStreamTab: function() {
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
    },
    
    /**
     * Initialise l'onglet des fichiers vidéo
     */
    initVideoFileTab: function() {
        // Initialiser les écouteurs d'événements pour les boutons de sources média
        const refreshSourcesButton = document.getElementById('refresh-sources');
        if (refreshSourcesButton) {
            refreshSourcesButton.addEventListener('click', () => {
                this.loadMediaSources();
            });
        }
        
        const mediaSourceSelect = document.getElementById('media-source-select');
        if (mediaSourceSelect) {
            mediaSourceSelect.addEventListener('change', (e) => {
                this.selectMediaSource(e.target.value);
            });
        }
        
        // Initialiser les écouteurs d'événements pour les contrôles média
        const mediaPlayButton = document.getElementById('media-play');
        const mediaPauseButton = document.getElementById('media-pause');
        const mediaRestartButton = document.getElementById('media-restart');
        const mediaProgressBar = document.getElementById('media-progress-bar');
        
        if (mediaPlayButton) {
            mediaPlayButton.addEventListener('click', () => {
                this.controlMedia('play');
            });
        }
        
        if (mediaPauseButton) {
            mediaPauseButton.addEventListener('click', () => {
                this.controlMedia('pause');
            });
        }
        
        if (mediaRestartButton) {
            mediaRestartButton.addEventListener('click', () => {
                this.controlMedia('restart');
            });
        }
        
        if (mediaProgressBar) {
            mediaProgressBar.addEventListener('input', (e) => {
                this.seekMedia(e.target.value);
            });
        }
        
        // Initialiser les écouteurs d'événements pour les boutons d'analyse
        const analyzeVideoButton = document.getElementById('analyze-video');
        if (analyzeVideoButton) {
            analyzeVideoButton.addEventListener('click', () => {
                this.analyzeFullVideo();
            });
        }
        
        const singleFrameAnalysisButton = document.getElementById('single-frame-analysis');
        if (singleFrameAnalysisButton) {
            singleFrameAnalysisButton.addEventListener('click', () => {
                this.analyzeSingleFrame();
            });
        }
        
        // Charger les sources média disponibles
        this.loadMediaSources();
        
        // Charger les analyses précédentes
        this.loadPreviousAnalyses();
    },
    
    // [Le reste du code pour le flux en direct reste inchangé...]
    
    /**
     * Charge la liste des sources média disponibles
     */
    loadMediaSources: async function() {
        try {
            const mediaSourceSelect = document.getElementById('media-source-select');
            const mediaInfo = document.getElementById('media-info');
            
            if (!mediaSourceSelect || !mediaInfo) return;
            
            // Afficher un message de chargement
            mediaInfo.innerHTML = '<p>Chargement des sources média...</p>';
            
            // Vider le sélecteur (sauf l'option par défaut)
            while (mediaSourceSelect.options.length > 1) {
                mediaSourceSelect.remove(1);
            }
            
            // Récupérer la liste des sources média depuis l'API
            const sources = await Utils.fetchAPI('/media-sources');
            
            if (!sources || !Array.isArray(sources) || sources.length === 0) {
                mediaInfo.innerHTML = '<p>Aucune source média disponible.</p><p>Ajoutez des fichiers vidéo à OBS et assurez-vous qu\'ils sont correctement configurés.</p>';
                return;
            }
            
            // Mettre à jour l'état
            this.state.mediaSources = sources;
            
            // Ajouter les options au sélecteur
            sources.forEach(source => {
                const option = document.createElement('option');
                option.value = source.name;
                option.textContent = source.name;
                mediaSourceSelect.appendChild(option);
            });
            
            // Afficher un message informatif
            mediaInfo.innerHTML = `<p>${sources.length} source(s) média disponible(s).</p><p>Sélectionnez une source pour commencer l'analyse.</p>`;
            
        } catch (error) {
            console.error('Erreur lors du chargement des sources média:', error);
            
            const mediaInfo = document.getElementById('media-info');
            if (mediaInfo) {
                mediaInfo.innerHTML = '<p class="error-text">Erreur lors du chargement des sources média. Vérifiez la connexion à OBS.</p>';
            }
        }
    },
    
    /**
     * Sélectionne une source média
     * @param {string} sourceName - Nom de la source média
     */
    selectMediaSource: async function(sourceName) {
        try {
            if (!sourceName) return;
            
            const mediaInfo = document.getElementById('media-info');
            const mediaPreview = document.getElementById('media-preview');
            
            // Afficher un message de chargement
            if (mediaInfo) {
                mediaInfo.innerHTML = '<p>Chargement des informations...</p>';
            }
            
            if (mediaPreview) {
                mediaPreview.innerHTML = '<div class="loading-message">Chargement du média...</div>';
            }
            
            // Sélectionner la source via l'API
            const response = await Utils.fetchAPI('/select-media-source', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ sourceName })
            });
            
            if (!response || !response.success) {
                throw new Error('Erreur lors de la sélection de la source');
            }
            
            // Récupérer les propriétés de la source
            const properties = await Utils.fetchAPI(`/media-properties/${sourceName}`);
            
            if (!properties) {
                throw new Error('Impossible de récupérer les propriétés');
            }
            
            // Mettre à jour l'état
            this.state.currentMediaSource = sourceName;
            this.state.mediaProperties = {
                duration: properties.duration || 0,
                currentTime: properties.position || 0,
                isPlaying: properties.playing || false
            };
            
            // Mettre à jour l'interface
            this.updateMediaInterface();
            
            // Démarrer la mise à jour du temps
            this.startMediaTimeUpdate();
            
        } catch (error) {
            console.error('Erreur lors de la sélection de la source média:', error);
            
            const mediaInfo = document.getElementById('media-info');
            if (mediaInfo) {
                mediaInfo.innerHTML = `<p class="error-text">Erreur lors de la sélection de la source: ${error.message}</p>`;
            }
        }
    },
    
    /**
     * Met à jour l'interface avec les informations du média sélectionné
     */
    updateMediaInterface: function() {
        const mediaInfo = document.getElementById('media-info');
        const mediaPreview = document.getElementById('media-preview');
        const mediaProgressBar = document.getElementById('media-progress-bar');
        const currentTime = document.getElementById('current-time');
        const totalTime = document.getElementById('total-time');
        
        // Mettre à jour les informations du média
        if (mediaInfo) {
            const sourceInfo = this.state.mediaSources.find(s => s.name === this.state.currentMediaSource);
            
            if (sourceInfo) {
                let infoHTML = `<p><strong>Source:</strong> ${this.state.currentMediaSource}</p>`;
                
                if (this.state.mediaProperties.duration) {
                    infoHTML += `<p><strong>Durée:</strong> ${this.formatTime(this.state.mediaProperties.duration)}</p>`;
                }
                
                infoHTML += `<p><strong>État:</strong> ${this.state.mediaProperties.isPlaying ? 'En lecture' : 'En pause'}</p>`;
                
                mediaInfo.innerHTML = infoHTML;
            }
        }
        
        // Mettre à jour la prévisualisation du média
        if (mediaPreview) {
            // Dans une implémentation réelle, cela pourrait être une capture d'écran du média
            // Pour l'exemple, on affiche juste un message
            mediaPreview.innerHTML = `<div class="media-placeholder">Prévisualisation de "${this.state.currentMediaSource}"</div>`;
        }
        
        // Mettre à jour la barre de progression
        if (mediaProgressBar) {
            mediaProgressBar.max = this.state.mediaProperties.duration;
            mediaProgressBar.value = this.state.mediaProperties.currentTime;
            mediaProgressBar.disabled = !this.state.currentMediaSource;
        }
        
        // Mettre à jour l'affichage du temps
        if (currentTime) {
            currentTime.textContent = this.formatTime(this.state.mediaProperties.currentTime);
        }
        
        if (totalTime) {
            totalTime.textContent = this.formatTime(this.state.mediaProperties.duration);
        }
    },
    
    /**
     * Formate un temps en secondes en format MM:SS
     * @param {number} seconds - Temps en secondes
     * @returns {string} Temps formaté
     */
    formatTime: function(seconds) {
        if (!seconds && seconds !== 0) return '00:00';
        
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },
    
    /**
     * Démarre la mise à jour périodique du temps de lecture
     */
    startMediaTimeUpdate: function() {
        // Arrêter l'intervalle existant si nécessaire
        if (this.state.mediaUpdateInterval) {
            clearInterval(this.state.mediaUpdateInterval);
        }
        
        // Créer un nouvel intervalle
        this.state.mediaUpdateInterval = setInterval(() => {
            this.updateMediaTime();
        }, 1000); // Mise à jour toutes les secondes
    },
    
    /**
     * Met à jour le temps de lecture du média
     */
    updateMediaTime: async function() {
        if (!this.state.currentMediaSource) return;
        
        try {
            // Récupérer le temps actuel via l'API
            const timeInfo = await Utils.fetchAPI(`/media-time/${this.state.currentMediaSource}`);
            
            if (!timeInfo) return;
            
            // Mettre à jour l'état
            this.state.mediaProperties = {
                duration: timeInfo.totalTime || this.state.mediaProperties.duration,
                currentTime: timeInfo.currentTime || 0,
                isPlaying: timeInfo.isPlaying || false
            };
            
            // Mettre à jour l'interface
            const mediaProgressBar = document.getElementById('media-progress-bar');
            const currentTime = document.getElementById('current-time');
            
            if (mediaProgressBar && !mediaProgressBar.matches(':active')) {
                mediaProgressBar.value = this.state.mediaProperties.currentTime;
            }
            
            if (currentTime) {
                currentTime.textContent = this.formatTime(this.state.mediaProperties.currentTime);
            }
            
        } catch (error) {
            console.error('Erreur lors de la mise à jour du temps:', error);
        }
    },
    
    /**
     * Contrôle la lecture du média
     * @param {string} action - Action à effectuer ('play', 'pause', 'restart')
     */
    controlMedia: async function(action) {
        if (!this.state.currentMediaSource) {
            Utils.showError('Aucune source média sélectionnée');
            return;
        }
        
        try {
            // Envoyer la commande à l'API
            const response = await Utils.fetchAPI('/control-media', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sourceName: this.state.currentMediaSource,
                    action: action
                })
            });
            
            if (!response || !response.success) {
                throw new Error(`Erreur lors de l'action ${action}`);
            }
            
            // Mettre à jour l'état en fonction de l'action
            switch (action) {
                case 'play':
                    this.state.mediaProperties.isPlaying = true;
                    break;
                case 'pause':
                    this.state.mediaProperties.isPlaying = false;
                    break;
                case 'restart':
                    this.state.mediaProperties.isPlaying = true;
                    this.state.mediaProperties.currentTime = 0;
                    break;
            }
            
            // Mettre à jour l'interface
            this.updateMediaInterface();
            
        } catch (error) {
            console.error(`Erreur lors du contrôle du média (${action}):`, error);
            Utils.showError(`Erreur lors de l'action ${action}`);
        }
    },
    
    /**
     * Déplace la position de lecture
     * @param {number} position - Position en secondes
     */
    seekMedia: async function(position) {
        if (!this.state.currentMediaSource) return;
        
        try {
            // Envoyer la commande à l'API
            const response = await Utils.fetchAPI('/control-media', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sourceName: this.state.currentMediaSource,
                    action: 'seek',
                    position: parseFloat(position)
                })
            });
            
            if (!response || !response.success) {
                throw new Error('Erreur lors du déplacement');
            }
            
            // Mettre à jour l'état
            this.state.mediaProperties.currentTime = parseFloat(position);
            
            // Mettre à jour l'interface
            const currentTime = document.getElementById('current-time');
            if (currentTime) {
                currentTime.textContent = this.formatTime(this.state.mediaProperties.currentTime);
            }
            
        } catch (error) {
            console.error('Erreur lors du déplacement de la position:', error);
        }
    },
    
    /**
     * Analyse une seule image du média actuel
     */
    analyzeSingleFrame: async function() {
        if (!this.state.currentMediaSource) {
            Utils.showError('Aucune source média sélectionnée');
            return;
        }
        
        try {
            // Mettre en pause le média pour l'analyse
            await this.controlMedia('pause');
            
            // Simuler l'extraction de caractéristiques
            this.simulateVideoFeatures();
            
            // Effectuer la classification
            await this.classify();
            
            Utils.showError('Image analysée avec succès', 3000);
            
        } catch (error) {
            console.error('Erreur lors de l\'analyse d\'image:', error);
            Utils.showError('Erreur lors de l\'analyse d\'image');
        }
    },
    
    /**
     * Analyse la vidéo complète
     */
    analyzeFullVideo: async function() {
        if (!this.state.currentMediaSource) {
            Utils.showError('Aucune source média sélectionnée');
            return;
        }
        
        try {
            // Récupérer les options d'analyse
            const saveAnalysis = document.getElementById('save-analysis')?.checked || false;
            const generateTimeline = document.getElementById('generate-timeline')?.checked || false;
            const sampleInterval = parseInt(document.getElementById('sample-interval')?.value || '5');
            
            // Afficher un message de progression
            Utils.showError('Démarrage de l\'analyse complète...', 3000);
            
            // Envoyer la demande d'analyse à l'API
            const result = await Utils.fetchAPI('/analyze-full-video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sourceName: this.state.currentMediaSource,
                    saveAnalysis: saveAnalysis,
                    generateTimeline: generateTimeline,
                    sampleInterval: sampleInterval
                })
            });
            
            if (!result || !result.analysisId) {
                throw new Error('L\'analyse n\'a pas pu démarrer');
            }
            
            // Rediriger vers la page de résultats d'analyse ou de suivi de progression
            window.location.href = `/analysis-results/${result.analysisId}`;
            
        } catch (error) {
            console.error('Erreur lors du lancement de l\'analyse vidéo:', error);
            Utils.showError('Erreur lors du lancement de l\'analyse vidéo');
        }
    },
    
    /**
     * Charge les analyses précédentes
     */
    loadPreviousAnalyses: async function() {
        try {
            const previousAnalysesContainer = document.getElementById('previous-analyses');
            if (!previousAnalysesContainer) return;
            
            // Afficher un message de chargement
            previousAnalysesContainer.innerHTML = '<p>Chargement des analyses précédentes...</p>';
            
            // Récupérer les analyses précédentes
            // Note: Cette API n'est pas encore implémentée dans le serveur
            const analyses = await Utils.fetchAPI('/video-analyses?limit=5');
            
            if (!analyses || !Array.isArray(analyses) || analyses.length === 0) {
                previousAnalysesContainer.innerHTML = '<p>Aucune analyse précédente trouvée.</p>';
                return;
            }
            
            // Créer la liste des analyses
            let analysesHTML = '<ul class="analyses-list">';
            
            analyses.forEach(analysis => {
                const date = new Date(analysis.timestamp * 1000);
                const formattedDate = date.toLocaleString('fr-FR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                analysesHTML += `
                    <li class="analysis-item">
                        <div class="analysis-info">
                            <div class="analysis-name">${analysis.source_name}</div>
                            <div class="analysis-date">${formattedDate}</div>
                        </div>
                        <a href="/analysis-results/${analysis.id}" class="btn small">Voir</a>
                    </li>
                `;
            });
            
            analysesHTML += '</ul>';
            
            previousAnalysesContainer.innerHTML = analysesHTML;
            
        } catch (error) {
            console.error('Erreur lors du chargement des analyses précédentes:', error);
            
            const previousAnalysesContainer = document.getElementById('previous-analyses');
            if (previousAnalysesContainer) {
                previousAnalysesContainer.innerHTML = '<p class="error-text">Erreur lors du chargement des analyses précédentes.</p>';
            }
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    ModelTesting.init();
});
