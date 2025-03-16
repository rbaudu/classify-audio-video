#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de vérification de santé de l'application.

Ce module fournit des utilitaires pour surveiller l'état de santé des
différents composants de l'application.
"""

import os
import time
import logging
import threading
from typing import Dict, List, Callable, Any, Optional

from server import DATA_DIR

# Configuration du logger
logger = logging.getLogger(__name__)


class HealthCheck:
    """
    Classe pour effectuer des vérifications de santé périodiques.
    """
    
    def __init__(self):
        """
        Initialise le health checker.
        """
        self.checks: Dict[str, Callable[[], bool]] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
    
    def register_check(self, name: str, check_func: Callable[[], bool]):
        """
        Enregistre une fonction de vérification.
        
        Args:
            name: Nom de la vérification
            check_func: Fonction de vérification qui renvoie True si tout va bien
        """
        with self.lock:
            self.checks[name] = check_func
            self.results[name] = {
                'status': None,
                'last_check': None,
                'last_success': None,
                'consecutive_failures': 0
            }
    
    def run_check(self, name: str) -> bool:
        """
        Exécute une vérification spécifique.
        
        Args:
            name: Nom de la vérification à exécuter
            
        Returns:
            Résultat de la vérification
        """
        if name not in self.checks:
            logger.warning(f"Vérification inconnue: {name}")
            return False
        
        with self.lock:
            now = time.time()
            check_func = self.checks[name]
            success = False
            
            try:
                success = bool(check_func())
                
                # Mettre à jour les résultats
                self.results[name]['last_check'] = now
                self.results[name]['status'] = success
                
                if success:
                    self.results[name]['last_success'] = now
                    self.results[name]['consecutive_failures'] = 0
                else:
                    self.results[name]['consecutive_failures'] += 1
                
                return success
            except Exception as e:
                logger.error(f"Erreur lors de la vérification {name}: {str(e)}")
                self.results[name]['last_check'] = now
                self.results[name]['status'] = False
                self.results[name]['consecutive_failures'] += 1
                return False
    
    def run_all_checks(self) -> Dict[str, bool]:
        """
        Exécute toutes les vérifications enregistrées.
        
        Returns:
            Dictionnaire avec les résultats de toutes les vérifications
        """
        results = {}
        for name in self.checks.keys():
            results[name] = self.run_check(name)
        return results
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Récupère le statut de santé complet.
        
        Returns:
            Dictionnaire avec le statut de santé
        """
        with self.lock:
            all_ok = all(result.get('status', False) for result in self.results.values())
            
            return {
                'status': 'healthy' if all_ok else 'unhealthy',
                'timestamp': time.time(),
                'checks': self.results.copy()
            }


# Singleton global pour les health checks
health_check = HealthCheck()


def register_health_checks():
    """
    Enregistre les health checks standards pour l'application.
    """
    from server.api.external_service import ExternalServiceClient
    from server.capture.sync_manager import SyncManager
    from server.database.db_manager import DBManager
    
    # Vérification de la connexion à la base de données
    db_manager = DBManager()
    health_check.register_check('database_connection', db_manager.check_connection)
    
    # Vérification du service externe
    external_service = ExternalServiceClient()
    health_check.register_check('external_service', 
                              lambda: external_service.get_status() is not None)
    
    # Vérification de la présence d'OBS
    sync_manager = SyncManager()
    health_check.register_check('obs_connection', 
                              lambda: sync_manager.obs_capture.is_connected())
    
    # Vérification du périphérique audio
    health_check.register_check('audio_device', 
                              lambda: sync_manager.audio_capture.check_device())
    
    # Vérification de l'espace disque
    health_check.register_check('disk_space', check_disk_space)


def check_disk_space(min_gb: float = 1.0) -> bool:
    """
    Vérifie s'il y a assez d'espace disque disponible.
    
    Args:
        min_gb: Espace minimum requis en GB
        
    Returns:
        True si assez d'espace disque est disponible, False sinon
    """
    try:
        # Obtenir l'espace disque disponible en octets
        stats = os.statvfs(DATA_DIR)
        free_bytes = stats.f_bavail * stats.f_frsize
        free_gb = free_bytes / (1024 ** 3)  # Convertir en GB
        
        # Vérifier s'il y a assez d'espace
        return free_gb >= min_gb
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de l'espace disque: {str(e)}")
        return False


def check_memory_usage(max_percent: float = 90.0) -> bool:
    """
    Vérifie si l'utilisation de la mémoire est sous un seuil acceptable.
    
    Args:
        max_percent: Pourcentage maximum d'utilisation de la mémoire
        
    Returns:
        True si l'utilisation est sous le seuil, False sinon
    """
    try:
        import psutil
        memory_percent = psutil.virtual_memory().percent
        return memory_percent < max_percent
    except ImportError:
        logger.warning("Module psutil non disponible pour vérifier l'utilisation mémoire")
        return True  # Considérer comme OK si le module n'est pas disponible
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de l'utilisation mémoire: {str(e)}")
        return False


def check_cpu_usage(max_percent: float = 95.0) -> bool:
    """
    Vérifie si l'utilisation du CPU est sous un seuil acceptable.
    
    Args:
        max_percent: Pourcentage maximum d'utilisation du CPU
        
    Returns:
        True si l'utilisation est sous le seuil, False sinon
    """
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.5)
        return cpu_percent < max_percent
    except ImportError:
        logger.warning("Module psutil non disponible pour vérifier l'utilisation CPU")
        return True  # Considérer comme OK si le module n'est pas disponible
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de l'utilisation CPU: {str(e)}")
        return False