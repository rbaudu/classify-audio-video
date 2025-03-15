#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import requests
from datetime import datetime

# Import de la configuration
from server import EXTERNAL_SERVICE_URL, EXTERNAL_SERVICE_API_KEY

logger = logging.getLogger(__name__)

class ExternalServiceClient:
    """
    Client pour interagir avec un service externe via HTTP.
    Responsable d'envoyer les résultats de classification d'activité.
    """
    
    def __init__(self, service_url=None, api_key=None, timeout=10):
        """
        Initialise le client de service externe.
        
        Args:
            service_url (str, optional): URL du service externe. Si None, utilise la valeur de la configuration.
            api_key (str, optional): Clé API pour l'authentification. Si None, utilise la valeur de la configuration.
            timeout (int, optional): Timeout pour les requêtes HTTP en secondes
        """
        self.service_url = service_url or EXTERNAL_SERVICE_URL
        self.api_key = api_key or EXTERNAL_SERVICE_API_KEY
        self.timeout = timeout
        
        logger.info(f"Client de service externe initialisé avec l'URL {self.service_url}")
    
    def send_activity(self, activity_data):
        """
        Envoie les données d'activité au service externe.
        
        Args:
            activity_data (dict): Données d'activité complètes
            
        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        if not activity_data:
            logger.warning("Pas de données d'activité à envoyer")
            return False
        
        try:
            # Extraire les infos essentielles de activity_data
            timestamp = activity_data.get('timestamp')
            activity = activity_data.get('activity')
            
            if not timestamp or not activity:
                logger.warning("Données d'activité incomplètes")
                return False
            
            # Préparation des données à envoyer
            payload = {
                'timestamp': timestamp,
                'date_time': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                'activity': activity,
                'metadata': activity_data.get('features', {})
            }
            
            # Préparation des headers
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Ajout de la clé API si présente
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # Envoi de la requête POST
            response = requests.post(
                self.service_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=self.timeout
            )
            
            # Vérification de la réponse
            if response.status_code == 200:
                logger.info(f"Activité '{activity}' envoyée avec succès au service externe")
                return True
            else:
                logger.warning(f"Erreur lors de l'envoi de l'activité au service externe: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Erreur de connexion au service externe: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'envoi de l'activité: {str(e)}")
            return False
    
    def get_status(self):
        """
        Vérifie le statut du service externe.
        
        Returns:
            dict: Statut du service ou None en cas d'erreur
        """
        try:
            # Construction de l'URL de status
            status_url = f"{self.service_url.rstrip('/')}/status"
            
            # Préparation des headers
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # Envoi de la requête GET
            response = requests.get(
                status_url,
                headers=headers,
                timeout=self.timeout
            )
            
            # Vérification de la réponse
            if response.status_code == 200:
                status_data = response.json()
                logger.info(f"Statut du service externe récupéré: {status_data}")
                return status_data
            else:
                logger.warning(f"Erreur lors de la récupération du statut: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Erreur de connexion lors de la vérification du statut: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la vérification du statut: {str(e)}")
            return None
