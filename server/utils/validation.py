#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de validation des entrées et de gestion de contexte.

Ce module fournit des fonctions et classes pour valider les entrées
et gérer des contextes avec gestion d'erreurs intégrée.
"""

import logging
import functools
import contextlib
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union, TypeVar, cast

from server.utils.error_handling import AppError, ErrorCode

# Configuration du logger
logger = logging.getLogger(__name__)

# Type variable pour le décorateur
T = TypeVar('T')


def validate_arguments(func: Callable[..., T]) -> Callable[..., T]:
    """
    Décorateur qui valide les arguments d'une fonction selon ses annotations de type.
    Lève une AppError si les types ne correspondent pas.
    
    Args:
        func: La fonction à décorer
        
    Returns:
        La fonction décorée avec validation d'arguments
    """
    signature = inspect.signature(func)
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Lier les arguments à la signature
        try:
            bound_args = signature.bind(*args, **kwargs)
            bound_args.apply_defaults()
        except TypeError as e:
            # Erreur lors de la liaison des arguments (arguments manquants, etc.)
            raise AppError(
                ErrorCode.API_REQUEST_ERROR,
                f"Erreur de validation des arguments: {str(e)}",
                details={
                    "function": func.__name__,
                    "error": str(e)
                }
            )
        
        # Valider les types des arguments
        for param_name, param_value in bound_args.arguments.items():
            param = signature.parameters.get(param_name)
            if param and param.annotation != inspect.Parameter.empty:
                expected_type = param.annotation
                
                # Ignorer Optional[...]
                if hasattr(expected_type, "__origin__") and expected_type.__origin__ is Union:
                    if type(None) in expected_type.__args__:
                        # C'est un Optional[...]
                        if param_value is None:
                            # None est valide pour Optional
                            continue
                        # Extraire le type réel sans None
                        non_none_types = [t for t in expected_type.__args__ if t is not type(None)]
                        if len(non_none_types) == 1:
                            expected_type = non_none_types[0]
                
                # Vérifier le type
                if not isinstance(param_value, expected_type):
                    raise AppError(
                        ErrorCode.API_REQUEST_ERROR,
                        f"Type d'argument invalide pour '{param_name}'",
                        details={
                            "function": func.__name__,
                            "param": param_name,
                            "expected_type": str(expected_type),
                            "actual_type": type(param_value).__name__,
                            "value": str(param_value)
                        }
                    )
        
        # Appeler la fonction avec les arguments validés
        return func(*args, **kwargs)
    
    return wrapper


def validate_not_none(value: Any, name: str, error_code: ErrorCode = ErrorCode.API_REQUEST_ERROR):
    """
    Vérifie qu'une valeur n'est pas None.
    
    Args:
        value: La valeur à vérifier
        name: Le nom de la valeur (pour le message d'erreur)
        error_code: Code d'erreur à utiliser si la validation échoue
        
    Raises:
        AppError: Si la valeur est None
    """
    if value is None:
        raise AppError(
            error_code,
            f"La valeur '{name}' ne peut pas être None",
            details={"param": name}
        )


def validate_not_empty(value: Union[str, List, Dict], name: str, 
                      error_code: ErrorCode = ErrorCode.API_REQUEST_ERROR):
    """
    Vérifie qu'une valeur n'est pas vide (chaîne, liste, dictionnaire).
    
    Args:
        value: La valeur à vérifier
        name: Le nom de la valeur (pour le message d'erreur)
        error_code: Code d'erreur à utiliser si la validation échoue
        
    Raises:
        AppError: Si la valeur est vide
    """
    if not value:
        raise AppError(
            error_code,
            f"La valeur '{name}' ne peut pas être vide",
            details={"param": name}
        )


def validate_in_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float], 
                     name: str, error_code: ErrorCode = ErrorCode.API_REQUEST_ERROR):
    """
    Vérifie qu'une valeur numérique est dans une plage donnée.
    
    Args:
        value: La valeur à vérifier
        min_val: Valeur minimale (inclusive)
        max_val: Valeur maximale (inclusive)
        name: Le nom de la valeur (pour le message d'erreur)
        error_code: Code d'erreur à utiliser si la validation échoue
        
    Raises:
        AppError: Si la valeur est hors de la plage
    """
    if value < min_val or value > max_val:
        raise AppError(
            error_code,
            f"La valeur '{name}' doit être entre {min_val} et {max_val}",
            details={
                "param": name,
                "value": value,
                "min": min_val,
                "max": max_val
            }
        )


def validate_matches(value: str, pattern: str, name: str, 
                    error_code: ErrorCode = ErrorCode.API_REQUEST_ERROR):
    """
    Vérifie qu'une chaîne correspond à un pattern regex.
    
    Args:
        value: La chaîne à vérifier
        pattern: Le pattern regex
        name: Le nom de la valeur (pour le message d'erreur)
        error_code: Code d'erreur à utiliser si la validation échoue
        
    Raises:
        AppError: Si la chaîne ne correspond pas au pattern
    """
    import re
    if not re.match(pattern, value):
        raise AppError(
            error_code,
            f"La valeur '{name}' ne correspond pas au format attendu",
            details={
                "param": name,
                "value": value,
                "pattern": pattern
            }
        )


def validate_file_exists(path: str, name: str, 
                         error_code: ErrorCode = ErrorCode.FILE_NOT_FOUND_ERROR):
    """
    Vérifie qu'un fichier existe.
    
    Args:
        path: Chemin du fichier à vérifier
        name: Le nom du paramètre (pour le message d'erreur)
        error_code: Code d'erreur à utiliser si la validation échoue
        
    Raises:
        AppError: Si le fichier n'existe pas
    """
    import os
    if not os.path.exists(path):
        raise AppError(
            error_code,
            f"Le fichier '{name}' n'existe pas: {path}",
            details={
                "param": name,
                "path": path
            }
        )
    
    if not os.path.isfile(path):
        raise AppError(
            error_code,
            f"Le chemin '{name}' n'est pas un fichier: {path}",
            details={
                "param": name,
                "path": path
            }
        )


class ValidationContext:
    """
    Gestionnaire de contexte pour la validation d'entrées.
    
    Exemple d'utilisation:
    ```
    with ValidationContext("Validation des paramètres de classification") as ctx:
        ctx.validate_not_none(model_name, "model_name")
        ctx.validate_in_range(confidence_threshold, 0.0, 1.0, "confidence_threshold")
        ctx.validate_file_exists(input_file, "input_file")
    ```
    """
    
    def __init__(self, context_name: str, error_code: ErrorCode = ErrorCode.API_REQUEST_ERROR):
        """
        Initialise le contexte de validation.
        
        Args:
            context_name: Nom du contexte (pour les messages d'erreur)
            error_code: Code d'erreur par défaut pour les validations
        """
        self.context_name = context_name
        self.error_code = error_code
        self.errors: List[AppError] = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.errors:
            # Combiner toutes les erreurs en une seule
            details = {
                "context": self.context_name,
                "errors": [{
                    "code": e.code.name,
                    "message": e.message,
                    "details": e.details
                } for e in self.errors]
            }
            
            raise AppError(
                self.error_code,
                f"Erreurs de validation dans {self.context_name}",
                details=details
            )
        
        return False  # Ne pas supprimer d'autres exceptions
    
    def add_error(self, error: AppError):
        """
        Ajoute une erreur au contexte.
        
        Args:
            error: Erreur à ajouter
        """
        self.errors.append(error)
    
    def validate_not_none(self, value: Any, name: str, error_code: Optional[ErrorCode] = None):
        """
        Vérifie qu'une valeur n'est pas None.
        
        Args:
            value: La valeur à vérifier
            name: Le nom de la valeur
            error_code: Code d'erreur optionnel
        """
        try:
            validate_not_none(value, name, error_code or self.error_code)
        except AppError as e:
            self.add_error(e)
    
    def validate_not_empty(self, value: Union[str, List, Dict], name: str, 
                          error_code: Optional[ErrorCode] = None):
        """
        Vérifie qu'une valeur n'est pas vide.
        
        Args:
            value: La valeur à vérifier
            name: Le nom de la valeur
            error_code: Code d'erreur optionnel
        """
        try:
            validate_not_empty(value, name, error_code or self.error_code)
        except AppError as e:
            self.add_error(e)
    
    def validate_in_range(self, value: Union[int, float], min_val: Union[int, float], 
                         max_val: Union[int, float], name: str, 
                         error_code: Optional[ErrorCode] = None):
        """
        Vérifie qu'une valeur numérique est dans une plage donnée.
        
        Args:
            value: La valeur à vérifier
            min_val: Valeur minimale (inclusive)
            max_val: Valeur maximale (inclusive)
            name: Le nom de la valeur
            error_code: Code d'erreur optionnel
        """
        try:
            validate_in_range(value, min_val, max_val, name, error_code or self.error_code)
        except AppError as e:
            self.add_error(e)
    
    def validate_matches(self, value: str, pattern: str, name: str, 
                        error_code: Optional[ErrorCode] = None):
        """
        Vérifie qu'une chaîne correspond à un pattern regex.
        
        Args:
            value: La chaîne à vérifier
            pattern: Le pattern regex
            name: Le nom de la valeur
            error_code: Code d'erreur optionnel
        """
        try:
            validate_matches(value, pattern, name, error_code or self.error_code)
        except AppError as e:
            self.add_error(e)
    
    def validate_file_exists(self, path: str, name: str, 
                            error_code: Optional[ErrorCode] = None):
        """
        Vérifie qu'un fichier existe.
        
        Args:
            path: Chemin du fichier à vérifier
            name: Le nom du paramètre
            error_code: Code d'erreur optionnel
        """
        try:
            validate_file_exists(path, name, error_code or self.error_code)
        except AppError as e:
            self.add_error(e)


@contextlib.contextmanager
def safe_resource(resource: Any, cleanup_func: Callable[[Any], None], resource_name: str,
                error_code: ErrorCode = ErrorCode.RESOURCE_BUSY_ERROR):
    """
    Gestionnaire de contexte pour assurer qu'une ressource est correctement nettoyée.
    
    Args:
        resource: La ressource à gérer
        cleanup_func: Fonction de nettoyage à appeler en sortie
        resource_name: Nom de la ressource (pour les messages d'erreur)
        error_code: Code d'erreur à utiliser pour les erreurs
        
    Yields:
        La ressource gérée
        
    Raises:
        AppError: Si une erreur survient pendant l'utilisation de la ressource
    """
    try:
        yield resource
    except Exception as e:
        # Capter toutes les exceptions
        if isinstance(e, AppError):
            # Si c'est déjà une AppError, la propager telle quelle
            cleanup_func(resource)
            raise
        else:
            # Sinon, envelopper dans une AppError
            cleanup_func(resource)
            raise AppError(
                error_code,
                f"Erreur lors de l'utilisation de la ressource {resource_name}",
                details={
                    "resource": resource_name,
                    "error": str(e)
                },
                original_exception=e
            )
    finally:
        # Assurer le nettoyage même en cas de succès
        cleanup_func(resource)
