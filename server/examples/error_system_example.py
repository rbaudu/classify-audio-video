#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exemple d'utilisation du système de gestion d'erreurs.

Ce script montre comment utiliser les différentes fonctionnalités du système
de gestion d'erreurs dans l'application.
"""

import time
import logging
import random
import requests
from typing import Dict, Any, Optional

# Configurer le logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Importer les composants du système de gestion d'erreurs
from server.utils.error_handling import AppError, ErrorCode
from server.utils.error_system import (
    init_error_system, error_boundary, transaction_boundary,
    enhanced_error_handling, with_circuit_breaker, retry_with_circuit_breaker
)


# Exemple 1: Utilisation du décorateur enhanced_error_handling
@enhanced_error_handling(error_code=ErrorCode.ANALYSIS_PROCESSING_ERROR, rethrow=False)
def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Exemple de fonction traitant des données avec gestion d'erreurs améliorée.
    """
    if not data:
        raise ValueError("Les données d'entrée sont vides")
    
    # Simuler un traitement
    processed_data = {}
    for key, value in data.items():
        processed_data[key] = value * 2
    
    return processed_data


# Exemple 2: Utilisation du retry_with_circuit_breaker pour les appels réseau
@retry_with_circuit_breaker(name="api-service", max_retries=3)
def call_external_api(url: str) -> Dict[str, Any]:
    """
    Exemple de fonction appelant une API externe avec retry et circuit breaker.
    """
    response = requests.get(url, timeout=5.0)
    response.raise_for_status()  # Lève une exception si le statut n'est pas 2xx
    return response.json()


# Exemple 3: Utilisation de error_boundary pour délimiter un bloc de code
def process_batch(items: list) -> list:
    """
    Exemple de fonction traitant un lot d'items avec boundary d'erreur.
    """
    results = []
    
    for item in items:
        # Chaque item est traité dans sa propre boundary d'erreur
        with error_boundary(f"processing-item-{item}", 
                          error_code=ErrorCode.ANALYSIS_DATA_ERROR,
                          rethrow=False):
            # Simuler un traitement qui peut échouer pour certains items
            if random.random() < 0.2:  # 20% de chance d'échec
                raise ValueError(f"Erreur de traitement pour l'item {item}")
            
            # Traitement réussi
            processed_item = item * 10
            results.append(processed_item)
    
    return results


# Exemple 4: Utilisation de transaction_boundary pour les opérations atomiques
def update_database(records: list) -> bool:
    """
    Exemple de fonction mettant à jour une base de données avec transaction boundary.
    """
    def rollback_changes(error):
        """
        Fonction de rollback appelée en cas d'erreur.
        """
        print(f"Rollback des changements suite à l'erreur: {error}")
    
    try:
        with transaction_boundary("database-update", on_error_callback=rollback_changes) as tx:
            # Simuler une mise à jour de base de données
            total_records = len(records)
            tx['data']['processed'] = 0
            
            for i, record in enumerate(records):
                # Stocker l'état de la transaction
                tx['data']['processed'] = i + 1
                tx['data']['current_record'] = record
                
                # Simuler un échec aléatoire
                if random.random() < 0.1 and i > len(records) // 2:
                    raise AppError(
                        ErrorCode.DB_WRITE_ERROR,
                        f"Erreur d'écriture pour l'enregistrement {record}",
                        details={"record_index": i, "record": record}
                    )
                
                # Simuler un délai de traitement
                time.sleep(0.05)
            
            # Si on arrive ici, tout s'est bien passé
            return True
                
    except Exception:
        return False


