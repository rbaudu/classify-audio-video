/**
 * Script principal pour la page de test du modèle de classification
 * Intègre les différents modules pour gérer l'affichage des flux audio/vidéo
 * et permettre de tester le modèle en direct
 */

// Gestionnaire des tests de modèle
const ModelTesting = {
    /**
     * Initialise la page de test du modèle
     */
    init: function() {
        console.log('Initialisation de la page de test du modèle...');
        
        // Initialiser les écouteurs d'événements pour les onglets
        this.initTabs();
        
        // Initialiser l'onglet par défaut (flux en direct)
        this.initLiveStreamTab();
        
        console.log('Initialisation terminée');
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
                    
                    // Arrêter les modules de l'onglet précédent
                    this.stopAllModules();
                    
                    // Initialiser l'onglet sélectionné
                    if (tabName === 'live-stream') {
                        this.initLiveStreamTab();
                    } else if (tabName === 'video-file') {
                        this.initVideoFileTab();
                    }
                });
            });
        }
    },
    
    /**
     * Arrête tous les modules
     */
    stopAllModules: function() {
        // Arrêter le module de flux vidéo
        if (window.VideoFeed) {
            window.VideoFeed.stop();
        }
        
        // Arrêter le module audio
        if (window.AudioVisualizer) {
            window.AudioVisualizer.stop();
        }
        
        // Arrêter le module de classification
        if (window.Classification) {
            window.Classification.stop();
        }
    },
    
    /**
     * Initialise l'onglet de flux en direct
     */
    initLiveStreamTab: function() {
        console.log('Initialisation de l\'onglet de flux en direct...');
        
        // Initialiser le flux vidéo
        if (window.VideoFeed) {
            window.VideoFeed.init();
        }
        
        // Initialiser l'audio
        if (window.AudioVisualizer) {
            window.AudioVisualizer.init();
        }
        
        // Initialiser la classification
        if (window.Classification) {
            window.Classification.init();
        }
        
        // Initialiser les informations du modèle
        if (window.ModelInfo) {
            window.ModelInfo.init();
        }
        
        // Configurer les écouteurs d'événements pour les boutons spécifiques
        const muteAudioButton = document.getElementById('mute-audio');
        if (muteAudioButton && window.AudioVisualizer) {
            muteAudioButton.addEventListener('click', () => {
                window.AudioVisualizer.toggleMute();
            });
        }
        
        // Effectuer une première classification
        if (window.Classification) {
            window.Classification.classify();
        }
    },
    
    /**
     * Initialise l'onglet des fichiers vidéo
     */
    initVideoFileTab: function() {
        console.log('Initialisation de l\'onglet des fichiers vidéo...');
        
        // Initialiser le module de fichiers vidéo (à implémenter)
        this.initVideoFileControls();
    },
    
    /**
     * Initialise les contrôles pour les fichiers vidéo
     */
    initVideoFileControls: function() {
        // Cette méthode serait implémentée pour gérer les fichiers vidéo
        console.log('Fonctionnalité de fichiers vidéo non implémentée');
        
        // Pour l'exemple, afficher un message dans l'interface
        const videoFileContent = document.getElementById('video-file');
        if (videoFileContent) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'info-message';
            messageDiv.innerHTML = '<p>La fonctionnalité d\'analyse de fichiers vidéo sera disponible dans une prochaine version.</p>';
            
            // Vérifier si le message existe déjà
            if (!videoFileContent.querySelector('.info-message')) {
                videoFileContent.appendChild(messageDiv);
            }
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Charger d'abord les modules
    const moduleUrls = [
        '/static/js/modules/video-feed.js',
        '/static/js/modules/audio-visualizer.js',
        '/static/js/modules/classification.js',
        '/static/js/modules/model-info.js'
    ];
    
    let modulesLoaded = 0;
    
    // Fonction à exécuter une fois tous les modules chargés
    const initApp = () => {
        ModelTesting.init();
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
