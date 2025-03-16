#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'utilitaires pour implémenter des mécanismes de retry.

Ce module fournit des décorateurs et des utilitaires permettant de réessayer
des opérations en cas d'échec avec différentes stratégies de retry.
"""

import time
import logging
import random
import functools
from typing import List, Callable, Type, Union, Optional, Any, TypeVar

from server.utils.error_handling import AppError, ErrorCode

# Configuration du logger
logger = logging.getLogger(__name__)

# Type variable pour le type de retour de la fonction décorée
T = TypeVar('T')

class RetryStrategy:
    """
    Classe de base pour les stratégies de retry.
    """
    
    def __init__(self, max_retries: int = 3):
        """
        Initialise la stratégie de retry.
        
        Args:
            max_retries: Nombre maximal de tentatives
        """
        self.max_retries = max_retries
    
    def get_next_delay(self, attempt: int) -> float:
        """
        Calcule le délai avant la prochaine tentative.
        
        Args:
            attempt: Numéro de la tentative actuelle (commence à 1)
            
        Returns:
            Délai en secondes avant la prochaine tentative
        """
        raise NotImplementedError("Les sous-classes doivent implémenter cette méthode")


class ConstantRetryStrategy(RetryStrategy):
    """
    Stratégie de retry avec un délai constant entre les tentatives.
    """
    
    def __init__(self, delay: float = 1.0, max_retries: int = 3):
        """
        Initialise la stratégie de retry avec délai constant.
        
        Args:
            delay: Délai en secondes entre les tentatives
            max_retries: Nombre maximal de tentatives
        """
        super().__init__(max_retries)
        self.delay = delay
    
    def get_next_delay(self, attempt: int) -> float:
        """
        Retourne un délai constant.
        
        Args:
            attempt: Numéro de la tentative actuelle (ignoré)
            
        Returns:
            Délai constant en secondes
        """
        return self.delay


class ExponentialBackoffStrategy(RetryStrategy):
    """
    Stratégie de retry avec backoff exponentiel.
    """
    
    def __init__(self, initial_delay: float = 0.5, backoff_factor: float = 2.0, 
                 max_delay: float = 60.0, jitter: bool = True, max_retries: int = 5):
        """
        Initialise la stratégie de retry avec backoff exponentiel.
        
        Args:
            initial_delay: Délai initial en secondes
            backoff_factor: Facteur multiplicatif pour le backoff
            max_delay: Délai maximal en secondes
            jitter: Ajouter un élément aléatoire pour éviter les tempêtes de requêtes
            max_retries: Nombre maximal de tentatives
        """
        super().__init__(max_retries)
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.jitter = jitter
    
    def get_next_delay(self, attempt: int) -> float:
        """
        Calcule le délai exponentiel pour la prochaine tentative.
        
        Args:
            attempt: Numéro de la tentative actuelle (commence à 1)
            
        Returns:
            Délai exponentiel en secondes
        """
        delay = min(self.initial_delay * (self.backoff_factor ** (attempt - 1)), self.max_delay)
        
        if self.jitter:
            # Ajouter un jitter entre 0.8 et 1.2 du délai
            delay = delay * (0.8 + random.random() * 0.4)
            
        return delay


def retry(
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    strategy: RetryStrategy = None,
    on_retry: Callable[[Exception, int, float], None] = None,
    retry_error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
    retry_error_message: str = "Échec après plusieurs tentatives",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Décorateur pour réessayer une fonction en cas d'exception.
    
    Args:
        exceptions: Exception(s) sur lesquelles réessayer
        strategy: Stratégie de retry à utiliser
        on_retry: Fonction appelée après chaque tentative échouée
        retry_error_code: Code d'erreur à utiliser si toutes les tentatives échouent
        retry_error_message: Message d'erreur si toutes les tentatives échouent
    
    Returns:
        Décorateur de fonction
    """
    if strategy is None:
        strategy = ExponentialBackoffStrategy()
    
    if not isinstance(exceptions, (list, tuple)):
        exceptions = [exceptions]
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(1, strategy.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e
                    delay = strategy.get_next_delay(attempt)
                    
                    # Journaliser la tentative
                    if attempt < strategy.max_retries:
                        logger.warning(
                            f"Tentative {attempt}/{strategy.max_retries} échouée pour {func.__name__}: "
                            f"{type(e).__name__}: {str(e)}. Nouvelle tentative dans {delay:.2f} secondes."
                        )
                        
                        # Appeler le callback on_retry si défini
                        if on_retry:
                            try:
                                on_retry(e, attempt, delay)
                            except Exception as callback_error:
                                logger.error(f"Erreur dans le callback on_retry: {callback_error}")
                        
                        # Attendre avant la prochaine tentative
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Toutes les tentatives ({strategy.max_retries}) ont échoué pour {func.__name__}: "
                            f"{type(e).__name__}: {str(e)}"
                        )
            
            # Si nous arrivons ici, toutes les tentatives ont échoué
            if isinstance(last_exception, AppError):
                # Si c'est déjà une AppError, la propager
                raise last_exception
            else:
                # Sinon, envelopper dans une AppError
                raise AppError(
                    retry_error_code,
                    retry_error_message,
                    details={
                        "function": func.__name__,
                        "attempts": strategy.max_retries,
                        "last_error": str(last_exception),
                        "last_error_type": type(last_exception).__name__
                    },
                    original_exception=last_exception
                )
        
        return wrapper
    
    return decorator


