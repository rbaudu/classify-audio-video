/**
 * Module de gestion du flux vidéo
 * Gère l'affichage et la mise à jour du flux vidéo
 */

const VideoFeed = {
    // État du flux vidéo
    state: {
        videoSnapshot: null,
        videoStatusInterval: null,
        lastRefresh: 0,
        refreshRate: 200, // ms entre les rafraîchissements
        errorCount: 0,
        maxErrors: 5
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
        videoImg.onerror = () => {
            this.handleImageError();
        };
        videoImg.onload = () => {
            // Réinitialiser le compteur d'erreurs lors d'un chargement réussi
            this.state.errorCount = 0;
            
            // Supprimer le message d'erreur s'il existe
            const noFeedMsg = videoFeedContainer.querySelector('.no-feed-message');
            if (noFeedMsg) {
                noFeedMsg.style.display = 'none';
            }
        };
        videoFeedContainer.appendChild(videoImg);
        
        // Ajouter un message par défaut (caché initialement)
        const noFeedMsg = document.createElement('div');
        noFeedMsg.classList.add('no-feed-message');
        noFeedMsg.textContent = 'Flux vidéo non disponible';
        noFeedMsg.style.display = 'none';
        videoFeedContainer.appendChild(noFeedMsg);
        
        // Fonction pour mettre à jour l'image
        const updateVideoImage = () => {
            const now = Date.now();
            if (now - this.state.lastRefresh >= this.state.refreshRate) {
                this.state.lastRefresh = now;
                
                // Ajouter un timestamp pour éviter le cache du navigateur
                videoImg.src = `/api/video-snapshot?t=${now}`;
                
                // Afficher dans la console un message périodique pour le débogage
                if (Math.random() < 0.05) { // ~5% des rafraîchissements
                    console.log(`Mise à jour de l'image à ${new Date().toLocaleTimeString()}`);
                }
            }
            
            // Planifier la prochaine mise à jour via requestAnimationFrame pour de meilleures performances
            if (this.state.videoSnapshot) {
                cancelAnimationFrame(this.state.videoSnapshot);
            }
            this.state.videoSnapshot = requestAnimationFrame(updateVideoImage);
        };
        
        // Mettre à jour l'image immédiatement puis continuellement avec requestAnimationFrame
        updateVideoImage();
        
        console.log('Flux vidéo initialisé');
    },
    
    /**
     * Gère les erreurs de chargement d'image
     */
    handleImageError: function() {
        this.state.errorCount++;
        const videoFeedContainer = document.getElementById('video-feed');
        if (!videoFeedContainer) return;
        
        const noFeedMsg = videoFeedContainer.querySelector('.no-feed-message');
        
        if (this.state.errorCount > this.state.maxErrors) {
            // Après plusieurs échecs, afficher le message d'erreur
            if (noFeedMsg) {
                noFeedMsg.style.display = 'block';
            }
            
            console.error(`Erreur de chargement d'image après ${this.state.errorCount} tentatives`);
            
            // Ajuster le taux de rafraîchissement pour ne pas surcharger le serveur
            this.state.refreshRate = Math.min(2000, this.state.refreshRate * 1.5);
        }
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
                    
                    // Si tout est OK, revenir à un taux de rafraîchissement normal
                    this.state.refreshRate = 200;
                } else {
                    indicator.innerHTML = `<span class="status-error">${data.message}</span>`;
                    indicator.classList.add('error');
                    indicator.classList.remove('active');
                    
                    console.warn('Problème avec la capture vidéo:', data.message);
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
     * Rafraîchit manuellement l'image vidéo 
     */
    refreshImage: function() {
        const videoFeedContainer = document.getElementById('video-feed');
        if (!videoFeedContainer) return;
        
        const videoImg = videoFeedContainer.querySelector('.video-image');
        if (videoImg) {
            videoImg.src = `/api/video-snapshot?t=${Date.now()}`;
        }
    },
    
    /**
     * Arrête le flux vidéo et nettoie les ressources
     */
    stop: function() {
        if (this.state.videoSnapshot) {
            cancelAnimationFrame(this.state.videoSnapshot);
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
