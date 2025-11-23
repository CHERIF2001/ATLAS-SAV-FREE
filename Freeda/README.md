# Freeda - Assistant Virtuel Intelligent

**Solution d'analyse et de traitement automatisé du support client Free.**

Freeda est un agent conversationnel conçu pour optimiser le traitement des demandes au service client. Il analyse sémantiquement chaque message, détecte l'émotion du client et construit une réponse contextuelle via l'IA générative Mistral AI.

---

## Accès à la Solution

| Environnement | URL | Statut |
|---------------|-----|--------|
| **Production** | [https://d7itckze71tqe.cloudfront.net](https://d7itckze71tqe.cloudfront.net) | En ligne |
| **Documentation API** | [https://d7itckze71tqe.cloudfront.net/docs](https://d7itckze71tqe.cloudfront.net/docs) | Swagger UI |

---

## Contexte et Évolution du Projet

Ce projet s'inscrit dans une démarche d'amélioration continue du Service Après-Vente (SAV) :

1.  **Phase 1 (Prototype)** : Analyse statique de fichiers d'exports (CSV/JSON) contenant des volumes importants de tweets pour identifier les tendances et les motifs de mécontentement.
2.  **Phase 2 (Solution Actuelle)** : Développement d'une application temps réel capable d'interagir directement avec les utilisateurs, remplaçant l'analyse a posteriori par une assistance immédiate et interactive.

Cette transition a permis de passer d'une observation passive des problèmes à une résolution active, soutenue par une architecture cloud robuste et scalable.

---

## Fonctionnalités Clés

- **Communication Temps Réel** : Échanges instantanés via le protocole WebSocket pour une latence minimale.
- **Intelligence Artificielle** : Intégration du modèle LLM Mistral AI pour le Traitement du Langage Naturel (NLP).
- **Analyse de Sentiment** : Détection automatique de la tonalité des messages (Positif, Négatif, Neutre, Urgent) permettant la priorisation des tickets.
- **Persistance des Données** : Sauvegarde automatique des conversations (DynamoDB côté serveur et LocalStorage côté client) assurant la continuité du service.
- **Sécurité** : Architecture sécurisée implémentant HTTPS, WAF et une Content Security Policy (CSP) stricte.

---

## Architecture Technique

### Frontend (Client)
- **Framework** : React 18 avec TypeScript
- **Outil de Build** : Vite
- **Interface Utilisateur** : TailwindCSS
- **Hébergement** : AWS S3 distribué via CloudFront (CDN)

### Backend (API)
- **Framework** : FastAPI (Python 3.9)
- **Serveur d'Application** : Uvicorn et Gunicorn
- **Infrastructure** : AWS ECS Fargate (Conteneurs Serverless)
- **Base de Données** : AWS DynamoDB (NoSQL)

---

## Guide d'Installation (Environnement Local)

### Prérequis
- Node.js version 18 ou supérieure
- Python version 3.9 ou supérieure
- AWS CLI configuré (pour l'accès aux services AWS)

### 1. Configuration du Backend

```bash
cd backend

# Création de l'environnement virtuel
python -m venv venv
# Windows :
.\venv\Scripts\activate
# Mac/Linux :
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt

# Configuration des variables d'environnement
# Créer un fichier .env dans backend/ avec les clés API nécessaires (Mistral, AWS)

# Lancement du serveur
uvicorn app.main:app --reload
```

### 2. Configuration du Frontend

```bash
# À la racine du dossier Freeda
npm install

# Créer un fichier .env.local avec la configuration suivante :
# VITE_API_URL=http://localhost:8000
# VITE_WS_URL=ws://localhost:8000

# Lancement du serveur de développement
npm run dev
```

---

## Déploiement et Maintenance

Le projet intègre des scripts PowerShell pour l'automatisation des tâches DevOps et le déploiement continu.

### Scripts Principaux

| Script | Description |
|--------|-------------|
| `.\deploy-smart.ps1` | **Déploiement complet** : Vérification de la configuration, compilation du projet React, transfert vers S3, invalidation du cache CloudFront et tests de disponibilité de l'API. |
| `.\debug-deployment.ps1` | **Diagnostic** : Analyse complète de l'état de santé de la stack technique (ECS, S3, CloudFront, API) et rapport d'erreurs. |
| `.\deploy-backend.ps1` | **Mise à jour API** : Reconstruction de l'image Docker et mise à jour du service ECS Fargate sans interruption de service. |

---

## Structure du Projet

```
Freeda/
├── backend/                 # API Python FastAPI
│   ├── app/                 # Code source de l'API
│   ├── tests/               # Tests unitaires (pytest)
│   └── infrastructure/      # Templates CloudFormation (ECS, DynamoDB)
├── src/                     # Code source React
│   ├── components/          # Composants d'interface
│   └── assets/              # Ressources statiques
├── infrastructure/          # Templates CloudFormation (Frontend S3/CloudFront)
├── public/                  # Fichiers publics
└── ...
```
