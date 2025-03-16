#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de circuit breaker pour éviter les appels répétés à des services en échec.

Ce module implémente le pattern Circuit Breaker pour améliorer la résilience
des appels aux services externes.
"""

import time
import logging
import threading
from typing import Dict, Optional, Any

from server.utils.error_enums import CircuitState
from server.utils.error_handling import AppError, ErrorCode

# Configuration du logger
logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Implémentation du pattern Circuit Breaker pour éviter les appels répétés à un service en échec.
    
    Le circuit breaker a trois états:
    - CLOSED: Tout fonctionne normalement, les appels sont autorisés
    - OPEN: Trop d'échecs, les appels sont bloqués pour une durée déterminée
    - HALF_OPEN: Période de test après OPEN, permet quelques appels pour vérifier si le service est rétabli
    """
    
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60, 
                 half_open_max_calls: int = 2):
        """
        Initialise le circuit breaker.
        
        Args:
            name: Nom du circuit (pour identification)
            failure_threshold: Nombre d'échecs consécutifs avant d'ouvrir le circuit
            recovery_timeout: Temps en secondes avant de passer à l'état HALF_OPEN
            half_open_max_calls: Nombre maximal d'appels autorisés en état HALF_OPEN
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        self.lock = threading.RLock()
    
    def allow_request(self) -> bool:
        """
        Vérifie si une requête est autorisée selon l'état actuel du circuit.
        
        Returns:
            True si la requête est autorisée, False sinon
        """
        with self.lock:
            now = time.time()
            
            if self.state == CircuitState.OPEN:
                # Vérifier si le temps de récupération est passé
                if now - self.last_failure_time >= self.recovery_timeout:
                    logger.info(f"Circuit breaker '{self.name}' passe de OPEN à HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                else:
                    # Circuit toujours ouvert
                    return False
            
            if self.state == CircuitState.HALF_OPEN:
                # En état HALF_OPEN, limiter le nombre d'appels
                if self.half_open_calls >= self.half_open_max_calls:
                    return False
                self.half_open_calls += 1
            
            # En état CLOSED ou quelques appels en HALF_OPEN
            return True
    
    def on_success(self):
        """
        Appelé après un appel réussi au service.
        Réinitialise le circuit si nécessaire.
        """
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                # Si succès en état HALF_OPEN, fermer le circuit
                logger.info(f"Circuit breaker '{self.name}' passe de HALF_OPEN à CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
            elif self.state == CircuitState.CLOSED:
                # En état CLOSED, réinitialiser le compteur d'échecs
                self.failure_count = 0
    
    def on_failure(self):
        """
        Appelé après un appel échoué au service.
        Peut ouvrir le circuit si le seuil d'échecs est atteint.
        """
        with self.lock:
            now = time.time()
            
            if self.state == CircuitState.CLOSED:
                # Incrémenter le compteur d'échecs
                self.failure_count += 1
                
                # Vérifier si le seuil est atteint
                if self.failure_count >= self.failure_threshold:
                    logger.warning(f"Circuit breaker '{self.name}' passe de CLOSED à OPEN après {self.failure_count} échecs")
                    self.state = CircuitState.OPEN
                    self.last_failure_time = now
                    
            elif self.state == CircuitState.HALF_OPEN:
                # Retourner à l'état OPEN en cas d'échec
                logger.warning(f"Circuit breaker '{self.name}' passe de HALF_OPEN à OPEN après un échec")
                self.state = CircuitState.OPEN
                self.last_failure_time = now
                self.half_open_calls = 0
    
    def reset(self):
        """
        Réinitialise le circuit breaker à son état initial.
        """
        with self.lock:
            logger.info(f"Circuit breaker '{self.name}' réinitialisé")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = 0
            self.half_open_calls = 0
    
    def get_state(self) -> dict:
        """
        Récupère l'état actuel du circuit breaker.
        
        Returns:
            Dictionnaire avec les informations d'état
        """
        with self.lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'last_failure_time': self.last_failure_time,
                'half_open_calls': self.half_open_calls,
                'failure_threshold': self.failure_threshold,
                'recovery_timeout': self.recovery_timeout
            }


# Gestionnaire global des circuit breakers
class CircuitBreakerRegistry:
    """
    Registre pour gérer tous les circuit breakers de l'application.
    """
    
    def __init__(self):
        """
        Initialise le registre.
        """
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.RLock()
    
    def get_or_create(self, name: str, **kwargs) -> CircuitBreaker:
        """
        Récupère un circuit breaker existant ou en crée un nouveau.
        
        Args:
            name: Nom du circuit breaker
            **kwargs: Paramètres pour la création d'un nouveau circuit breaker
            
        Returns:
            Le circuit breaker demandé
        """
        with self.lock:
            if name in self.breakers:
                return self.breakers[name]
            
            breaker = CircuitBreaker(name, **kwargs)
            self.breakers[name] = breaker
            return breaker
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """
        Récupère un circuit breaker existant.
        
        Args:
            name: Nom du circuit breaker
            
        Returns:
            Le circuit breaker s'il existe, None sinon
        """
        with self.lock:
            return self.breakers.get(name)
    
    def reset_all(self):
        """
        Réinitialise tous les circuit breakers.
        """
        with self.lock:
            for breaker in self.breakers.values():
                breaker.reset()
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Récupère l'état de tous les circuit breakers.
        
        Returns:
            Dictionnaire avec les états de tous les circuit breakers
        """
        with self.lock:
            return {name: breaker.get_state() for name, breaker in self.breakers.items()}


# Singleton global pour les circuit breakers
circuit_breaker_registry = CircuitBreakerRegistry()