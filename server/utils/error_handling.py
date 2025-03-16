"""
Module pour la gestion des erreurs de l'application.

Ce module fournit des classes d'exceptions personnalisées et des fonctions 
pour gérer les erreurs de manière cohérente dans toute l'application.
"""
import logging
import traceback
import sys
import json
from enum import Enum
from functools import wraps
from flask import jsonify, Response

# Configuration du logger
logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """Codes d'erreur standardisés pour l'application"""
    # Erreurs générales (1-99)
    UNKNOWN_ERROR = 1
    CONFIG_ERROR = 2
    INITIALIZATION_ERROR = 3
    
    # Erreurs de capture (100-199)
    OBS_CONNECTION_ERROR = 100
    OBS_STREAM_ERROR = 101
    AUDIO_DEVICE_ERROR = 110
    AUDIO_STREAM_ERROR = 111
    SYNC_ERROR = 120
    
    # Erreurs d'analyse (200-299)
    ANALYSIS_DATA_ERROR = 200
    ANALYSIS_PROCESSING_ERROR = 201
    CLASSIFICATION_ERROR = 210
    MODEL_LOADING_ERROR = 211
    
    # Erreurs de base de données (300-399)
    DB_CONNECTION_ERROR = 300
    DB_QUERY_ERROR = 301
    DB_WRITE_ERROR = 302
    DB_INTEGRITY_ERROR = 303
    
    # Erreurs d'API (400-499)
    API_REQUEST_ERROR = 400
    API_RESPONSE_ERROR = 401
    EXTERNAL_SERVICE_ERROR = 410
    RATE_LIMIT_ERROR = 411
    
    # Erreurs de ressources (500-599)
    FILE_NOT_FOUND_ERROR = 500
    PERMISSION_ERROR = 501
    RESOURCE_BUSY_ERROR = 502
    RESOURCE_EXHAUSTED_ERROR = 503

