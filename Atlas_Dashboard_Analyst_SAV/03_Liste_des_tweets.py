"""
Page 3: Liste des tweets avec filtres avancés
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from src.config import COLORS
from src.utils import load_dataframe
from src.config import PROCESSED_DIR


def load_data():
    """Charge les données depuis la session ou le fichier"""
    if "df_filtered" in st.session_state:
        return st.session_state["df_filtered"]
    
    data_file = PROCESSED_DIR / "tweets_enriched.parquet"
    if not data_file.exists():
        alt_files = [
            PROCESSED_DIR / "free_tweets_enriched_parsed.parquet",
            PROCESSED_DIR / "free_tweets_enriched.parquet"
        ]
        for alt_file in alt_files:
            if alt_file.exists():
                data_file = alt_file
                break
    
    if data_file.exists():
        return load_dataframe(data_file)
    return None


def get_badge_html(value, badge_type="sentiment"):
    """Génère le HTML pour un badge coloré"""
    value_lower = str(value).lower()
    
    if badge_type == "sentiment":
        if value_lower == "positif":
            return '<span class="badge-positif">Positif</span>'
        elif value_lower == "neutre":
            return '<span class="badge-neutre">Neutre</span>'
        elif value_lower == "négatif":
            return '<span class="badge-negatif">Négatif</span>'
    
    elif badge_type == "urgence":
        if value_lower == "faible":
            return '<span class="badge-faible">Faible</span>'
        elif value_lower == "moyenne":
            return '<span class="badge-moyenne">Moyenne</span>'
        elif value_lower == "élevée":
            return '<span class="badge-elevee">Élevée</span>'
    
    elif badge_type == "churn":
        if value_lower in ["modéré", "élevé"]:
            return '<span class="badge-elevee">Risque</span>'
        else:
            return '<span class="badge-faible">Faible</span>'
    
    return str(value)


def render_tweet_table(df):
    """Affiche le tableau HTML custom des tweets"""
    if len(df) == 0:
        st.info("Aucun tweet ne correspond aux filtres")
        return
    
    # Colonnes à afficher
    display_cols = []
    if "created_at" in df.columns:
        display_cols.append("created_at")
    if "screen_name" in df.columns:
        display_cols.append("screen_name")
    if "text_translated_fr" in df.columns:
        display_cols.append("text_translated_fr")
    elif "text_clean" in df.columns:
        display_cols.append("text_clean")
    if "motif" in df.columns:
        display_cols.append("motif")
    if "sentiment" in df.columns:
        display_cols.append("sentiment")
    if "urgence" in df.columns:
        display_cols.append("urgence")
    if "is_churn_risk" in df.columns:
        display_cols.append("is_churn_risk")
    
    df_display = df[display_cols].copy()
    
    # Limiter à 1000 lignes pour les performances
    max_rows = 1000
    if len(df_display) > max_rows:
        st.warning(f"Affichage des {max_rows} premiers résultats sur {len(df_display)}")
        df_display = df_display.head(max_rows)
    
    # Générer le HTML
    html = """
    <style>
        .tweet-table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
        }
        .tweet-table th {
            background-color: #f3f4f6;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e5e7eb;
            font-size: 0.875rem;
        }
        .tweet-table td {
            padding: 1rem;
            border-bottom: 1px solid #e5e7eb;
            font-size: 0.875rem;
        }
        .tweet-table tr:hover {
            background-color: #f9fafb;
        }
        .tweet-table tr:last-child td {
            border-bottom: none;
        }
        .tweet-text {
            max-width: 400px;
            word-wrap: break-word;
        }
    </style>
    <table class="tweet-table">
        <thead>
            <tr>
    """
    
    # En-têtes
    headers = {
        "created_at": "Date",
        "screen_name": "Client",
        "text_translated_fr": "Tweet",
        "text_clean": "Tweet",
        "motif": "Motif",
        "sentiment": "Sentiment",
        "urgence": "Urgence",
        "is_churn_risk": "Churn"
    }
    
    for col in display_cols:
        html += f'<th>{headers.get(col, col)}</th>'
    
    html += """
            </tr>
        </thead>
        <tbody>
    """
    
    # Lignes de données
    for idx, row in df_display.iterrows():
        html += "<tr>"
        
        for col in display_cols:
            value = row[col]
            
            if pd.isna(value):
                html += "<td>-</td>"
            elif col == "created_at":
                try:
                    date_val = pd.to_datetime(value)
                    html += f'<td>{date_val.strftime("%Y-%m-%d %H:%M")}</td>'
                except:
                    html += f'<td>{str(value)}</td>'
            elif col == "sentiment":
                html += f'<td>{get_badge_html(value, "sentiment")}</td>'
            elif col == "urgence":
                html += f'<td>{get_badge_html(value, "urgence")}</td>'
            elif col == "is_churn_risk":
                html += f'<td>{get_badge_html("élevé" if value else "faible", "churn")}</td>'
            elif col in ["text_translated_fr", "text_clean"]:
                text = str(value)[:200] + ("..." if len(str(value)) > 200 else "")
                html += f'<td class="tweet-text">{text}</td>'
            else:
                html += f'<td>{str(value)}</td>'
        
        html += "</tr>"
    
    html += """
        </tbody>
    </table>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def main():
    """Page de liste des tweets"""
    st.title("📋 Liste des Tweets")
    
    df = load_data()
    
    if df is None or len(df) == 0:
        st.error("❌ Aucune donnée disponible")
        return
    
    # Filtres avancés dans la sidebar
    with st.sidebar:
        st.header("🔍 Filtres Avancés")
        
        # Filtre par client
        if "screen_name" in df.columns:
            clients = ["Tous"] + sorted(df["screen_name"].dropna().unique().tolist())
            selected_client = st.selectbox("Client", clients)
            if selected_client != "Tous":
                df = df[df["screen_name"] == selected_client]
        
        # Filtre par motif
        if "motif" in df.columns:
            motifs = ["Tous"] + sorted(df["motif"].dropna().unique().tolist())
            selected_motif = st.selectbox("Motif", motifs)
            if selected_motif != "Tous":
                df = df[df["motif"] == selected_motif]
        
        # Filtre par sentiment
        if "sentiment" in df.columns:
            sentiments = ["Tous"] + sorted(df["sentiment"].dropna().unique().tolist())
            selected_sentiment = st.selectbox("Sentiment", sentiments)
            if selected_sentiment != "Tous":
                df = df[df["sentiment"] == selected_sentiment]
        
        # Filtre par urgence
        if "urgence" in df.columns:
            urgences = ["Tous"] + sorted(df["urgence"].dropna().unique().tolist())
            selected_urgence = st.selectbox("Urgence", urgences)
            if selected_urgence != "Tous":
                df = df[df["urgence"] == selected_urgence]
        
        # Filtre churn
        if "is_churn_risk" in df.columns:
            churn_options = ["Tous", "Risque churn", "Pas de risque"]
            selected_churn = st.selectbox("Risque churn", churn_options)
            if selected_churn == "Risque churn":
                df = df[df["is_churn_risk"] == True]
            elif selected_churn == "Pas de risque":
                df = df[df["is_churn_risk"] == False]
        
        # Filtre par date
        if "created_at" in df.columns and not df["created_at"].isna().all():
            date_min = pd.to_datetime(df["created_at"]).min().date()
            date_max = pd.to_datetime(df["created_at"]).max().date()
            
            date_range = st.date_input(
                "Période",
                value=(date_min, date_max),
                min_value=date_min,
                max_value=date_max
            )
            
            if len(date_range) == 2:
                df = df[
                    (pd.to_datetime(df["created_at"]).dt.date >= date_range[0]) &
                    (pd.to_datetime(df["created_at"]).dt.date <= date_range[1])
                ]
    
    # Statistiques
    st.metric("Nombre de tweets", len(df))
    
    st.markdown("---")
    
    # Tableau
    render_tweet_table(df)
    
    # Bouton d'export
    if len(df) > 0:
        st.markdown("---")
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Télécharger les résultats (CSV)",
            data=csv,
            file_name=f"tweets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()

