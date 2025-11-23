import sys
from pathlib import Path
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, date
from collections import Counter
import re
import json

# Add project root to sys.path to import src modules
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.utils import load_dataframe
from src.config import PROCESSED_DIR, COLORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SAV Analytics API", debug=True)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global DataFrame
df_enriched = None

def load_data():
    """Load data from parquet files with fallback"""
    global df_enriched
    try:
        data_file = PROCESSED_DIR / "tweets_enriched.parquet"
        if not data_file.exists():
            alternatives = [
                PROCESSED_DIR / "free_tweets_enriched_parsed.parquet",
                PROCESSED_DIR / "free_tweets_enriched.parquet",
                PROCESSED_DIR / "tweets_cleaned.parquet"
            ]
            for alt in alternatives:
                if alt.exists():
                    data_file = alt
                    break
        
        if not data_file.exists():
            logger.error("No data file found!")
            return
            
        logger.info(f"Loading data from {data_file}")
        df = load_dataframe(data_file)
        
        # Ensure datetime
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
            if df["created_at"].dt.tz is not None:
                df["created_at"] = df["created_at"].dt.tz_convert(None)
            df = df.dropna(subset=["created_at"])
            df["date"] = df["created_at"].dt.date
            df["week"] = df["created_at"].dt.to_period("W").astype(str)
            df["month"] = df["created_at"].dt.to_period("M").astype(str)
            df["hour"] = df["created_at"].dt.hour
            
        # Normalize column names (handle Capitalized names)
        df.rename(columns={
            "Motif": "motif",
            "Sentiment": "sentiment",
            "Urgence": "urgence",
            "Risque_churn": "risque_churn",
            "Risque Churn": "risque_churn"
        }, inplace=True)
            
        # Normalize columns
        if "sentiment" in df.columns:
            df["sentiment_norm"] = df["sentiment"].astype(str).str.lower().map({
                "positif": "Positif", "positive": "Positif",
                "negatif": "Négatif", "négatif": "Négatif",
                "neutre": "Neutre"
            }).fillna("Neutre")
        else:
            df["sentiment_norm"] = "Neutre"

        if "urgence" in df.columns:
            df["is_urgent"] = df["urgence"].astype(str).str.contains("élev", case=False, na=False)
        else:
            df["is_urgent"] = False

        if "risque_churn" in df.columns:
            df["churn_risk"] = df["risque_churn"].astype(str)
        elif "is_churn_risk" in df.columns:
            df["churn_risk"] = df["is_churn_risk"].apply(lambda x: "élevé" if x else "faible")
        else:
            df["churn_risk"] = "faible"
        df["is_churn"] = df["churn_risk"].str.lower().str.contains("élev", na=False)
            
        df_enriched = df
        logger.info(f"Data loaded successfully: {len(df)} rows")
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")

@app.on_event("startup")
async def startup_event():
    load_data()

def apply_filters(
    df: pd.DataFrame,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent_only: bool = False,
    churn_risk: Optional[str] = None
) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    
    filtered_df = df.copy()
    
    if start_date:
        filtered_df = filtered_df[filtered_df["date"] >= start_date]
    if end_date:
        filtered_df = filtered_df[filtered_df["date"] <= end_date]
        
    if motif and motif != "(Tous)":
        if "motif" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["motif"] == motif]
            
    if sentiment and sentiment != "(Tous)":
        filtered_df = filtered_df[filtered_df["sentiment_norm"] == sentiment]
        
    if urgent_only:
        filtered_df = filtered_df[filtered_df["is_urgent"]]
        
    if churn_risk and churn_risk != "(Tous)":
        filtered_df = filtered_df[filtered_df["churn_risk"] == churn_risk]
        
    return filtered_df

