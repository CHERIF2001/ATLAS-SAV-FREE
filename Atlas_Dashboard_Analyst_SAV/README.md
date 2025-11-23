# ATLAS Dashboard Analyst SAV

**Outil de supervision et d'analyse des données SAV Free.**

Ce tableau de bord permet aux analystes de visualiser les tendances, de surveiller la qualité des réponses de l'IA et d'explorer les données enrichies (sentiments, motifs de churn, pics d'activité).

---

## Fonctionnalités Clés

- **📊 Visualisation de Données** : Graphiques interactifs (Histogrammes, Heatmaps, Nuages de mots) pour comprendre les volumes et les motifs.
- **🧠 Analyse IA** : Pipeline d'enrichissement utilisant Mistral AI pour classifier les tweets et détecter les sentiments.
- **🔍 Exploration** : Interface de filtrage avancée pour isoler des segments spécifiques (ex: "Clients mécontents le week-end").
- **📉 Détection de Churn** : Analyse spécifique des menaces de résiliation.

---

## Architecture Technique

### Frontend
- **Framework** : React 18 + TypeScript
- **Build** : Vite
- **UI** : TailwindCSS + Shadcn/UI (Composants `ui/`)
- **Charts** : Recharts (supposé) / Composants personnalisés

### Backend / Pipeline
- **Langage** : Python 3.9+
- **Logique** : Scripts d'ETL et d'enrichissement (`pipeline_enrichment.py`)
- **IA** : Client Mistral AI pour la classification (`llm_classification.py`)
- **Données** : Traitement de fichiers Parquet/CSV

---

## Guide d'Installation

### 1. Backend & Pipeline Python

```bash
# À la racine du dossier Dashboard
python -m venv venv
# Windows :
.\venv\Scripts\activate
# Mac/Linux :
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt

# Lancer le pipeline d'enrichissement (exemple)
python main.py
```

### 2. Frontend React

```bash
cd frontend

# Installation
npm install

# Lancement serveur de dev
npm run dev
```
> L'interface sera accessible sur `http://localhost:5173`

---

## Structure du Projet

```
Atlas_Dashboard_Analyst_SAV/
├── backend/                 # Logique métier Python
│   ├── services/            # Modules de nettoyage et classification
│   └── ...
├── frontend/                # Interface Utilisateur React
│   ├── src/
│   │   ├── components/      # Graphiques et filtres
│   │   ├── pages/           # Pages (Analytics, Sentiment, Data)
│   │   └── ui/              # Composants de base (Boutons, Cards...)
│   └── ...
├── tests/                   # Tests de robustesse et qualité
└── main.py                  # Point d'entrée du script d'analyse
```

---

## Tests

Le projet inclut une suite de tests pour valider la robustesse du pipeline IA :

```bash
# Lancer les tests
pytest tests/
```
