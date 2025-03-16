#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de surveillance et récupération des erreurs.

Ce module fournit des utilitaires pour surveiller et alerter sur les erreurs
dans l'application.
"""

import os
import time
import json
import logging
import threading
import traceback
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime
from collections import deque

from server.utils.error_handling import AppError, ErrorCode
from server.utils.error_enums import AlertLevel

# Configuration du logger
logger = logging.getLogger(__name__)

# Configuration des alertes par email (habituellement défini dans config.py)
EMAIL_ALERTS_ENABLED = False  # Désactivé par défaut
EMAIL_SMTP_SERVER = "smtp.example.com"
EMAIL_SMTP_PORT = 587
EMAIL_FROM = "alerts@example.com"
EMAIL_TO = "admin@example.com"
EMAIL_USERNAME = "alerts@example.com"
EMAIL_PASSWORD = ""  # Ne jamais mettre de mot de passe en dur


class ErrorStats:
    """
    Classe pour suivre les statistiques des erreurs.
    """
    
    def __init__(self, window_size: int = 100, time_window: int = 3600):
        """
        Initialise les statistiques d'erreurs.
        
        Args:
            window_size: Nombre d'erreurs à conserver dans l'historique
            time_window: Fenêtre de temps en secondes pour calculer le taux d'erreurs
        """
        self.window_size = window_size
        self.time_window = time_window
        self.error_history = deque(maxlen=window_size)
        self.error_counts: Dict[str, int] = {}
        self.error_rates: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def add_error(self, error: Union[Exception, AppError], code: Optional[ErrorCode] = None):
        """
        Ajoute une erreur aux statistiques.
        
        Args:
            error: L'erreur à ajouter
            code: Code d'erreur optionnel si l'erreur n'est pas une AppError
        """
        with self.lock:
            now = time.time()
            
            # Déterminer le code d'erreur
            if isinstance(error, AppError):
                error_code = error.code
            else:
                error_code = code or ErrorCode.UNKNOWN_ERROR
            
            # Ajouter à l'historique
            error_entry = {
                'timestamp': now,
                'error_type': type(error).__name__,
                'error_code': error_code.name if hasattr(error_code, 'name') else str(error_code),
                'message': str(error)
            }
            self.error_history.append(error_entry)
            
            # Mettre à jour les compteurs
            error_key = error_code.name if hasattr(error_code, 'name') else str(error_code)
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Recalculer les taux d'erreur
            self._update_error_rates(now)
    
    def _update_error_rates(self, current_time: float):
        """
        Met à jour les taux d'erreur basés sur la fenêtre de temps.
        
        Args:
            current_time: Temps actuel en secondes depuis l'epoch
        """
        # Filtrer les erreurs dans la fenêtre de temps
        window_start = current_time - self.time_window
        recent_errors = [e for e in self.error_history if e['timestamp'] >= window_start]
        
        # Compter les erreurs par type dans la fenêtre
        window_counts: Dict[str, int] = {}
        for error in recent_errors:
            error_key = error['error_code']
            window_counts[error_key] = window_counts.get(error_key, 0) + 1
        
        # Calculer les taux (erreurs par heure)
        hours = self.time_window / 3600.0
        self.error_rates = {k: v / hours for k, v in window_counts.items()}
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques d'erreurs actuelles.
        
        Returns:
            Dictionnaire contenant les statistiques d'erreurs
        """
        with self.lock:
            return {
                'total_errors': len(self.error_history),
                'error_counts': self.error_counts.copy(),
                'error_rates': self.error_rates.copy(),
                'recent_errors': list(self.error_history)
            }
    
    def clear_stats(self):
        """
        Réinitialise les statistiques d'erreurs.
        """
        with self.lock:
            self.error_history.clear()
            self.error_counts = {}
            self.error_rates = {}