class RetryContext:
    """
    Gestionnaire de contexte pour réessayer un bloc de code.
    
    Exemple d'utilisation:
    ```
    with RetryContext(max_retries=3, exceptions=[ConnectionError, TimeoutError]) as retry_ctx:
        # Code qui peut échouer
        response = requests.get(url, timeout=5)
        
        # Vérifier une condition et déclencher une nouvelle tentative
        if response.status_code != 200:
            retry_ctx.retry("Réponse non 200")
    ```
    """
    
    def __init__(
        self,
        exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
        strategy: RetryStrategy = None,
        on_retry: Callable[[Exception, int, float], None] = None,
        retry_error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        retry_error_message: str = "Échec après plusieurs tentatives"
    ):
        """
        Initialise le contexte de retry.
        
        Args:
            exceptions: Exception(s) sur lesquelles réessayer
            strategy: Stratégie de retry à utiliser
            on_retry: Fonction appelée après chaque tentative échouée
            retry_error_code: Code d'erreur à utiliser si toutes les tentatives échouent
            retry_error_message: Message d'erreur si toutes les tentatives échouent
        """
        self.exceptions = exceptions if isinstance(exceptions, (list, tuple)) else [exceptions]
        self.strategy = strategy or ExponentialBackoffStrategy()
        self.on_retry = on_retry
        self.retry_error_code = retry_error_code
        self.retry_error_message = retry_error_message
        self.attempt = 1
        self._should_retry = False
        self._retry_reason = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and not self._should_retry:
            # Pas d'exception et pas de demande de retry
            return True
        
        if exc_type is not None and not any(issubclass(exc_type, e) for e in self.exceptions):
            # Exception qui n'est pas dans la liste des exceptions à réessayer
            return False
        
        if self.attempt >= self.strategy.max_retries:
            # Toutes les tentatives ont échoué
            if exc_type is None and self._should_retry:
                # C'était une demande de retry, pas une exception
                exc_message = self._retry_reason or "Condition de retry déclenchée manuellement"
                logger.error(f"Toutes les tentatives ({self.strategy.max_retries}) ont échoué: {exc_message}")
                
                # Lever une AppError
                raise AppError(
                    self.retry_error_code,
                    self.retry_error_message,
                    details={
                        "attempts": self.strategy.max_retries,
                        "last_reason": self._retry_reason
                    }
                )
            return False
        
        # Calculer le délai avant la prochaine tentative
        delay = self.strategy.get_next_delay(self.attempt)
        
        # Journaliser la tentative
        if exc_type is not None:
            logger.warning(
                f"Tentative {self.attempt}/{self.strategy.max_retries} échouée: "
                f"{exc_type.__name__}: {str(exc_val)}. Nouvelle tentative dans {delay:.2f} secondes."
            )
            
            # Appeler le callback on_retry si défini
            if self.on_retry:
                try:
                    self.on_retry(exc_val, self.attempt, delay)
                except Exception as callback_error:
                    logger.error(f"Erreur dans le callback on_retry: {callback_error}")
        elif self._should_retry:
            reason = self._retry_reason or "condition de retry déclenchée manuellement"
            logger.warning(
                f"Tentative {self.attempt}/{self.strategy.max_retries} échouée: "
                f"{reason}. Nouvelle tentative dans {delay:.2f} secondes."
            )
        
        # Attendre avant la prochaine tentative
        time.sleep(delay)
        
        # Incrémenter le compteur de tentatives
        self.attempt += 1
        
        # Réinitialiser le flag de retry
        self._should_retry = False
        self._retry_reason = None
        
        # Indiquer que l'exception a été gérée
        return True
    
    def retry(self, reason: Optional[str] = None):
        """
        Demande une nouvelle tentative.
        
        Args:
            reason: Raison de la nouvelle tentative
        """
        self._should_retry = True
        self._retry_reason = reason
