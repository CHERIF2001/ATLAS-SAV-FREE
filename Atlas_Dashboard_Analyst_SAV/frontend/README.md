# SAV Dashboard Frontend

Ce projet est le frontend du dashboard d'analyse de tweets SAV pour Free Mobile.
Il est construit avec React, TypeScript, Tailwind CSS, Shadcn UI et Recharts.

## Prérequis

- Node.js (v18+)
- npm

## Installation

1. Naviguez dans le dossier `frontend` :
   ```bash
   cd frontend
   ```

2. Installez les dépendances :
   ```bash
   npm install
   ```

## Démarrage

Pour lancer le serveur de développement :

```bash
npm run dev
```

L'application sera accessible à l'adresse indiquée dans le terminal (généralement http://localhost:5173).

## Structure du projet

- `/src/components` : Composants UI réutilisables et graphiques
- `/src/pages` : Pages principales (Analytics, Sentiment)
- `/src/services` : Service API (mock)
- `/src/lib` : Utilitaires
- `/src/hooks` : Hooks personnalisés

## Fonctionnalités

- **Analytics SAV** : KPIs, Nuage de mots, Histogrammes, Analyse de Churn
- **Analyse Sentiment** : Heatmap, Distribution, Pics d'activité
