# Architecture JavaScript

## Introduction

L'interface utilisateur de Classify Audio Video utilise une architecture JavaScript modulaire pour améliorer la maintenabilité, la testabilité et les performances. Cette approche divise les fonctionnalités en modules spécialisés qui sont chargés de manière asynchrone lorsqu'ils sont nécessaires.

## Principes architecturaux

- **Séparation des responsabilités** : Chaque module gère un aspect spécifique de l'application
- **Faible couplage** : Les modules communiquent via des interfaces bien définies
- **Chargement asynchrone** : Les modules sont chargés uniquement lorsqu'ils sont nécessaires
- **Namespaces globaux** : Chaque module s'exporte dans l'espace global `window` sous un nom unique
- **Réutilisabilité** : Les modules sont conçus pour être réutilisables dans différents contextes

## Structure des modules

### Page de test du modèle (`model_testing.js`)

La page de test du modèle est divisée en quatre modules principaux :

#### 1. Module de flux vidéo (`video-feed.js`)
Responsable de l'affichage et de la gestion des flux vidéo en direct :
- Initialisation et affichage du flux vidéo 
- Vérification périodique de l'état de la capture
- Affichage des messages d'erreur et des indicateurs d'état
- Gestion des mises à jour d'images via l'API de snapshot

#### 2. Module de visualisation audio (`audio-visualizer.js`)
Gère la visualisation et le traitement des flux audio :
- Création d'un visualiseur graphique pour l'audio
- Simulation d'un analyseur de spectre audio
- Contrôles pour couper/activer le son
- Génération de caractéristiques audio pour l'analyse

#### 3. Module de classification (`classification.js`)
Analyse les données audio/vidéo et génère des classifications d'activité :
- Traitement des caractéristiques extraites
- Classification des activités basée sur les données
- Affichage des résultats avec niveaux de confiance
- Mise à jour automatique des classifications à intervalle régulier

#### 4. Module d'informations sur le modèle (`model-info.js`)
Gère les informations et les opérations relatives au modèle :
- Affichage des statistiques du modèle (précision, dernière mise à jour)
- Fonctionnalités d'entraînement et de réentraînement
- Export et import de modèles
- Gestion des paramètres du modèle

### Page de statistiques (`statistics.js`)

La page de statistiques utilise également une architecture modulaire avec quatre composants principaux :

#### 1. Module de chargement de données (`data-loader.js`)
Responsable de la récupération et de la mise en cache des données statistiques :
- Chargement des données depuis l'API pour différentes périodes
- Mise en cache des résultats pour éviter des appels réseau inutiles
- Simulation de données en cas d'indisponibilité de l'API
- Gestion des états de chargement et d'erreur

#### 2. Module de gestion des graphiques (`chart-manager.js`)
Crée et met à jour les différents graphiques statistiques :
- Graphique en camembert pour la répartition des activités
- Graphique à barres pour la durée par activité
- Graphique empilé pour la distribution horaire
- Graphique linéaire pour les tendances d'activité
- Adaptation des graphiques à la période sélectionnée

#### 3. Module d'exportation (`export-manager.js`)
Gère l'exportation des données statistiques dans différents formats :
- Export au format CSV avec sections structurées
- Export au format JSON pour les données brutes
- Préparation pour l'export PDF (à venir)
- Téléchargement direct des fichiers générés

#### 4. Module de résumé (`summary-manager.js`)
Met à jour l'affichage des résumés statistiques :
- Calcul et affichage de l'activité principale
- Identification de l'activité la plus fréquente
- Calcul du temps actif vs temps total
- Formatage des durées et pourcentages pour une meilleure lisibilité

## Mécanisme de chargement des modules

Chaque page principale (`model_testing.js` et `statistics.js`) implémente un mécanisme de chargement dynamique des modules :

