# ATLAS-SAV-FREE

## Vue d'ensemble de la Solution

ATLAS-SAV-FREE est une suite logicielle complète destinée à moderniser et optimiser le Service Après-Vente (SAV) de Free. Cette solution unifiée répond à deux objectifs stratégiques majeurs : fournir une assistance immédiate et intelligente aux abonnés, et offrir aux équipes internes des outils d'analyse avancés pour piloter la qualité du service.

Le projet s'articule autour de deux composantes principales :

1.  **Freeda** : Un assistant virtuel intelligent pour l'interaction client en temps réel.
2.  **Atlas Dashboard** : Une plateforme de supervision et d'analyse de données pour les analystes SAV.

---

## Composants de la Solution

### 1. Freeda (Assistant Virtuel)

Freeda est l'interface directe avec les abonnés. Il s'agit d'un agent conversationnel nouvelle génération conçu pour remplacer les analyses a posteriori par une résolution active des problèmes.

**Fonctionnalités Principales :**
*   **Interaction Temps Réel** : Communication instantanée via WebSocket.
*   **Intelligence Artificielle** : Utilisation du modèle Mistral AI pour la compréhension du langage naturel et la génération de réponses contextuelles.
*   **Analyse Sémantique** : Détection automatique du sentiment (positif, négatif, urgent) pour prioriser les demandes critiques.
*   **Architecture Cloud** : Déploiement robuste sur AWS (ECS Fargate, DynamoDB, CloudFront) assurant scalabilité et haute disponibilité.

**Technologies :** React, TypeScript, Python (FastAPI), AWS.

### 2. Atlas Dashboard (Supervision Analyste)

Atlas Dashboard est l'outil de pilotage destiné aux équipes internes. Il permet de visualiser les tendances, de surveiller la performance de l'IA et d'identifier les signaux faibles.

**Fonctionnalités Principales :**
*   **Visualisation de Données** : Tableaux de bord interactifs pour le suivi des volumes et des motifs de contact.
*   **Enrichissement IA** : Pipeline de traitement pour classifier les tickets et détecter les risques de résiliation (Churn).
*   **Exploration** : Outils de filtrage avancés pour segmenter les données et isoler des comportements spécifiques.

**Technologies :** React, TypeScript, Python (ETL & Pipelines).

---

## Architecture Globale

La solution repose sur une séparation claire des responsabilités :

*   **Dossier `Freeda/`** : Contient l'intégralité du code source de l'application chatbot (Frontend et Backend API).
*   **Dossier `Atlas_Dashboard_Analyst_SAV/`** : Contient le code source du tableau de bord analytique et des pipelines de traitement de données.

---

## Installation et Démarrage Rapide

Chaque composant dispose de sa propre documentation détaillée et de ses procédures d'installation spécifiques. Veuillez vous référer aux fichiers README respectifs pour les instructions techniques :

*   **Pour Freeda** : Consultez `Freeda/README.md`
*   **Pour Atlas Dashboard** : Consultez `Atlas_Dashboard_Analyst_SAV/README.md`

### Prérequis Généraux

Pour travailler sur l'ensemble de la solution, assurez-vous de disposer de l'environnement suivant :

*   **Node.js** (v18+)
*   **Python** (v3.9+)
*   **Git**
*   **Accès AWS** (pour les déploiements et l'accès aux services cloud)

---

## Contact et Support

Cette solution est maintenue par l'équipe de développement ATLAS. Pour toute question technique ou demande d'évolution, veuillez contacter le responsable du projet ou vous référer à la documentation interne.