class ErrorAlert:
    """
    Classe pour gérer les alertes d'erreurs.
    """
    
    def __init__(self, throttle_seconds: int = 300):
        """
        Initialise le gestionnaire d'alertes.
        
        Args:
            throttle_seconds: Temps minimum entre les alertes (en secondes)
        """
        self.throttle_seconds = throttle_seconds
        self.last_alert_time: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def should_alert(self, error_code: ErrorCode) -> bool:
        """
        Détermine si une alerte doit être envoyée pour cette erreur.
        
        Args:
            error_code: Code d'erreur à vérifier
            
        Returns:
            True si une alerte doit être envoyée, False sinon
        """
        with self.lock:
            now = time.time()
            error_key = error_code.name
            
            # Vérifier si l'erreur a été alertée récemment
            if error_key in self.last_alert_time:
                elapsed = now - self.last_alert_time[error_key]
                if elapsed < self.throttle_seconds:
                    return False
            
            # Mettre à jour le timestamp de dernière alerte
            self.last_alert_time[error_key] = now
            return True
    
    def send_email_alert(self, error: AppError, level: AlertLevel = AlertLevel.ERROR) -> bool:
        """
        Envoie une alerte par email pour une erreur.
        
        Args:
            error: L'erreur à signaler
            level: Niveau d'alerte
        
        Returns:
            True si l'email a été envoyé, False sinon
        """
        if not EMAIL_ALERTS_ENABLED:
            logger.debug("Alertes email désactivées dans la configuration")
            return False
        
        # Vérifier si on doit alerter pour cette erreur
        if not self.should_alert(error.code):
            logger.debug(f"Alerte pour {error.code.name} limitée (throttling)")
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            # Préparer le sujet de l'email
            subject = f"[{level.name}] Classify Audio/Video - {error.code.name}: {error.message[:50]}"
            
            # Préparer le corps de l'email
            body = f"""Erreur détectée dans l'application Classify Audio/Video:

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Code: {error.code.name} ({error.code.value})
Message: {error.message}

"""
            
            # Ajouter les détails si disponibles
            if error.details:
                body += f"Détails: {json.dumps(error.details, indent=2)}\n\n"
            
            # Ajouter la stack trace si disponible
            if error.original_exception:
                body += f"\nException d'origine: {type(error.original_exception).__name__}: {str(error.original_exception)}"
                if hasattr(error.original_exception, '__traceback__') and error.original_exception.__traceback__:
                    tb = ''.join(traceback.format_exception(type(error.original_exception), 
                                                           error.original_exception, 
                                                           error.original_exception.__traceback__))
                    body += f"\n\nStack trace:\n{tb}"
            
            # Créer le message email
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = EMAIL_FROM
            msg['To'] = EMAIL_TO
            
            # Envoyer l'email
            with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
                if EMAIL_USERNAME and EMAIL_PASSWORD:
                    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Alerte email envoyée pour {error.code.name}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte email: {str(e)}")
            return False
    
    def send_webhook_alert(self, error: AppError, webhook_url: str, level: AlertLevel = AlertLevel.ERROR) -> bool:
        """
        Envoie une alerte via webhook pour une erreur.
        
        Args:
            error: L'erreur à signaler
            webhook_url: URL du webhook à appeler
            level: Niveau d'alerte
        
        Returns:
            True si le webhook a été appelé avec succès, False sinon
        """
        # Vérifier si on doit alerter pour cette erreur
        if not self.should_alert(error.code):
            logger.debug(f"Alerte pour {error.code.name} limitée (throttling)")
            return False
        
        try:
            import requests
            
            # Préparer les données
            data = {
                'timestamp': datetime.now().isoformat(),
                'level': level.name,
                'code': error.code.name,
                'code_value': error.code.value,
                'message': error.message,
                'details': error.details,
                'error_type': type(error).__name__
            }
            
            # Ajouter des informations sur l'exception d'origine si disponible
            if error.original_exception:
                data['original_exception'] = {
                    'type': type(error.original_exception).__name__,
                    'message': str(error.original_exception)
                }
            
            # Envoyer la requête POST
            response = requests.post(
                webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=5.0  # Timeout de 5 secondes
            )
            
            # Vérifier la réponse
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Alerte webhook envoyée pour {error.code.name}")
                return True
            else:
                logger.warning(f"Erreur lors de l'envoi de l'alerte webhook: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte webhook: {str(e)}")
            return False


# Singleton global pour les statistiques d'erreurs
error_stats = ErrorStats()

# Singleton global pour les alertes d'erreurs
error_alert = ErrorAlert()


def log_error(error: Union[Exception, AppError], level: int = logging.ERROR):
    """
    Enregistre une erreur dans les logs et les statistiques.
    
    Args:
        error: L'erreur à enregistrer
        level: Niveau de log
    """
    # Logger l'erreur
    if isinstance(error, AppError):
        error.log(level)
    else:
        logger.log(level, f"Exception: {str(error)}")
        logger.log(level, f"Type: {type(error).__name__}")
        logger.log(level, f"Stack trace: {traceback.format_exc()}")
    
    # Ajouter aux statistiques
    error_stats.add_error(error)
    
    # Envoyer une alerte si c'est une erreur critique
    if level >= logging.ERROR and isinstance(error, AppError):
        alert_level = AlertLevel.CRITICAL if level >= logging.CRITICAL else AlertLevel.ERROR
        error_alert.send_email_alert(error, level=alert_level)