```javascript
// Exemple du mécanisme de chargement dans model_testing.js
document.addEventListener('DOMContentLoaded', function() {
    // Liste des modules à charger
    const moduleUrls = [
        '/static/js/modules/video-feed.js',
        '/static/js/modules/audio-visualizer.js',
        '/static/js/modules/classification.js',
        '/static/js/modules/model-info.js'
    ];
    
    let modulesLoaded = 0;
    
    // Fonction à exécuter une fois tous les modules chargés
    const initApp = () => {
        ModelTesting.init();
    };
    
    // Charger chaque module de manière asynchrone
    moduleUrls.forEach(url => {
        const script = document.createElement('script');
        script.src = url;
        script.onload = () => {
            modulesLoaded++;
            if (modulesLoaded === moduleUrls.length) {
                initApp();
            }
        };
        script.onerror = (error) => {
            console.error(`Erreur lors du chargement du module ${url}:`, error);
            modulesLoaded++;
            if (modulesLoaded === moduleUrls.length) {
                initApp();
            }
        };
        document.head.appendChild(script);
    });
});
```

Ce mécanisme garantit que :
1. Les modules sont chargés de manière asynchrone pour ne pas bloquer le rendu de la page
2. L'application n'est initialisée que lorsque tous les modules sont chargés
3. L'application peut démarrer même si certains modules n'ont pas pu être chargés (dégradation gracieuse)

## Communication entre modules

Les modules communiquent principalement via :

1. **Exposition globale** : Chaque module s'expose dans l'espace `window`
   ```javascript
   // Exposition d'un module
   window.VideoFeed = VideoFeed;
   ```

2. **Appels directs** : Les modules peuvent s'appeler directement
   ```javascript
   // Appel du module AudioVisualizer depuis le module Classification
   if (window.AudioVisualizer) {
       this.state.audioFeatures = window.AudioVisualizer.generateFeatures();
   }
   ```

3. **Fonctions de rappel (callbacks)** : Utilisées pour les opérations asynchrones
   ```javascript
   // Utilisation de callbacks dans DataLoader
   window.DataLoader.loadData(
       this.state.currentPeriod,
       this.onDataLoadSuccess.bind(this),
       this.onDataLoadError.bind(this)
   );
   ```

## Avantages de cette architecture

1. **Fichiers plus petits** : Réduit la taille des fichiers individuels pour une meilleure maintenabilité
2. **Chargement à la demande** : Optimise les performances en ne chargeant que ce qui est nécessaire
3. **Testabilité améliorée** : Les modules peuvent être testés individuellement
4. **Développement parallèle** : Plusieurs développeurs peuvent travailler sur différents modules simultanément
5. **Évolutivité** : Facilite l'ajout de nouvelles fonctionnalités sans toucher au code existant
6. **Dégradation gracieuse** : L'application peut continuer à fonctionner même si certains modules échouent

## Bonnes pratiques pour étendre l'architecture

Si vous souhaitez étendre ou modifier l'architecture JavaScript, voici quelques bonnes pratiques à suivre :

1. **Respecter la séparation des responsabilités** : Créez de nouveaux modules pour de nouvelles fonctionnalités distinctes
2. **Documenter les interfaces** : Documentez clairement les méthodes et propriétés que d'autres modules peuvent utiliser
3. **Gérer les erreurs** : Implémentez une gestion robuste des erreurs dans chaque module
4. **Vérifier les dépendances** : Avant d'utiliser une fonctionnalité d'un autre module, vérifiez qu'il est disponible
5. **Éviter les références circulaires** : Structurez les dépendances entre modules de manière hiérarchique
6. **Maintenir l'état local** : Chaque module doit gérer son propre état dans un objet `state`
7. **Fournir des méthodes d'initialisation et de nettoyage** : Chaque module doit avoir des méthodes `init()` et `stop()`

## Tests des modules

Pour tester l'architecture modulaire, vous pouvez :

1. **Tests unitaires** : Testez chaque module individuellement en simulant ses dépendances
2. **Tests d'intégration** : Testez l'interaction entre plusieurs modules
3. **Tests de chargement** : Vérifiez que les modules se chargent correctement, même dans des conditions réseau dégradées
4. **Tests de robustesse** : Simulez des échecs de modules pour vérifier la dégradation gracieuse
