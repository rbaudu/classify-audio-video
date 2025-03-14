#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class ExternalServiceClient:
    """
    Client pour interagir avec un service externe via HTTP.
    Responsable d'envoyer les résultats de classification d'activité.
    """
    
    def __init__(self, service_url, api_key=None, timeout=10):
        """
        Initialise le client de service externe.
        
        Args:
            service_url (str): URL du service externe
            api_key (str, optional): Clé API pour l'authentification
            timeout (int, optional): Timeout pour les requêtes HTTP en secondes
        """
        self.service_url = service_url
        self.api_key = api_key
        self.timeout = timeout
        
        logger.info(f"Client de service externe initialisé avec l'URL {service_url}")
    
    def send_activity(self, timestamp, activity, metadata=None):
        """
        Envoie les données d'activité au service externe.
        
        Args:
            timestamp (int): Horodatage Unix de l'activité
            activity (str): Type d'activité détectée
            metadata (dict, optional): Métadonnées supplémentaires
            
        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        try:
            # Préparation des données à envoyer
            payload = {
                'timestamp': timestamp,
                'date_time': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                'activity': activity
            }
            
            # Ajout des métadonnées si présentes
            if metadata:
                payload['metadata'] = metadata
            
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
