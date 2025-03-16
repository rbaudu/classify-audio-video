#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'intégration et de configuration du système de gestion d'erreurs.

Ce module sert de point d'entrée unique pour le système de gestion d'erreurs,
offrant un accès aux différentes fonctionnalités disponibles.
"""

import logging
import functools
import traceback
import threading
import time
from typing import Any, Dict, Optional, Callable, Type, Union, List, TypeVar
import contextlib

# Importer les composants du système de gestion d'erreurs
from server.utils.error_handling import AppError, ErrorCode, log_exception
from server.utils.error_monitor import ErrorStats, ErrorAlert, log_error, error_stats, error_alert
from server.utils.error_enums import AlertLevel, CircuitState
from server.utils.health_check import HealthCheck, register_health_checks, health_check
from server.utils.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry, circuit_breaker_registry
from server.utils.retry import retry, RetryStrategy, ExponentialBackoffStrategy, RetryContext

# Configuration du logger
logger = logging.getLogger(__name__)

# Type variable pour le type de retour d'une fonction
T = TypeVar('T')


def init_error_system():
    """
    Initialise le système de gestion d'erreurs.
    
    Cette fonction doit être appelée au démarrage de l'application.
    """
    # Enregistrer les vérifications de santé standard
    register_health_checks()
    
    # Configurer les alertes si nécessaire
    # ...
    
    logger.info("Système de gestion d'erreurs initialisé")


def with_circuit_breaker(name: str, **circuit_kwargs):
    """
    Décorateur qui ajoute un circuit breaker à une fonction.
    
    Si le circuit est ouvert, la fonction ne sera pas appelée et une erreur sera levée.
    
    Args:
        name: Nom du circuit breaker
        **circuit_kwargs: Paramètres pour le circuit breaker
    
    Returns:
        Décorateur de fonction
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Récupérer ou créer le circuit breaker
            breaker = circuit_breaker_registry.get_or_create(name, **circuit_kwargs)
            
            # Vérifier si l'appel est autorisé
            if not breaker.allow_request():
                # Circuit ouvert, retourner une erreur
                raise AppError(
                    ErrorCode.EXTERNAL_SERVICE_ERROR,
                    f"Circuit breaker '{name}' ouvert - Service temporairement indisponible",
                    details={
                        "circuit_breaker": name,
                        "state": breaker.state.value,
                        "recovery_timeout": breaker.recovery_timeout
                    }
                )
            
            try:
                # Appeler la fonction décorée
                result = func(*args, **kwargs)
                
                # Notifier le circuit breaker du succès
                breaker.on_success()
                
                return result
                
            except Exception as e:
                # Notifier le circuit breaker de l'échec
                breaker.on_failure()
                
                # Ré-lever l'exception
                raise
                
        return wrapper
    return decorator


def retry_with_circuit_breaker(name: str, max_retries: int = 3, circuit_kwargs: Optional[Dict] = None):
    """
    Combinaison des décorateurs retry et circuit_breaker.
    
    Args:
        name: Nom du circuit breaker
        max_retries: Nombre maximal de tentatives
        circuit_kwargs: Paramètres pour le circuit breaker
        
    Returns:
        Décorateur de fonction
    """
    circuit_kwargs = circuit_kwargs or {}
    strategy = ExponentialBackoffStrategy(max_retries=max_retries)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Appliquer les deux décorateurs
        retry_func = retry(
            exceptions=Exception,
            strategy=strategy,
            retry_error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            retry_error_message=f"Toutes les tentatives ({max_retries}) ont échoué"
        )(func)
        
        circuit_func = with_circuit_breaker(name, **circuit_kwargs)(retry_func)
        
        return circuit_func
    return decorator


