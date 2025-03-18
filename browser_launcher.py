#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour ouvrir automatiquement un navigateur vers l'interface web
"""

import os
import sys
import time
import webbrowser
import json
import socket
import platform
import subprocess
from urllib.request import urlopen
from urllib.error import URLError

def is_port_open(host, port):
    """Vérifie si un port est ouvert sur le host spécifié"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)  # Timeout de 2 secondes
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def wait_for_server(host, port, max_attempts=30, interval=1):
    """Attendre que le serveur soit prêt"""
    print(f"Attente du démarrage du serveur sur {host}:{port}...")
    
    attempts = 0
    while attempts < max_attempts:
        if is_port_open(host, port):
            # Une fois que le port est ouvert, donnons un peu de temps au serveur pour s'initialiser
            time.sleep(1)
            return True
        
        time.sleep(interval)
        attempts += 1
        print(f"Tentative {attempts}/{max_attempts}...")
    
    return False

def read_config():
    """Lire la configuration pour obtenir l'hôte et le port"""
    try:
        # Essayer de lire depuis Config
        from server.config import Config
        return Config.FLASK_HOST, Config.FLASK_PORT
    except ImportError:
        # Valeurs par défaut
        return "localhost", 5000

def open_browser(url):
    """Ouvre le navigateur avec l'URL spécifiée"""
    print(f"Ouverture du navigateur à l'adresse: {url}")
    
    # Essayer d'ouvrir avec le navigateur par défaut
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"Erreur lors de l'ouverture du navigateur par défaut: {e}")
    
    # Si le navigateur par défaut échoue, essayer avec des navigateurs spécifiques
    browsers = []
    
    if platform.system() == 'Windows':
        # Chemins Windows courants
        browsers = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files\Mozilla Firefox\firefox.exe',
            r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe',
            r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
            r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        ]
    elif platform.system() == 'Darwin':  # macOS
        browsers = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Firefox.app/Contents/MacOS/firefox',
            '/Applications/Safari.app/Contents/MacOS/Safari'
        ]
    else:  # Linux
        browsers = [
            '/usr/bin/google-chrome',
            '/usr/bin/firefox',
            '/usr/bin/chromium-browser'
        ]
    
    for browser in browsers:
        if os.path.exists(browser):
            try:
                subprocess.Popen([browser, url])
                return True
            except Exception as e:
                print(f"Échec avec le navigateur {browser}: {e}")
    
    print("Impossible d'ouvrir un navigateur automatiquement.")
    print(f"Veuillez ouvrir manuellement l'URL: {url}")
    return False

def main():
    """Fonction principale"""
    # Lire la configuration
    host, port = read_config()
    
    # Construire l'URL
    if host == '0.0.0.0':
        # Si l'hôte est 0.0.0.0, utiliser localhost pour l'accès
        host = 'localhost'
    
    url = f"http://{host}:{port}"
    
    # Attendre que le serveur soit prêt
    if wait_for_server(host, port):
        print(f"Serveur démarré avec succès sur {url}")
        
        # Vérifier que l'interface web répond
        try:
            response = urlopen(url, timeout=5)
            if response.getcode() == 200:
                print("Interface web accessible, ouverture du navigateur...")
                open_browser(url)
            else:
                print(f"L'interface web répond avec le code {response.getcode()}")
        except URLError as e:
            print(f"Erreur lors de l'accès à l'interface web: {e}")
            print(f"Le serveur semble fonctionner mais l'interface n'est pas accessible.")
            print(f"Essayez d'ouvrir manuellement l'URL: {url}")
    else:
        print(f"Le serveur ne semble pas être démarré sur {url} après plusieurs tentatives.")
        print("Veuillez vérifier que le serveur est bien en cours d'exécution.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
