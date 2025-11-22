# 🚀 Freeda Support - Assistant Virtuel Intelligent

Freeda est une solution de support client nouvelle génération combinant un **ChatBot IA** (Mistral AI) et une **interface de gestion pour agents**.

## 🏗️ Architecture

Le projet est divisé en deux parties distinctes :

### 1. Frontend Client (Public)
- **URL** : `https://support.freeda.com` (exemple)
- **Fonctionnalités** :
  - ChatBot intelligent (réponses automatiques)
  - Création de tickets sans compte
  - Suivi de ticket par ID
  - Canaux multiples (Chat, WhatsApp, SMS)

### 2. Backend API (FastAPI)
- **Endpoints Publics** (`/public`) : Pour le frontend client (pas d'auth)
- **Endpoints Privés** (`/private`) : Pour le dashboard admin (JWT requis)
- **Services** :
  - 🧠 **IA** : Mistral AI pour l'analyse et les réponses
  - 💾 **Base de données** : DynamoDB (AWS)
  - ⚡ **Temps réel** : WebSocket pour le chat

---

## 🚀 Démarrage Rapide

### Prérequis
- Node.js 18+
- Python 3.9+
- Docker (optionnel)
- Compte AWS (pour le déploiement)

### 1. Lancer le Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```
L'API sera accessible sur `http://localhost:8000`

### 2. Lancer le Frontend Client
```bash
npm install
npm run dev
```
Le site sera accessible sur `http://localhost:5173`

---

## 📚 Documentation

- **[Architecture détaillée](ARCHITECTURE.md)** : Vue d'ensemble technique
- **[API Documentation (Privée)](backend/docs/API_PRIVATE.md)** : Pour les développeurs du dashboard admin
- **[Guide de Déploiement](docs/archive/DEPLOY_README.md)** : Comment mettre en production

## 🛠️ Structure du Projet

```
Freeda/
├── backend/                 # API Python FastAPI
│   ├── app/
│   │   ├── routers/
│   │   │   ├── public/      # Endpoints pour le client (ChatBot)
│   │   │   └── private/     # Endpoints pour les agents (Admin)
│   │   └── services/        # Logique métier (IA, DB, Export)
│   └── docs/                # Documentation API
│
├── src/                     # Frontend React (Client)
│   ├── components/          # ChatBot, CallScreen...
│   └── pages/               # Pages publiques
│
└── infrastructure/          # Templates CloudFormation AWS
```

## 🔐 Sécurité

- **Client** : Accès public limité, protection anti-spam (à venir)
- **Admin** : Authentification JWT stricte, rôles (Agent, Manager, Admin)
- **Données** : Stockage sécurisé sur DynamoDB, chiffrement au repos

---

*Développé avec ❤️ par l'équipe SOCADY*