def enhanced_error_handling(error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR, log_level: int = logging.ERROR, 
                           rethrow: bool = False):
    """
    Décorateur avancé pour la gestion des erreurs.
    
    Fournit des informations de diagnostic améliorées et une journalisation structurée.
    
    Args:
        error_code: Code d'erreur par défaut à utiliser si une exception non-AppError est levée
        log_level: Niveau de log à utiliser pour les erreurs
        rethrow: Si True, relancer les exceptions après les avoir loggées
        
    Returns:
        Décorateur de fonction
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Collecter des informations diagnostiques
                start_time = time.time()
                call_info = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "timestamp": start_time
                }
                
                result = func(*args, **kwargs)
                
                # Ajouter des informations sur la durée
                duration = time.time() - start_time
                logger.debug(f"Fonction {func.__name__} exécutée en {duration:.3f} secondes")
                
                return result
                
            except AppError as e:
                # Journaliser et traiter les erreurs spécifiques de l'application
                e.log(log_level)
                if rethrow:
                    raise
                return None
                
            except Exception as e:
                # Convertir les erreurs non-AppError en AppError pour une journalisation structurée
                error = AppError(
                    error_code,
                    f"Erreur lors de l'exécution de {func.__name__}: {str(e)}",
                    details=call_info,
                    original_exception=e
                )
                log_error(error, log_level)
                if rethrow:
                    raise error from e
                return None
                
        return wrapper
    return decorator


@contextlib.contextmanager
def error_boundary(context_name: str, error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR, 
                 log_level: int = logging.ERROR, rethrow: bool = True):
    """
    Gestionnaire de contexte pour délimiter une frontière d'erreur.
    
    Permet de capturer et de traiter les erreurs dans un bloc de code spécifique.
    
    Args:
        context_name: Nom du contexte pour l'identification dans les logs
        error_code: Code d'erreur par défaut à utiliser si une exception non-AppError est levée
        log_level: Niveau de log à utiliser pour les erreurs
        rethrow: Si True, relancer les exceptions après les avoir loggées
        
    Yields:
        Rien
        
    Raises:
        AppError: Si une erreur se produit et rethrow est True
    """
    try:
        # Marquer le début du contexte
        logger.debug(f"Entrée dans le contexte d'erreur: {context_name}")
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        
        # Exécuter le bloc de code protégé
        yield
        
        # Marquer la fin du contexte
        duration = time.time() - start_time
        logger.debug(f"Sortie du contexte d'erreur: {context_name} (durée: {duration:.3f}s)")
        
    except AppError as e:
        # Journaliser et traiter les erreurs spécifiques de l'application
        e.log(log_level)
        if rethrow:
            raise
            
    except Exception as e:
        # Convertir les erreurs non-AppError en AppError pour une journalisation structurée
        error = AppError(
            error_code,
            f"Erreur dans le contexte {context_name}: {str(e)}",
            details={
                "context": context_name,
                "timestamp": time.time(),
                "duration": time.time() - start_time
            },
            original_exception=e
        )
        log_error(error, log_level)
        if rethrow:
            raise error from e


@contextlib.contextmanager
def transaction_boundary(description: str, on_error_callback: Optional[Callable[[Exception], None]] = None):
    """
    Gestionnaire de contexte pour les transactions.
    
    Utile pour les opérations qui doivent être atomiques ou nécessitent un rollback en cas d'erreur.
    
    Args:
        description: Description de la transaction pour les logs
        on_error_callback: Fonction à appeler en cas d'erreur (pour le rollback)
        
    Yields:
        Dict pour stocker l'état de la transaction
        
    Raises:
        Exception: Toute exception levée dans le bloc est propagée après le callback
    """
    # État de la transaction
    transaction_state = {
        "complete": False,
        "error": None,
        "data": {},
        "start_time": time.time()
    }
    
    logger.info(f"Début de la transaction: {description}")
    
    try:
        # Exécuter le bloc de transaction
        yield transaction_state
        
        # Marquer la transaction comme complète
        transaction_state["complete"] = True
        duration = time.time() - transaction_state["start_time"]
        logger.info(f"Transaction réussie: {description} (durée: {duration:.3f}s)")
        
    except Exception as e:
        # Stocker l'erreur
        transaction_state["error"] = e
        duration = time.time() - transaction_state["start_time"]
        logger.error(f"Erreur dans la transaction: {description} (durée: {duration:.3f}s)")
        log_exception(e)
        
        # Appeler le callback de rollback si défini
        if on_error_callback:
            try:
                on_error_callback(e)
                logger.info(f"Rollback exécuté pour la transaction: {description}")
            except Exception as rollback_error:
                logger.critical(f"Erreur lors du rollback de la transaction: {description}")
                log_exception(rollback_error)
        
        # Re-lever l'exception
        raise