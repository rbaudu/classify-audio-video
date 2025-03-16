#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'énumérations pour la gestion des erreurs.

Ce module définit les différentes énumérations utilisées dans le système de gestion d'erreurs.
"""

from enum import Enum

class AlertLevel(Enum):
    """
    Niveaux d'alerte pour les erreurs.
    """
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3


class CircuitState(Enum):
    """
    États possibles d'un circuit breaker.
    """
    CLOSED = 'closed'       # Fonctionnement normal
    OPEN = 'open'           # Circuit ouvert, appels bloqués
    HALF_OPEN = 'half_open' # État intermédiaire de test