class AppError(Exception):
    """
    Classe de base pour toutes les exceptions de l'application.
    
    Attributs:
        code (ErrorCode): Code d'erreur standardisé
        message (str): Message d'erreur descriptif
        details (dict, optional): Détails supplémentaires sur l'erreur
        original_exception (Exception, optional): Exception d'origine
    """
    
    def __init__(self, code, message, details=None, original_exception=None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.original_exception = original_exception
        super().__init__(self.message)
    
    def to_dict(self):
        """Convertit l'erreur en dictionnaire pour la sérialisation"""
        error_dict = {
            'error': True,
            'code': self.code.value,
            'code_name': self.code.name,
            'message': self.message
        }
        
        if self.details:
            error_dict['details'] = self.details
            
        if self.original_exception:
            error_dict['original_error'] = str(self.original_exception)
            
        return error_dict
    
    def log(self, level=logging.ERROR):
        """Enregistre l'erreur dans les logs"""
        log_message = f"[{self.code.name}] {self.message}"
        
        if self.details:
            log_message += f" - Details: {json.dumps(self.details)}"
            
        if self.original_exception:
            log_message += f" - Original exception: {self.original_exception}"
            logger.log(level, log_message, exc_info=self.original_exception)
        else:
            logger.log(level, log_message)

# Classes d'erreurs spécifiques

class CaptureError(AppError):
    """Erreurs liées à la capture audio/vidéo"""
    pass

class OBSError(CaptureError):
    """Erreurs spécifiques à OBS"""
    pass

class AudioError(CaptureError):
    """Erreurs spécifiques à la capture audio"""
    pass

class SyncError(CaptureError):
    """Erreurs de synchronisation audio/vidéo"""
    pass

class AnalysisError(AppError):
    """Erreurs liées à l'analyse et la classification"""
    pass

class ClassificationError(AnalysisError):
    """Erreurs spécifiques à la classification d'activité"""
    pass

class DatabaseError(AppError):
    """Erreurs liées à la base de données"""
    pass

class APIError(AppError):
    """Erreurs liées aux API"""
    pass

class ExternalServiceError(APIError):
    """Erreurs de communication avec les services externes"""
    pass

class ResourceError(AppError):
    """Erreurs liées aux ressources (fichiers, etc.)"""
    pass

# Fonctions utilitaires pour la gestion des erreurs

def handle_exceptions(func):
    """
    Décorateur pour gérer les exceptions dans les fonctions générales
    
    Args:
        func: La fonction à décorer
        
    Returns:
        La fonction décorée avec gestion d'erreurs
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            # Les erreurs de l'application sont déjà formatées
            e.log()
            return None
        except Exception as e:
            # Exceptions inattendues
            error = AppError(
                ErrorCode.UNKNOWN_ERROR,
                f"Erreur inattendue lors de l'exécution de {func.__name__}",
                details={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)},
                original_exception=e
            )
            error.log(logging.CRITICAL)
            return None
    return wrapper

def handle_route_exceptions(func):
    """
    Décorateur pour gérer les exceptions dans les routes Flask
    
    Args:
        func: La fonction de route à décorer
        
    Returns:
        La fonction de route décorée avec gestion d'erreurs
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            # Les erreurs de l'application sont formatées et renvoyées en JSON
            e.log()
            status_code = determine_http_status(e.code)
            return jsonify(e.to_dict()), status_code
        except Exception as e:
            # Exceptions inattendues
            error = AppError(
                ErrorCode.UNKNOWN_ERROR,
                f"Erreur inattendue lors de l'exécution de {func.__name__}",
                details={"route": func.__name__, "args": str(args), "kwargs": str(kwargs)},
                original_exception=e
            )
            error.log(logging.CRITICAL)
            return jsonify(error.to_dict()), 500
    return wrapper

def determine_http_status(error_code):
    """
    Détermine le code de statut HTTP approprié en fonction du code d'erreur
    
    Args:
        error_code (ErrorCode): Code d'erreur de l'application
        
    Returns:
        int: Code de statut HTTP correspondant
    """
    # Codes d'erreur associés aux codes HTTP
    error_to_http = {
        # Erreurs générales
        ErrorCode.UNKNOWN_ERROR: 500,
        ErrorCode.CONFIG_ERROR: 500,
        ErrorCode.INITIALIZATION_ERROR: 500,
        
        # Erreurs de capture
        ErrorCode.OBS_CONNECTION_ERROR: 503,  # Service Unavailable
        ErrorCode.OBS_STREAM_ERROR: 503,
        ErrorCode.AUDIO_DEVICE_ERROR: 503,
        ErrorCode.AUDIO_STREAM_ERROR: 503,
        ErrorCode.SYNC_ERROR: 500,
        
        # Erreurs d'analyse
        ErrorCode.ANALYSIS_DATA_ERROR: 400,  # Bad Request
        ErrorCode.ANALYSIS_PROCESSING_ERROR: 500,
        ErrorCode.CLASSIFICATION_ERROR: 500,
        ErrorCode.MODEL_LOADING_ERROR: 500,
        
        # Erreurs de base de données
        ErrorCode.DB_CONNECTION_ERROR: 503,
        ErrorCode.DB_QUERY_ERROR: 500,
        ErrorCode.DB_WRITE_ERROR: 500,
        ErrorCode.DB_INTEGRITY_ERROR: 400,
        
        # Erreurs d'API
        ErrorCode.API_REQUEST_ERROR: 400,
        ErrorCode.API_RESPONSE_ERROR: 500,
        ErrorCode.EXTERNAL_SERVICE_ERROR: 502,  # Bad Gateway
        ErrorCode.RATE_LIMIT_ERROR: 429,  # Too Many Requests
        
        # Erreurs de ressources
        ErrorCode.FILE_NOT_FOUND_ERROR: 404,  # Not Found
        ErrorCode.PERMISSION_ERROR: 403,  # Forbidden
        ErrorCode.RESOURCE_BUSY_ERROR: 423,  # Locked
        ErrorCode.RESOURCE_EXHAUSTED_ERROR: 429
    }
    
    # Retourner le code HTTP correspondant ou 500 par défaut
    return error_to_http.get(error_code, 500)

def log_exception(e):
    """
    Enregistre une exception dans les logs avec le stack trace complet
    
    Args:
        e (Exception): L'exception à enregistrer
    """
    logger.error(f"Exception: {str(e)}")
    logger.error(f"Type: {type(e).__name__}")
    logger.error(f"Stack trace: {traceback.format_exc()}")
    
    # Si c'est une AppError, enregistrer les détails spécifiques
    if isinstance(e, AppError):
        logger.error(f"App Error Code: {e.code.name}")
        logger.error(f"Details: {e.details}")
        if e.original_exception:
            logger.error(f"Original exception: {e.original_exception}")
