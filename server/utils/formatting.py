"""
Fonctions utilitaires de formatage
"""

def format_time(seconds):
    """
    Formate un temps en secondes en format lisible (HH:MM:SS ou MM:SS)
    
    Args:
        seconds (int): Temps en secondes
        
    Returns:
        str: Temps formaté (HH:MM:SS ou MM:SS)
        
    Raises:
        ValueError: Si seconds est négatif
    """
    if seconds < 0:
        raise ValueError("Le temps en secondes ne peut pas être négatif")
    
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"
