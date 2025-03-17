/**
 * Module de gestion du flux vidéo
 * Gère l'affichage et la mise à jour du flux vidéo
 */

const VideoFeed = {
    // État du flux vidéo
    state: {
        videoSnapshot: null,
        videoStatusInterval: null
    },

    /**
     * Initialise le flux vidéo
     */
    init: function() {
        console.log('Initialisation du flux vidéo...');
        const videoFeedContainer = document.getElementById('video-feed');
        
        if (!videoFeedContainer) return;
        
        // Vérifier d'abord l'état de la capture vidéo
        this.checkVideoStatus();
        
        // Démarrer l'intervalle de vérification du statut vidéo
        if (this.state.videoStatusInterval) {
            clearInterval(this.state.videoStatusInterval);
        }
        
        this.state.videoStatusInterval = setInterval(() => {
            this.checkVideoStatus();
        }, 5000); // Vérifier toutes les 5 secondes
        
        // Configurer le conteneur vidéo
        videoFeedContainer.innerHTML = '';
        
        // Méthode d'affichage 1 : Utiliser un élément img mis à jour périodiquement
        const videoImg = document.createElement('img');
        videoImg.classList.add('video-image');
        videoImg.alt = 'Flux vidéo en direct';
        videoFeedContainer.appendChild(videoImg);
        
        // Fonction pour mettre à jour l'image
        const updateVideoImage = () => {
            // Ajouter un timestamp pour éviter le cache du navigateur
            videoImg.src = `/api/video-snapshot?t=${new Date().getTime()}`;
        };
        
        // Mettre à jour l'image immédiatement puis toutes les 200ms
        updateVideoImage();
        this.state.videoSnapshot = setInterval(updateVideoImage, 200);
        
        console.log('Flux vidéo initialisé');
    },
    
    /**
     * Vérifie l'état de la capture vidéo
     */
    checkVideoStatus: function() {
        console.log('Vérification du statut vidéo...');
        fetch('/api/video-status')
            .then(response => response.json())
            .then(data => {
                const videoFeedContainer = document.getElementById('video-feed');
                const statusIndicator = videoFeedContainer ? videoFeedContainer.querySelector('.status-indicator') : null;
                
                if (!videoFeedContainer) return;
                
                // Créer l'indicateur de statut s'il n'existe pas
                if (!statusIndicator) {
                    const indicator = document.createElement('div');
                    indicator.classList.add('status-indicator');
                    videoFeedContainer.appendChild(indicator);
                }
                
                const indicator = videoFeedContainer.querySelector('.status-indicator');
                
                if (data.status === 'ok') {
                    indicator.innerHTML = `<span class="status-ok">Caméra active: ${data.currentSource}</span>`;
                    indicator.classList.add('active');
                    indicator.classList.remove('error');
                } else {
                    indicator.innerHTML = `<span class="status-error">${data.message}</span>`;
                    indicator.classList.add('error');
                    indicator.classList.remove('active');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la vérification du statut vidéo:', error);
                const videoFeedContainer = document.getElementById('video-feed');
                if (!videoFeedContainer) return;
                
                const statusIndicator = videoFeedContainer.querySelector('.status-indicator') || document.createElement('div');
                statusIndicator.classList.add('status-indicator');
                statusIndicator.classList.add('error');
                statusIndicator.innerHTML = '<span class="status-error">Erreur de connexion au serveur</span>';
                
                if (!videoFeedContainer.querySelector('.status-indicator')) {
                    videoFeedContainer.appendChild(statusIndicator);
                }
            });
    },
    
    /**
     * Arrête le flux vidéo et nettoie les ressources
     */
    stop: function() {
        if (this.state.videoSnapshot) {
            clearInterval(this.state.videoSnapshot);
            this.state.videoSnapshot = null;
        }
        
        if (this.state.videoStatusInterval) {
            clearInterval(this.state.videoStatusInterval);
            this.state.videoStatusInterval = null;
        }
    }
};

// Exporter le module
window.VideoFeed = VideoFeed;