@app.get("/api/filters")
async def get_filters():
    if df_enriched is None:
        return {"min_date": None, "max_date": None, "motifs": [], "churn_risks": []}
    
    motifs = sorted(df_enriched["motif"].dropna().unique().tolist()) if "motif" in df_enriched.columns else []
    churn_risks = sorted(df_enriched["churn_risk"].dropna().unique().tolist()) if "churn_risk" in df_enriched.columns else []
    
    return {
        "min_date": df_enriched["date"].min(),
        "max_date": df_enriched["date"].max(),
        "motifs": motifs,
        "churn_risks": churn_risks
    }

@app.get("/api/kpis")
async def get_kpis(
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    
    total = len(df)
    if total == 0:
        return {
            "total_tweets": 0,
            "negatifs": 0, "negatifs_pct": 0,
            "positifs": 0, "positifs_pct": 0,
            "neutres": 0, "neutres_pct": 0,
            "urgents": 0, "urgents_pct": 0,
            "churn": 0, "churn_pct": 0,
            "worst_day": "N/A", "worst_day_count": 0
        }
        
    neg = len(df[df["sentiment_norm"] == "Négatif"])
    pos = len(df[df["sentiment_norm"] == "Positif"])
    neu = len(df[df["sentiment_norm"] == "Neutre"])
    urg = df["is_urgent"].sum()
    churn_count = df["is_churn"].sum()
    
    worst_day = "N/A"
    worst_day_count = 0
    if neg > 0:
        df_neg = df[df["sentiment_norm"] == "Négatif"]
        daily_neg = df_neg.groupby("date").size()
        if not daily_neg.empty:
            worst_day = daily_neg.idxmax()
            worst_day_count = int(daily_neg.max())

    return {
        "total_tweets": total,
        "negatifs": neg, "negatifs_pct": round(neg/total*100, 1),
        "positifs": pos, "positifs_pct": round(pos/total*100, 1),
        "neutres": neu, "neutres_pct": round(neu/total*100, 1),
        "urgents": int(urg), "urgents_pct": round(urg/total*100, 1),
        "churn": int(churn_count), "churn_pct": round(churn_count/total*100, 1),
        "worst_day": str(worst_day), "worst_day_count": worst_day_count
    }

@app.get("/api/wordcloud")
async def get_wordcloud(
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    
    # Use negative tweets for wordcloud if no sentiment specified, or use filtered df
    if sentiment is None or sentiment == "(Tous)":
        df_target = df[df["sentiment_norm"] == "Négatif"]
    else:
        df_target = df
        
    if df_target.empty:
        return []

    # Simple word extraction (splitting by space, removing short words)
    # In a real app, use proper tokenization and stopword removal
    text_col = "text_clean" if "text_clean" in df_target.columns else "full_text"
    all_text = " ".join(df_target[text_col].astype(str).tolist()).lower()
    words = re.findall(r'\w+', all_text)
    
    # Basic stop words (very limited list for demo)
    stop_words = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'est', 'en', 'il', 'elle', 'que', 'qui', 'ce', 'ca', 'pour', 'sur', 'dans', 'pas', 'plus', 'mais', 'avec', 'tout', 'fait', 'faire', 'être', 'avoir', 'a', 'au', 'aux', 'ne', 'se', 'par', 'je', 'tu', 'nous', 'vous', 'ils', 'elles', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses', 'notre', 'votre', 'leur', 'leurs', 'free', 'freemobile'}
    
    filtered_words = [w for w in words if len(w) > 3 and w not in stop_words]
    counter = Counter(filtered_words)
    
    # Top 30 words
    top_words = counter.most_common(30)
    
    # Normalize sizes
    if not top_words:
        return []
        
    max_count = top_words[0][1]
    min_count = top_words[-1][1]
    
    result = []
    colors = ['#ef4444', '#f97316', '#f59e0b', '#8b5cf6', '#6366f1', '#10b981', '#3b82f6']
    
    for i, (word, count) in enumerate(top_words):
        # Scale size between 12 and 60
        size = 12 + ((count - min_count) / (max_count - min_count + 1)) * 48
        result.append({
            "text": word,
            "size": int(size),
            "color": colors[i % len(colors)]
        })
        
    return result

@app.get("/api/volume")
async def get_volume(
    period: str = "day",
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    
    if df.empty:
        return []

    if period == "day":
        vol = df.groupby("date").size().reset_index(name="volume")
        # Limit to last 30 days if too many
        if len(vol) > 30:
            vol = vol.iloc[-30:]
        return [{"label": str(d), "volume": int(v)} for d, v in zip(vol["date"], vol["volume"])]
    elif period == "week":
        vol = df.groupby("week").size().reset_index(name="volume")
        return [{"label": str(w), "volume": int(v)} for w, v in zip(vol["week"], vol["volume"])]
    elif period == "month":
        vol = df.groupby("month").size().reset_index(name="volume")
        return [{"label": str(m), "volume": int(v)} for m, v in zip(vol["month"], vol["volume"])]
    elif period == "year":
        # Group by year
        df["year"] = pd.to_datetime(df["date"]).dt.year
        vol = df.groupby("year").size().reset_index(name="volume")
        return [{"label": str(y), "volume": int(v)} for y, v in zip(vol["year"], vol["volume"])]
    
    return []

@app.get("/api/churn-trend")
async def get_churn_trend(
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    
    if df.empty or "month" not in df.columns:
        return []
        
    monthly = df.groupby("month").agg(
        total=("is_churn", "count"),
        churn=("is_churn", "sum")
    ).reset_index()
    
    monthly["rate"] = (monthly["churn"] / monthly["total"] * 100).fillna(0)
    
    result = []
    for _, row in monthly.iterrows():
        result.append({
            "month": str(row["month"]),
            "actual": round(row["rate"], 1),
            "predicted": None
        })
        
    # Add simple linear projection for next 2 months
    if len(result) >= 2:
        last_val = result[-1]["actual"]
        prev_val = result[-2]["actual"]
        trend = last_val - prev_val
        
        result.append({"month": "Next+1", "actual": None, "predicted": round(max(0, last_val + trend), 1)})
        result.append({"month": "Next+2", "actual": None, "predicted": round(max(0, last_val + trend * 2), 1)})
        
    return result

@app.get("/api/churn-motifs-stacked")
async def get_churn_motifs_stacked(
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    
    # Filter for churners only
    df_churn = df[df["is_churn"]]
    
    if df_churn.empty or "motif" not in df_churn.columns:
        return []
        
    stacked = df_churn.groupby(["month", "motif"]).size().unstack(fill_value=0).reset_index()
    
    result = []
    for _, row in stacked.iterrows():
        item = {"month": str(row["month"])}
        for col in stacked.columns:
            if col != "month":
                item[col] = int(row[col])
        result.append(item)
        
    return result

@app.get("/api/churn-distribution")
async def get_churn_distribution(
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    df_churn = df[df["is_churn"]]
    
    if df_churn.empty or "motif" not in df_churn.columns:
        return []
        
    dist = df_churn["motif"].value_counts().reset_index()
    dist.columns = ["name", "value"]
    
    # Assign colors
    colors = ['#ef4444', '#f97316', '#f59e0b', '#8b5cf6', '#64748b', '#10b981']
    
    result = []
    for i, row in dist.iterrows():
        result.append({
            "name": row["name"],
            "value": int(row["value"]),
            "color": colors[i % len(colors)]
        })
        
    return result

@app.get("/api/motif-sentiment")
async def get_motif_sentiment(
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    
    if "motif" not in df.columns or "sentiment_norm" not in df.columns:
        return []
        
    pivot = df.groupby(["motif", "sentiment_norm"]).size().unstack(fill_value=0).reset_index()
    
    result = []
    for _, row in pivot.iterrows():
        total = row.get("Positif", 0) + row.get("Neutre", 0) + row.get("Négatif", 0)
        if total > 0:
            result.append({
                "motif": row["motif"],
                "positif": round(row.get("Positif", 0) / total * 100, 1),
                "neutre": round(row.get("Neutre", 0) / total * 100, 1),
                "negatif": round(row.get("Négatif", 0) / total * 100, 1)
            })
            
    return result

@app.get("/api/sentiment-distribution")
async def get_sentiment_distribution(
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    
    counts = df["sentiment_norm"].value_counts()
    
    return [
        { "name": 'Positif', "value": int(counts.get("Positif", 0)), "color": '#10b981' },
        { "name": 'Neutre', "value": int(counts.get("Neutre", 0)), "color": '#6b7280' },
        { "name": 'Négatif', "value": int(counts.get("Négatif", 0)), "color": '#ef4444' },
    ]

@app.get("/api/activity-peaks")
async def get_activity_peaks(
    type: str = "hourly",
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    
    if type == "hourly":
        grp = df.groupby("hour").agg(
            volume=("full_text", "count"),
            negative=("sentiment_norm", lambda x: (x == "Négatif").sum())
        ).reset_index()
        return [{"time": f"{h}h", "volume": int(v), "negative": int(n)} for h, v, n in zip(grp["hour"], grp["volume"], grp["negative"])]
        
    elif type == "daily":
        grp = df.groupby("date").agg(
            volume=("full_text", "count"),
            negative=("sentiment_norm", lambda x: (x == "Négatif").sum())
        ).reset_index()
        return [{"day": str(d), "volume": int(v), "negative": int(n)} for d, v, n in zip(grp["date"], grp["volume"], grp["negative"])]
        
    elif type == "weekly":
        grp = df.groupby("week").agg(
            volume=("full_text", "count"),
            negative=("sentiment_norm", lambda x: (x == "Négatif").sum())
        ).reset_index()
        return [{"week": str(w), "volume": int(v), "negative": int(n)} for w, v, n in zip(grp["week"], grp["volume"], grp["negative"])]

    return []

@app.get("/api/tweets")
async def get_tweets(
    page: int = 1,
    limit: int = 15,
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    
    total = len(df)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    # Slice dataframe
    df_page = df.iloc[start_idx:end_idx].copy()
    
    # Convert dates to string for JSON serialization
    if "date" in df_page.columns:
        df_page["date"] = df_page["date"].astype(str)
    if "created_at" in df_page.columns:
        df_page["created_at"] = df_page["created_at"].astype(str)
        
    # Safe serialization using pandas to_json
    data_json = df_page.to_json(orient="records", date_format="iso")
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": json.loads(data_json)
    }

@app.get("/api/export")
async def export_tweets(
    columns: str = Query(None), # Comma separated list of columns
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    motif: Optional[str] = None,
    sentiment: Optional[str] = None,
    urgent: bool = False,
    churn: Optional[str] = None
):
    df = apply_filters(df_enriched, startDate, endDate, motif, sentiment, urgent, churn)
    
    # Column mapping for renaming
    column_mapping = {
        "created_at": "Date de création",
        "date": "Date",
        "full_text": "Message original",
        "text_clean": "Message nettoyé",
        "text_translated_fr": "Message traduit",
        "motif": "Motif",
        "sentiment_norm": "Sentiment",
        "is_urgent": "Urgent",
        "churn_risk": "Risque Churn",
        "lang": "Langue",
        "emojis": "Emojis"
    }
    
    # Select and rename columns
    if columns:
        selected_cols = columns.split(",")
        # Filter only existing columns
        valid_cols = [c for c in selected_cols if c in df.columns]
        df_export = df[valid_cols].copy()
    else:
        # Default columns if none specified
        default_cols = ["date", "full_text", "motif", "sentiment_norm", "is_urgent", "churn_risk"]
        valid_cols = [c for c in default_cols if c in df.columns]
        df_export = df[valid_cols].copy()
        
    # Rename columns
    df_export = df_export.rename(columns=column_mapping)
    
    # Convert to CSV
    from fastapi.responses import StreamingResponse
    import io
    
    stream = io.StringIO()
    df_export.to_csv(stream, index=False, sep=";")
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=export_tweets.csv"
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
