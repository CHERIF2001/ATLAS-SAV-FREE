# 🎯 Prochaines étapes - Guide d'utilisation

## ✅ État actuel

- ✅ **Données nettoyées** : 3,035 tweets clients (fichier `tweets_cleaned.parquet`)
- ❌ **Données enrichies** : Pas encore (besoin de l'enrichissement LLM)

## 🚀 Étape suivante : Enrichissement LLM

Vous devez maintenant enrichir vos tweets avec les classifications LLM (sentiment, motif, urgence, churn).

### Option 1 : Pipeline complet (recommandé)

Exécutez le pipeline complet qui va :
1. Charger les données nettoyées
2. Enrichir avec Mistral LLM
3. Sauvegarder le résultat final

```bash
python main.py
```

**⚠️ Important :** Vous devez avoir configuré votre clé API Mistral dans un fichier `.env` :

```env
MISTRAL_API_KEY=votre_clé_api_ici
```

### Option 2 : Enrichissement uniquement (si données déjà nettoyées)

Si vous voulez juste enrichir les données déjà nettoyées :

```python
from src.pipeline_enrichment import enrich_with_llm
from src.utils import load_dataframe, save_dataframe
from pathlib import Path
import pandas as pd

# Charger les données nettoyées
df = load_dataframe(Path("data/processed/tweets_cleaned.parquet"))

# Enrichir avec LLM
df_enriched = enrich_with_llm(
    df,
    text_col="text_clean",
    checkpoint_path=Path("data/processed/checkpoint.parquet")
)

# Sauvegarder
save_dataframe(df_enriched, Path("data/processed/tweets_enriched.parquet"))
```

## 📋 Checklist avant de lancer

- [ ] Clé API Mistral configurée dans `.env`
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Modèle spaCy installé (`python -m spacy download fr_core_news_sm`)
- [ ] Fichier `tweets_cleaned.parquet` existe (✅ déjà fait)

## ⏱️ Temps estimé

Pour 3,035 tweets :
- **Temps estimé** : 15-30 minutes (selon votre connexion et le modèle Mistral)
- **Coût estimé** : ~$0.50-$2.00 (selon le modèle utilisé)

## 🎨 Après l'enrichissement : Dashboard

Une fois l'enrichissement terminé, lancez le dashboard :

```bash
streamlit run app/streamlit_app.py
```

Le dashboard affichera :
- 📊 KPIs (sentiment, urgence, churn)
- 📈 Graphiques temporels
- 🎯 Analyse par motif
- 📋 Liste des tweets avec filtres

## 🔧 Configuration

### Modèle Mistral

Par défaut : `mistral-medium-latest` (plus précis, plus cher)

Pour réduire les coûts, modifiez `.env` :
```env
MISTRAL_MODEL=mistral-small-latest
```

### Taille des batches

Par défaut : 20 tweets par batch

Pour modifier, éditez `src/config.py` :
```python
LLM_BATCH_SIZE = 20  # Augmentez pour aller plus vite (risque rate limit)
```

## 📊 Vérification

Après l'enrichissement, vérifiez que les colonnes sont présentes :

```python
import pandas as pd
df = pd.read_parquet("data/processed/tweets_enriched.parquet")
print(df.columns)
# Doit contenir: motif, sentiment, urgence, risque_churn, is_churn_risk
```

## 🆘 Problèmes courants

### Erreur "MISTRAL_API_KEY non définie"
→ Créez un fichier `.env` avec votre clé API

### Rate limit API
→ Le pipeline gère automatiquement les pauses. Attendez quelques minutes et relancez.

### Interruption du traitement
→ Le pipeline sauvegarde un checkpoint. Relancez simplement `python main.py` pour reprendre.

### Coûts trop élevés
→ Utilisez `mistral-small-latest` au lieu de `mistral-medium-latest`

## 📞 Besoin d'aide ?

Consultez :
- `README.md` : Documentation complète
- `QUICKSTART.md` : Guide de démarrage rapide
- `DOC_CLEANING.md` : Documentation du nettoyage
- `DOC_FILTRE_FREE.md` : Documentation du filtrage Free

