#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extensions pour le module de gestion d'erreurs.

Ce module ajoute des fonctionnalités avancées au système de base de gestion des erreurs,
comme les décorateurs de fonctions et les gestionnaires de contexte.
"""

import functools
import logging
import time
import traceback
import inspect
import contextlib
from typing import Any, Callable, Dict, Optional, Type, Union, List, TypeVar

from server.utils.error_handling import AppError, ErrorCode, log_exception
from server.utils.retry import retry, RetryStrategy, ExponentialBackoffStrategy
from server.utils.error_monitor import CircuitBreakerRegistry, log_error

# Configuration du logger
logger = logging.getLogger(__name__)

# Type variable pour le type de retour d'une fonction
T = TypeVar('T')

# Registry global pour les circuit breakers
circuit_breaker_registry = CircuitBreakerRegistry()


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
                        "state": breaker.state,
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
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "timestamp": start_time
                }
                
                # Essayer d'obtenir la signature et les arguments liés
                try:
                    signature = inspect.signature(func)
                    bound_args = signature.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                    call_info["bound_args"] = str(bound_args.arguments)
                except Exception:
                    # Ignorer les erreurs dans la liaison d'arguments
                    pass
                
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


def log_sensitive_operations(operation_name: str, success_level: int = logging.INFO, 
                             error_level: int = logging.ERROR):
    """
    Décorateur spécifique pour les opérations sensibles.
    
    Journalise les opérations sensibles comme les modifications de données, les opérations de sécurité, etc.
    
    Args:
        operation_name: Nom de l'opération à journaliser
        success_level: Niveau de log en cas de succès
        error_level: Niveau de log en cas d'erreur
        
    Returns:
        Décorateur de fonction
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            user_info = kwargs.get('user_id', 'unknown')
            
            logger.log(success_level, 
                      f"Début de l'opération sensible: {operation_name} (utilisateur: {user_info})")
            
            try:
                result = func(*args, **kwargs)
                
                duration = time.time() - start_time
                logger.log(success_level, 
                          f"Opération sensible réussie: {operation_name} (utilisateur: {user_info}, durée: {duration:.3f}s)")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.log(error_level, 
                          f"Erreur dans l'opération sensible: {operation_name} (utilisateur: {user_info}, durée: {duration:.3f}s)")
                logger.log(error_level, f"Détails de l'erreur: {str(e)}")
                log_exception(e)
                raise
                
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
