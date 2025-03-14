/**
 * Script principal pour l'application Classify Audio Video
 * Contient les fonctions communes utilisées dans toute l'application
 */

// Configuration globale
const CONFIG = {
    API_BASE_URL: '/api',
    REFRESH_INTERVAL: 5000, // 5 secondes
    ACTIVITY_ICONS: {
        'endormi': '😴',
        'à table': '🍽️',
        'lisant': '📖',
        'au téléphone': '📱',
        'en conversation': '🗣️',
        'occupé': '🏃',
        'inactif': '💤'
    },
    ACTIVITY_COLORS: {
        'endormi': '#90caf9',
        'à table': '#ffcc80',
        'lisant': '#a5d6a7',
        'au téléphone': '#ef9a9a',
        'en conversation': '#ce93d8',
        'occupé': '#ffab91',
        'inactif': '#b0bec5'
    }
};

// Utilitaires
const Utils = {
    /**
     * Formate un timestamp Unix en date/heure lisible
     * @param {number} timestamp - Timestamp Unix en secondes
     * @param {boolean} includeSeconds - Inclure les secondes dans le format
     * @returns {string} Date formatée
     */
    formatDateTime: function(timestamp, includeSeconds = true) {
        if (!timestamp) return '-';
        
        const date = new Date(timestamp * 1000);
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear();
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        
        if (includeSeconds) {
            const seconds = date.getSeconds().toString().padStart(2, '0');
            return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
        }
        
        return `${day}/${month}/${year} ${hours}:${minutes}`;
    },
    
    /**
     * Formate une durée en secondes en format lisible (HH:MM:SS)
     * @param {number} seconds - Durée en secondes
     * @returns {string} Durée formatée
     */
    formatDuration: function(seconds) {
        if (!seconds && seconds !== 0) return '-';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${remainingSeconds}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${remainingSeconds}s`;
        } else {
            return `${remainingSeconds}s`;
        }
    },
    
    /**
     * Récupère l'icône correspondant à une activité
     * @param {string} activity - Nom de l'activité
     * @returns {string} Icône (emoji)
     */
    getActivityIcon: function(activity) {
        return CONFIG.ACTIVITY_ICONS[activity] || '❓';
    },
    
    /**
     * Récupère la couleur correspondant à une activité
     * @param {string} activity - Nom de l'activité
     * @returns {string} Code couleur hexadécimal
     */
    getActivityColor: function(activity) {
        return CONFIG.ACTIVITY_COLORS[activity] || '#cccccc';
    },
    
    /**
     * Effectue une requête API
     * @param {string} endpoint - Point d'accès API (sans le préfixe de base)
     * @param {object} options - Options de la requête fetch
     * @returns {Promise<object>} Promesse résolvant avec les données JSON
     */
    fetchAPI: async function(endpoint, options = {}) {
        try {
            const url = `${CONFIG.API_BASE_URL}${endpoint}`;
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`Erreur API: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Erreur lors de l'appel API à ${endpoint}:`, error);
            throw error;
        }
    },
    
    /**
     * Affiche un message d'erreur à l'utilisateur
     * @param {string} message - Message d'erreur
     * @param {number} duration - Durée d'affichage en millisecondes
     */
    showError: function(message, duration = 5000) {
        // Vérifier si un conteneur d'erreur existe déjà
        let errorContainer = document.getElementById('error-container');
        
        // Si non, en créer un
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.id = 'error-container';
            errorContainer.style.position = 'fixed';
            errorContainer.style.top = '20px';
            errorContainer.style.right = '20px';
            errorContainer.style.zIndex = '1000';
            document.body.appendChild(errorContainer);
        }
        
        // Créer le message d'erreur
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.style.backgroundColor = '#f44336';
        errorElement.style.color = 'white';
        errorElement.style.padding = '10px 15px';
        errorElement.style.marginBottom = '10px';
        errorElement.style.borderRadius = '4px';
        errorElement.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.2)';
        errorElement.style.animation = 'fadeIn 0.3s';
        errorElement.textContent = message;
        
        // Ajouter un bouton de fermeture
        const closeButton = document.createElement('span');
        closeButton.innerHTML = '&times;';
        closeButton.style.marginLeft = '10px';
        closeButton.style.float = 'right';
        closeButton.style.cursor = 'pointer';
        closeButton.onclick = function() {
            errorContainer.removeChild(errorElement);
        };
        
        errorElement.appendChild(closeButton);
        errorContainer.appendChild(errorElement);
        
        // Supprimer après la durée spécifiée
        setTimeout(() => {
            if (errorElement.parentNode === errorContainer) {
                errorContainer.removeChild(errorElement);
            }
        }, duration);
    }
};

