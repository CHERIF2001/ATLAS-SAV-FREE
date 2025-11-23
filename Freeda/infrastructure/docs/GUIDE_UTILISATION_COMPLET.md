# 📱 Guide d'Utilisation - Freeda Support App

**Application de Support Client Multi-Canal pour Free**  
Version 1.0.0 - Déployée sur AWS

---

## 🎯 Vue d'Ensemble

**Freeda** est une application de support client innovante qui permet aux utilisateurs de Free de contacter le service client via **5 canaux différents** :

1. **📞 Appel Vocal** (avec assistant vocal IA)
2. **💬 Chat en Direct** (avec chatbot IA Mistral)
3. **📱 SMS** (redirection vers l'app de messagerie)
4. **💚 WhatsApp** (redirection vers WhatsApp)
5. **📧 Email** (demande formelle)

---

## 🏗️ Architecture de l'Application

### Frontend (Interface Utilisateur)
- **Technologie** : React + TypeScript + Vite
- **UI Framework** : Shadcn/ui (composants modernes)
- **Hébergement** : AWS S3 + CloudFront
- **URL** : https://d7itckze71tqe.cloudfront.net

### Backend (API)
- **Technologie** : Python FastAPI
- **Hébergement** : AWS ECS Fargate (conteneurs Docker)
- **Base de données** : DynamoDB
- **IA** : Mistral AI (génération de réponses)
- **URL API** : http://freeda-alb-production-1511177887.eu-west-3.elb.amazonaws.com

---

## 📖 Guide d'Utilisation Détaillé

### Page d'Accueil

Lorsque l'utilisateur arrive sur l'application, il voit :

1. **Logo Free** en haut
2. **Titre** : "Contactez le support Free"
3. **Badge "Service disponible 24/7"**
4. **5 boutons de canal** :
   - 📞 Appeler
   - 💬 Écrire un message
   - 📱 SMS (désactivé sur desktop)
   - 💚 WhatsApp
   - 📧 Email (Demande formelle)
5. **Checkbox RGPD** (obligatoire avant de continuer)

#### ⚠️ Règle Importante
L'utilisateur **DOIT cocher la case RGPD** avant de pouvoir utiliser n'importe quel canal. Sinon, une alerte s'affiche.

---

## 🔄 Flux d'Utilisation par Canal

### 1️⃣ Canal : Appel Vocal (📞 Appeler)

#### Étape 1 : Confirmation
- L'utilisateur clique sur "Appeler"
- Une popup de confirmation s'affiche :
  - **Titre** : "Confirmation d'appel"
  - **Message** : "Votre demande sera traitée par l'assistant vocal de Free..."
  - **Boutons** : "Annuler" ou "Continuer"

#### Étape 2 : Écran d'Appel
Si l'utilisateur clique sur "Continuer", il est redirigé vers l'écran d'appel (`CallScreen.tsx`) :

**Phase 1 : Connexion (10 secondes)**
- Affichage : "Patientez, connexion à notre assistant vocal"
- Spinner de chargement
- Compte à rebours : 10 → 0 secondes

**Phase 2 : Appel en cours**
- Affichage : "Voice Calling..."
- Timer qui monte : 00:00 → 00:30...
- Animation d'ondes sonores (20 barres animées)
- **Reconnaissance vocale automatique** (Web Speech API)
  - L'utilisateur peut parler directement
  - L'IA détecte les mots-clés : "réseau", "facture", "offre"

**Phase 3 : IA répond (après 30 secondes)**
- Affichage : "Connecté avec l'assistant vocal de Free"
- L'IA dit : "Bonjour ! Je suis l'assistant virtuel de Free. Comment puis-je vous aider aujourd'hui ?"
- **Synthèse vocale** (Text-to-Speech)
- L'utilisateur peut continuer à parler
- L'IA répond en fonction du sujet détecté :
  - **Réseau** → "Je vois un souci de réseau. Souhaitez-vous diagnostiquer la box, le Wi‑Fi ou la ligne ?"
  - **Facture** → "Concernant votre facture, je peux vous aider..."
  - **Offre** → "Pour nos offres, préférez‑vous des informations sur le mobile..."

#### Contrôles Disponibles
- **🎤 Mute/Unmute** : Couper/activer le micro
- **⏸️ Pause** : Mettre en pause la synthèse vocale
- **📞 Raccrocher** : Terminer l'appel et revenir à l'accueil

#### Technologies Utilisées
- **Web Speech API** (reconnaissance vocale navigateur)
- **SpeechSynthesis API** (synthèse vocale navigateur)
- **Détection de mots-clés** (pas de connexion backend pour l'appel)

---

### 2️⃣ Canal : Chat en Direct (💬 Écrire un message)

#### Étape 1 : Ouverture du Chat
- L'utilisateur clique sur "Écrire un message"
- Redirection vers l'écran de chat (`ChatBot.tsx`)

#### Étape 2 : Interface de Chat

**En-tête**
- Logo "F" (Free)
- Titre : "Free - Assistant virtuel"
- Bouton "←" pour revenir
- Bouton "✕" pour fermer le ticket (si ticket ouvert)

**Zone de Messages**
- Message de bienvenue automatique :
  > "Bonjour ! Je suis l'assistant virtuel de Free. Décrivez votre problème et je vous aiderai à le résoudre."

**Boutons Rapides** (affichés au début)
- 📶 Problème réseau
- 🧾 Facture
- 📋 Infos offre
- ❓ Autre demande

**Zone de Saisie**
- 🎤 Bouton micro (enregistrement vocal - simulation)
- 📝 Champ de texte : "Écrire ici..."
- ➤ Bouton envoyer

#### Étape 3 : Création d'un Ticket

**Premier message de l'utilisateur**
- L'utilisateur tape un message (ex: "Ma connexion internet ne fonctionne pas")
- Le message s'affiche immédiatement (Optimistic UI)
- Un message "Analyse en cours..." apparaît
- **Appel API** : `POST /public/tickets`
  ```json
  {
    "initial_message": "Ma connexion internet ne fonctionne pas"
  }
  ```
- Le backend :
  1. Crée un ticket dans DynamoDB
  2. Génère un `ticket_id` unique
  3. Envoie le message à Mistral AI
  4. Reçoit une réponse de l'IA
  5. Stocke la réponse dans le ticket
  6. Retourne le `ticket_id`

**Réponse de l'IA**
- Le message "Analyse en cours..." est remplacé par la réponse de Mistral AI
- Exemple de réponse :
  > "Je comprends que vous rencontrez un problème de connexion internet. Voici quelques étapes pour diagnostiquer :
  > 
  > 1. Vérifiez que votre box est bien allumée
  > 2. Redémarrez votre box en la débranchant 30 secondes
  > 3. Vérifiez les câbles
  > 
  > -- Agent Free"

#### Étape 4 : Conversation Continue

**Messages suivants**
- L'utilisateur peut continuer à envoyer des messages
- **Appel API** : `POST /public/tickets/{ticket_id}/messages`
  ```json
  {
    "message": "J'ai redémarré la box mais ça ne fonctionne toujours pas"
  }
  ```
- L'IA répond en tenant compte de l'historique de la conversation

**WebSocket en Temps Réel**
- Une connexion WebSocket est établie : `ws://[backend-url]/ws/{ticket_id}`
- Les nouveaux messages arrivent automatiquement sans rafraîchir la page
- Types de messages WebSocket :
  - `new_message` : Nouveau message (utilisateur ou IA)
  - `ticket_snapshot` : Historique complet du ticket
  - `status_updated` : Changement de statut du ticket

#### Étape 5 : Fermeture du Ticket

**Bouton "✕" dans l'en-tête**
- L'utilisateur clique sur "✕"
- Popup de confirmation :
  - **Titre** : "Fermer le ticket"
  - **Message** : "Êtes-vous sûr de vouloir fermer ce ticket ? Vous ne pourrez plus envoyer de messages après la fermeture."
  - **Boutons** : "Annuler" ou "Fermer le ticket"

**Après fermeture**
- **Appel API** : `PATCH /public/tickets/{ticket_id}/status`
  ```json
  {
    "status": "fermé"
  }
  ```
- Badge "Fermé" affiché dans l'en-tête
- Zone de saisie désactivée avec message : "Ce ticket est fermé. Vous ne pouvez plus envoyer de messages."
- Message automatique : "Ce ticket a été fermé. Merci d'avoir contacté le support Free."

#### Fonctionnalités Avancées

**Formatage Markdown**
Les réponses de l'IA supportent le markdown :
- `**texte**` → **texte en gras**
- `*texte*` → *texte en italique*
- `- item` → Liste à puces
- `1. item` → Liste numérotée
- `-- Agent Free` → Signature stylisée (séparée par une ligne)

**Bouton Micro** 🎤
- Simulation d'enregistrement vocal
- Animation de points rouges pulsants
- Message "Enregistrement en cours..."
- Envoie "Message vocal enregistré" (fonctionnalité de démonstration)

---

### 3️⃣ Canal : SMS (📱)

#### Comportement
- **Sur Desktop** : Bouton grisé avec mention "(Mobile uniquement)"
- **Sur Mobile** : Bouton actif

#### Flux
1. L'utilisateur clique sur "SMS"
2. Popup de confirmation :
   - **Titre** : "Redirection SMS"
   - **Message** : "Vous allez être redirigé vers votre application de messagerie..."
3. Si confirmé :
   - Ouverture de l'app SMS native avec :
     - **Destinataire** : +33666078215
     - **Message pré-rempli** : "Bonjour, je souhaite contacter le support Free. Pouvez-vous m'aider ?"

---

### 4️⃣ Canal : WhatsApp (💚)

#### Flux
1. L'utilisateur clique sur "WhatsApp"
2. Popup de confirmation :
   - **Titre** : "Redirection WhatsApp"
   - **Message** : "Vous allez être redirigé vers WhatsApp..."
3. Si confirmé :
   - **Sur Mobile** : Ouverture de l'app WhatsApp
   - **Sur Desktop** : Ouverture de WhatsApp Web
   - **Destinataire** : +33634374398
   - **Message pré-rempli** : "Bonjour, je souhaite contacter le support Free. Pouvez-vous m'aider ?"

---

### 5️⃣ Canal : Email (📧)

#### Flux
1. L'utilisateur clique sur "Email (Demande formelle)"
2. Popup de confirmation :
   - **Titre** : "Redirection Email"
   - **Message** : "Vous allez être redirigé vers votre client email..."
3. Si confirmé :
   - Ouverture du client email par défaut avec :
     - **Destinataire** : support@free.fr
     - **Sujet** : "Demande de support - Contact SAV"
     - **Corps** : Modèle pré-rempli avec sections :
       - Détails de la demande
       - Informations de contact
       - Numéro de client

---

## 🔧 Fonctionnalités Techniques

### Gestion des États
- **Page d'accueil** : `currentScreen = 'home'`
- **Appel en cours** : `currentScreen = 'call'`
- **Chat en cours** : `currentScreen = 'chat'`

### Stockage des Données

**Backend (DynamoDB)**
```json
{
  "ticket_id": "uuid-v4",
  "status": "en cours" | "fermé",
  "created_at": "2025-11-23T12:00:00Z",
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user" | "assistant",
      "content": "Texte du message",
      "timestamp": "2025-11-23T12:01:00Z"
    }
  ],
  "sentiment": "neutre" | "positif" | "négatif",
  "category": "technique" | "facturation" | "autre"
}
```

### API Endpoints Utilisés

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/public/tickets` | Créer un nouveau ticket |
| `POST` | `/public/tickets/{id}/messages` | Ajouter un message |
| `PATCH` | `/public/tickets/{id}/status` | Changer le statut |
| `WS` | `/ws/{ticket_id}` | WebSocket temps réel |
| `GET` | `/health` | Health check |

---

## 🎨 Design et UX

### Couleurs
- **Primaire** : Rouge Free (#D40000)
- **Fond** : Blanc / Gris clair
- **Messages utilisateur** : Rouge (primaire)
- **Messages IA** : Gris clair

### Responsive
- **Mobile-first** : Optimisé pour mobile
- **Desktop** : Largeur max 448px (centrée)
- **Adaptation** : SMS désactivé sur desktop

### Animations
- **Ondes sonores** : 20 barres animées (appel vocal)
- **Loader** : Spinner + "Analyse en cours..."
- **Micro** : Points rouges pulsants
- **Transitions** : Smooth scroll vers le bas des messages

---

## 🔐 Sécurité et Confidentialité

### RGPD
- **Consentement obligatoire** avant toute interaction
- **Lien vers politique** : https://free.fr/politique-confidentialite/conservation-donnees-freeda
- **Message** : "J'accepte que mes données personnelles soient traitées..."

### Données Collectées
- Messages de l'utilisateur
- Horodatage des interactions
- Sentiment détecté (par l'IA)
- Catégorie du problème

### Stockage
- **DynamoDB** : Chiffrement au repos
- **WebSocket** : Connexion sécurisée
- **Pas de stockage local** : Tout est côté serveur

---

## 🚀 Performance

### Optimisations
- **Optimistic UI** : Messages affichés immédiatement
- **WebSocket** : Mises à jour temps réel sans polling
- **CloudFront CDN** : Latence minimale mondiale
- **Lazy Loading** : Composants chargés à la demande

### Temps de Réponse
- **Création ticket** : ~2-3 secondes
- **Réponse IA** : ~3-5 secondes (Mistral AI)
- **WebSocket** : Instantané (<100ms)

---

## 🐛 Gestion des Erreurs

### Erreurs Réseau
- **Message** : "Désolé, je ne parviens pas à contacter le serveur."
- **Affichage** : Dans la bulle de message
- **Retry** : L'utilisateur peut renvoyer le message

### Erreurs API
- **400 Bad Request** : "Requête invalide"
- **404 Not Found** : "Ticket introuvable"
- **500 Server Error** : "Erreur serveur"

### Fallbacks
- **WebSocket déconnecté** : Reconnexion automatique
- **Speech API non supportée** : Désactivation silencieuse
- **Image manquante** : Fallback vers placeholder

---

## 📊 Analytics (Backend)

### Données Analysées
- **Sentiment** : Positif, Neutre, Négatif (via Mistral AI)
- **Catégorie** : Technique, Facturation, Offre, Autre
- **Durée** : Temps de résolution du ticket
- **Satisfaction** : Basée sur le sentiment

### Utilisation
- Tableau de bord admin (non inclus dans cette version)
- Export des données
- Statistiques temps réel

---

## 🔄 Workflow Complet - Exemple

### Scénario : Problème de Connexion Internet

1. **Utilisateur arrive sur le site**
   - URL : https://d7itckze71tqe.cloudfront.net
   - Voit la page d'accueil avec les 5 canaux

2. **Accepte le RGPD**
   - Coche la case de consentement

3. **Choisit le Chat**
   - Clique sur "💬 Écrire un message"
   - Redirigé vers l'interface de chat

4. **Envoie le premier message**
   - Tape : "Ma connexion internet ne fonctionne pas depuis ce matin"
   - Clique sur ➤ ou appuie sur Entrée

5. **Backend traite**
   - Crée un ticket avec ID unique
   - Envoie à Mistral AI
   - Reçoit une réponse structurée

6. **IA répond**
   - Affiche une réponse avec étapes de diagnostic
   - Propose des solutions

7. **Conversation continue**
   - L'utilisateur suit les étapes
   - Envoie des messages de suivi
   - L'IA adapte ses réponses

8. **Problème résolu**
   - L'utilisateur clique sur "✕"
   - Confirme la fermeture
   - Ticket marqué comme "fermé"

9. **Retour à l'accueil**
   - Clique sur "←"
   - Peut créer un nouveau ticket si besoin

---

## 🎓 Cas d'Usage

### Cas 1 : Utilisateur Pressé
- **Canal** : Appel vocal
- **Avantage** : Réponse immédiate, mains libres
- **Limitation** : Reconnaissance vocale navigateur (pas toujours précise)

### Cas 2 : Utilisateur Détaillé
- **Canal** : Chat
- **Avantage** : Historique écrit, réponses structurées
- **Limitation** : Nécessite de taper

### Cas 3 : Utilisateur Mobile
- **Canal** : WhatsApp ou SMS
- **Avantage** : Utilise l'app préférée
- **Limitation** : Sort de l'application Freeda

### Cas 4 : Demande Officielle
- **Canal** : Email
- **Avantage** : Trace écrite formelle
- **Limitation** : Pas de réponse immédiate

---

## 🛠️ Maintenance et Support

### Logs
- **Frontend** : Console navigateur (`console.log`, `console.error`)
- **Backend** : CloudWatch Logs (`/ecs/freeda-production`)

### Monitoring
- **Health Check** : http://[backend-url]/health
- **Métriques ECS** : CPU, Memory, Task Count
- **CloudFront** : Latence, Erreurs 4xx/5xx

### Mises à Jour
1. **Frontend** : `npm run build` + `.\deploy-frontend-app.ps1`
2. **Backend** : `.\redeploy-backend.ps1`

---

## 📞 Support Technique

### Problèmes Courants

**Le chat ne répond pas**
- Vérifier que le backend est accessible
- Tester : `curl http://[backend-url]/health`
- Vérifier les logs CloudWatch

**WebSocket déconnecté**
- Vérifier la connexion réseau
- Le WebSocket se reconnecte automatiquement

**L'appel vocal ne fonctionne pas**
- Vérifier que le navigateur supporte Web Speech API
- Autoriser l'accès au microphone
- Fonctionne mieux sur Chrome/Edge

---

## 🎉 Conclusion

**Freeda** est une application de support client moderne et complète qui offre une expérience utilisateur fluide sur 5 canaux différents. L'intégration de l'IA Mistral permet des réponses pertinentes et contextuelles, tandis que l'architecture AWS garantit scalabilité et disponibilité 24/7.

**Points Forts** :
- ✅ Multi-canal (5 options)
- ✅ IA conversationnelle (Mistral)
- ✅ Temps réel (WebSocket)
- ✅ Interface moderne et responsive
- ✅ Déployé sur AWS (production-ready)

**URL de Production** : https://d7itckze71tqe.cloudfront.net

---

*Guide créé le 23 novembre 2025 - Version 1.0.0*