# Exemple 5: Utilisation de la capture d'OBS avec gestion d'erreurs
class OBSCaptureWithErrorHandling:
    """
    Exemple de classe pour la capture OBS avec gestion d'erreurs intégrée.
    """
    
    def __init__(self):
        self.connection_retries = 0
        self.max_connection_retries = 5
    
    @enhanced_error_handling(error_code=ErrorCode.OBS_CONNECTION_ERROR)
    def connect(self, host: str, port: int, password: str) -> bool:
        """
        Se connecte à OBS avec gestion d'erreurs améliorée.
        """
        # Simuler une connexion qui peut échouer
        if random.random() < 0.3:  # 30% de chance d'échec
            self.connection_retries += 1
            raise AppError(
                ErrorCode.OBS_CONNECTION_ERROR,
                f"Impossible de se connecter à OBS (tentative {self.connection_retries})",
                details={"host": host, "port": port}
            )
        
        # Connexion réussie
        return True
    
    @with_circuit_breaker(name="obs-stream", failure_threshold=3, recovery_timeout=30)
    def get_stream_source(self, source_name: str) -> Dict[str, Any]:
        """
        Récupère une source de flux OBS avec circuit breaker.
        """
        # Simuler une récupération de source qui peut échouer
        if random.random() < 0.2:  # 20% de chance d'échec
            raise AppError(
                ErrorCode.OBS_STREAM_ERROR,
                f"Impossible de récupérer la source '{source_name}'",
                details={"source": source_name}
            )
        
        # Récupération réussie
        return {
            "name": source_name,
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "status": "active"
        }
    
    def capture_with_recovery(self, source_name: str) -> Optional[Dict[str, Any]]:
        """
        Exemple de capture avec mécanisme de récupération.
        """
        for attempt in range(3):
            try:
                with error_boundary(f"obs-capture-{source_name}", 
                                  error_code=ErrorCode.OBS_STREAM_ERROR):
                    # Tenter de récupérer la source
                    source = self.get_stream_source(source_name)
                    
                    # Simuler la capture d'une frame
                    frame = {
                        "timestamp": time.time(),
                        "source": source_name,
                        "data": "frame-data-placeholder"
                    }
                    
                    return frame
            except AppError as e:
                logging.warning(f"Tentative {attempt+1}/3 de capture échouée: {e.message}")
                time.sleep(1)  # Attendre avant la prochaine tentative
        
        # Toutes les tentatives ont échoué
        logging.error(f"Impossible de capturer depuis la source {source_name} après 3 tentatives")
        return None


# Exemple principal d'utilisation
def main():
    """
    Fonction principale pour démontrer l'utilisation du système de gestion d'erreurs.
    """
    # Initialiser le système de gestion d'erreurs
    init_error_system()
    
    print("\n1. Démonstration de enhanced_error_handling:")
    try:
        result = process_data({"a": 5, "b": 10})
        print(f"- Succès: {result}")
        
        # Exemple d'erreur
        result = process_data({})
        print(f"- Succès (ne devrait pas s'afficher): {result}")
    except Exception as e:
        print(f"- Exception inattendue: {e}")
    
    print("\n2. Démonstration de error_boundary:")
    items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    results = process_batch(items)
    print(f"- Résultats traités: {results}")
    print(f"- Nombre d'items traités: {len(results)} sur {len(items)}")
    
    print("\n3. Démonstration de transaction_boundary:")
    records = [f"record-{i}" for i in range(1, 21)]
    success = update_database(records)
    print(f"- Mise à jour de la base de données: {'réussie' if success else 'échouée'}")
    
    print("\n4. Démonstration de la classe OBS avec gestion d'erreurs:")
    obs = OBSCaptureWithErrorHandling()
    
    # Tentative de connexion
    connected = False
    for i in range(3):
        try:
            connected = obs.connect("localhost", 4444, "password")
            if connected:
                print("- Connecté à OBS avec succès")
                break
        except Exception as e:
            print(f"- Erreur de connexion: {e}")
    
    if connected:
        # Tentative de capture
        print("- Capture de sources:")
        sources = ["webcam", "screen", "microphone"]
        for source in sources:
            frame = obs.capture_with_recovery(source)
            if frame:
                print(f"  - Source {source} capturée: {frame['timestamp']}")
            else:
                print(f"  - Échec de capture pour la source {source}")
    
    print("\nTest du système de gestion d'erreurs terminé!")


if __name__ == "__main__":
    main()