// Gestionnaire d'état de connexion
const ConnectionManager = {
    isConnected: true,
    checkInterval: null,
    
    /**
     * Initialise la vérification de connexion
     * @param {number} interval - Intervalle en millisecondes entre les vérifications
     */
    init: function(interval = 10000) {
        this.checkInterval = setInterval(() => this.checkConnection(), interval);
        this.checkConnection();
    },
    
    /**
     * Vérifie l'état de la connexion au serveur
     */
    checkConnection: async function() {
        try {
            const result = await fetch(`${CONFIG.API_BASE_URL}/current-activity`, {
                method: 'HEAD',
                cache: 'no-store'
            });
            
            const wasConnected = this.isConnected;
            this.isConnected = result.ok;
            
            // Si l'état a changé
            if (wasConnected !== this.isConnected) {
                this.updateConnectionStatus();
                
                if (this.isConnected) {
                    console.log('Reconnecté au serveur');
                    // Déclencher un événement personnalisé pour la reconnexion
                    document.dispatchEvent(new CustomEvent('server-reconnected'));
                } else {
                    console.log('Connexion au serveur perdue');
                    Utils.showError('Connexion au serveur perdue. Tentative de reconnexion...');
                }
            }
        } catch (error) {
            if (this.isConnected) {
                this.isConnected = false;
                this.updateConnectionStatus();
                console.log('Connexion au serveur perdue', error);
                Utils.showError('Connexion au serveur perdue. Tentative de reconnexion...');
            }
        }
    },
    
    /**
     * Met à jour les indicateurs d'état de connexion dans l'interface
     */
    updateConnectionStatus: function() {
        const statusElements = document.querySelectorAll('.status-dot');
        const statusTextElements = document.querySelectorAll('.status-text');
        
        statusElements.forEach(element => {
            if (this.isConnected) {
                element.classList.remove('disconnected');
                element.classList.add('connected');
            } else {
                element.classList.remove('connected');
                element.classList.add('disconnected');
            }
        });
        
        statusTextElements.forEach(element => {
            element.textContent = this.isConnected ? 'Connecté' : 'Déconnecté';
        });
    }
};

// Gestionnaire de temps d'exécution
const UptimeManager = {
    startTime: null,
    uptimeElement: null,
    updateInterval: null,
    
    /**
     * Initialise le gestionnaire de temps d'exécution
     */
    init: function() {
        this.startTime = new Date();
        this.uptimeElement = document.getElementById('uptime');
        
        if (this.uptimeElement) {
            this.updateInterval = setInterval(() => this.updateUptime(), 1000);
            this.updateUptime();
        }
    },
    
    /**
     * Met à jour l'affichage du temps d'exécution
     */
    updateUptime: function() {
        if (!this.uptimeElement) return;
        
        const now = new Date();
        const diffInSeconds = Math.floor((now - this.startTime) / 1000);
        
        const hours = Math.floor(diffInSeconds / 3600).toString().padStart(2, '0');
        const minutes = Math.floor((diffInSeconds % 3600) / 60).toString().padStart(2, '0');
        const seconds = (diffInSeconds % 60).toString().padStart(2, '0');
        
        this.uptimeElement.textContent = `${hours}:${minutes}:${seconds}`;
    }
};

// Gestion des modales
const ModalManager = {
    /**
     * Ouvre une modale
     * @param {string} modalId - ID de l'élément modal à ouvrir
     */
    openModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            
            // Ajouter gestionnaire pour fermer la modale en cliquant à l'extérieur
            window.onclick = function(event) {
                if (event.target === modal) {
                    ModalManager.closeModal(modalId);
                }
            };
            
            // Ajouter gestionnaire pour le bouton de fermeture
            const closeButton = modal.querySelector('.close-modal');
            if (closeButton) {
                closeButton.onclick = function() {
                    ModalManager.closeModal(modalId);
                };
            }
        }
    },
    
    /**
     * Ferme une modale
     * @param {string} modalId - ID de l'élément modal à fermer
     */
    closeModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser le gestionnaire de connexion
    ConnectionManager.init();
    
    // Initialiser le gestionnaire de temps d'exécution
    UptimeManager.init();
    
    // Initialiser les modales
    document.querySelectorAll('.modal').forEach(modal => {
        const closeButton = modal.querySelector('.close-modal');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
    });
    
    // Fermer les modales lors d'un clic à l'extérieur
    window.addEventListener('click', event => {
        document.querySelectorAll('.modal').forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
});
