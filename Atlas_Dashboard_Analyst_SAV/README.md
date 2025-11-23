# ATLAS Analytics - Analyse de Tweets Free

Dashboard professionnel d'analyse de tweets clients avec enrichissement LLM et visualisations avancées.

## 🚀 Fonctionnalités

### Pipeline de traitement
- ✅ Nettoyage complet des tweets (RT, doublons, URLs, mentions, emojis)
- ✅ **Filtrage automatique des tweets Free** (exclusion des comptes contenant "free")
- ✅ Détection automatique de langue et traduction vers français
- ✅ Normalisation et préprocessing avec spaCy (lemmatisation, stopwords)
- ✅ Enrichissement LLM avec Mistral (motif, sentiment, urgence, risque churn)
- ✅ Parsing sécurisé des réponses LLM avec fallback intelligent
- ✅ Traitement par batches avec retry automatique
- ✅ Sauvegarde incrémentale et reprise en cas d'erreur

### Dashboard Streamlit
- 📊 **Dashboard général**: KPIs, évolution temporelle, nuage de mots, heatmaps
- 🎯 **Analyse par motif**: Matrices croisées, volumes, urgence et churn par thème
- 📋 **Liste des tweets**: Tableau interactif avec filtres avancés et badges colorés

## 📁 Structure du projet

```
ATLAS-analytics/
├── data/
│   ├── raw/              # Fichiers CSV bruts
│   └── processed/        # Données enrichies (parquet)
├── src/
│   ├── cleaning.py       # Nettoyage et préprocessing
│   ├── llm_classification.py  # Classification LLM
│   ├── parse_llm_outputs.py   # Parsing sécurisé
│   ├── pipeline_enrichment.py # Pipeline complet
│   ├── utils.py          # Utilitaires
│   └── config.py         # Configuration
├── app/
│   ├── streamlit_app.py  # App principale
│   ├── pages/
│   │   ├── 01_Dashboard.py
│   │   ├── 02_Analyse_par_motif.py
│   │   └── 03_Liste_des_tweets.py
│   └── assets/
│       └── free_logo.png
├── main.py               # Script d'exécution
├── requirements.txt
└── README.md
```

## 🛠️ Installation

### 1. Cloner le projet et installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Installer le modèle spaCy français

```bash
python -m spacy download fr_core_news_sm
```

### 3. Configuration de l'API Mistral

Créez un fichier `.env` à la racine du projet :

```env
MISTRAL_API_KEY=votre_clé_api_mistral
MISTRAL_MODEL=mistral-medium-latest
```

Obtenez votre clé API sur [Mistral AI](https://console.mistral.ai/)

### 4. Préparer les données

Placez votre fichier CSV de tweets dans `data/raw/free_tweet_export.csv`

Le CSV doit contenir au minimum une colonne avec le texte des tweets (par défaut `full_text`).

## 📊 Utilisation

### Exécuter le pipeline complet

```bash
python main.py
```

Options disponibles :
- `--input`: Chemin vers le fichier CSV d'entrée
- `--output`: Chemin vers le fichier de sortie
- `--checkpoint`: Chemin vers le fichier checkpoint
- `--text-col`: Nom de la colonne texte (défaut: `full_text`)

Exemple :
```bash
python main.py --input data/raw/mes_tweets.csv --text-col tweet_text
```

### Lancer le dashboard Streamlit

```bash
streamlit run app/streamlit_app.py
```

Le dashboard sera accessible sur `http://localhost:8501`

## 🎨 Fonctionnalités du Dashboard

### Page 1: Dashboard Général
- **KPIs**: Total tweets, répartition sentiment, tweets urgents, risque churn
- **Évolution temporelle**: Sentiments et churn par semaine
- **Volumes**: Par jour et par semaine
- **Répartition par thème**: Graphiques en barres
- **Nuage de mots**: Mots-clés des tweets négatifs
- **Heatmap**: Croisement motif × sentiment

### Page 2: Analyse par Motif
- **Matrice motif × sentiment**: Visualisation croisée
- **Volumes par motif**: Graphiques comparatifs
- **Urgence par motif**: Répartition des niveaux d'urgence
- **Churn par motif**: Identification des thèmes à risque
- **Détails par motif**: KPIs et évolution temporelle

### Page 3: Liste des Tweets
- **Tableau interactif**: Affichage HTML custom avec badges
- **Filtres avancés**: Client, motif, sentiment, urgence, churn, date
- **Export CSV**: Téléchargement des résultats filtrés

## 🔧 Configuration

Modifiez `src/config.py` pour ajuster :
- Chemins des fichiers
- Modèle Mistral utilisé
- Taille des batches LLM
- Couleurs du dashboard
- Colonnes attendues dans le CSV

## 📝 Notes importantes

### Performance
- Le traitement LLM peut être long pour de gros volumes
- Les checkpoints permettent de reprendre en cas d'interruption
- Les batches sont traités avec des pauses pour éviter les rate limits

### Coûts API
- L'utilisation de Mistral API génère des coûts
- Surveillez votre consommation sur le dashboard Mistral
- Utilisez `mistral-small` pour réduire les coûts (moins précis)

### Données
- Les données nettoyées sont sauvegardées en parquet (format efficace)
- Les réponses LLM brutes sont conservées pour debug
- Les colonnes enrichies: `motif`, `sentiment`, `urgence`, `risque_churn`, `is_churn_risk`

## 🐛 Dépannage

### Erreur "MISTRAL_API_KEY non définie"
- Vérifiez que le fichier `.env` existe et contient la clé
- Ou définissez la variable d'environnement directement

### Erreur "Modèle spaCy non trouvé"
```bash
python -m spacy download fr_core_news_sm
```

### Erreur de traduction
- Vérifiez votre connexion internet
- Le module `deep-translator` utilise Google Translate (gratuit mais avec limites)

### Dashboard ne charge pas les données
- Vérifiez que le pipeline a été exécuté
- Le fichier doit être dans `data/processed/tweets_enriched.parquet`

## 📄 Licence

Ce projet est fourni à des fins éducatives et professionnelles.

## 👥 Auteur

Projet développé par l'équipe SOCADY pour l'analyse de tweets clients de Free.

