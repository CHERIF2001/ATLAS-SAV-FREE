import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from src.config import COLORS, PROCESSED_DIR
from src.utils import load_dataframe

def load_data():
    if "df_filtered" in st.session_state:
        return st.session_state["df_filtered"]
    
    data_file = PROCESSED_DIR / "tweets_enriched.parquet"
    if not data_file.exists():
        # Fallback files
        for f in [PROCESSED_DIR / "free_tweets_enriched_parsed.parquet", PROCESSED_DIR / "free_tweets_enriched.parquet"]:
            if f.exists():
                data_file = f
                break
    
    if data_file.exists():
        return load_dataframe(data_file)
    return None

def get_badge_html(value, badge_type="sentiment"):
    v = str(value).lower()
    
    badges = {
        "sentiment": {
            "positif": '<span class="badge-positif">Positif</span>',
            "neutre": '<span class="badge-neutre">Neutre</span>',
            "négatif": '<span class="badge-negatif">Négatif</span>'
        },
        "urgence": {
            "faible": '<span class="badge-faible">Faible</span>',
            "moyenne": '<span class="badge-moyenne">Moyenne</span>',
            "élevée": '<span class="badge-elevee">Élevée</span>'
        },
        "churn": {
            "modéré": '<span class="badge-elevee">Risque</span>',
            "élevé": '<span class="badge-elevee">Risque</span>'
        }
    }
    
    if badge_type == "churn":
        return badges["churn"].get(v, '<span class="badge-faible">Faible</span>')
        
    return badges.get(badge_type, {}).get(v, str(value))

def render_tweet_table(df):
    if len(df) == 0:
        st.info("Aucun tweet ne correspond aux filtres")
        return
    
    cols = ["created_at", "screen_name", "text_translated_fr", "text_clean", "motif", "sentiment", "urgence", "is_churn_risk"]
    display_cols = [c for c in cols if c in df.columns]
    
    # Prefer translated text if available
    if "text_translated_fr" in display_cols and "text_clean" in display_cols:
        display_cols.remove("text_clean")
    
    df_display = df[display_cols].copy()
    
    if len(df_display) > 1000:
        st.warning(f"Affichage des 1000 premiers résultats sur {len(df_display)}")
        df_display = df_display.head(1000)
    
    # CSS
    st.markdown("""
    <style>
        .tweet-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
        .tweet-table th { background: #f3f4f6; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e5e7eb; }
        .tweet-table td { padding: 12px; border-bottom: 1px solid #e5e7eb; font-size: 14px; }
        .tweet-table tr:hover { background: #f9fafb; }
        .tweet-text { max-width: 400px; word-wrap: break-word; }
    </style>
    """, unsafe_allow_html=True)
    
    html = '<table class="tweet-table"><thead><tr>'
    
    headers = {
        "created_at": "Date", "screen_name": "Client", "text_translated_fr": "Tweet",
        "text_clean": "Tweet", "motif": "Motif", "sentiment": "Sentiment",
        "urgence": "Urgence", "is_churn_risk": "Churn"
    }
    
    for col in display_cols:
        html += f'<th>{headers.get(col, col)}</th>'
    html += '</tr></thead><tbody>'
    
    for _, row in df_display.iterrows():
        html += "<tr>"
        for col in display_cols:
            val = row[col]
            if pd.isna(val):
                html += "<td>-</td>"
                continue
                
            if col == "created_at":
                try:
                    html += f'<td>{pd.to_datetime(val).strftime("%Y-%m-%d %H:%M")}</td>'
                except:
                    html += f'<td>{val}</td>'
            elif col == "sentiment":
                html += f'<td>{get_badge_html(val, "sentiment")}</td>'
            elif col == "urgence":
                html += f'<td>{get_badge_html(val, "urgence")}</td>'
            elif col == "is_churn_risk":
                html += f'<td>{get_badge_html("élevé" if val else "faible", "churn")}</td>'
            elif "text" in col:
                text = str(val)[:200] + ("..." if len(str(val)) > 200 else "")
                html += f'<td class="tweet-text">{text}</td>'
            else:
                html += f'<td>{val}</td>'
        html += "</tr>"
        
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

def main():
    st.title("📋 Liste des Tweets")
    
    df = load_data()
    if df is None or len(df) == 0:
        st.error("❌ Aucune donnée")
        return
    
    with st.sidebar:
        st.header("🔍 Filtres")
        
        # Helper to add filter
        def add_filter(label, col):
            if col in df.columns:
                opts = ["Tous"] + sorted(df[col].dropna().unique().tolist())
                sel = st.selectbox(label, opts)
                return sel if sel != "Tous" else None
            return None

        if f_client := add_filter("Client", "screen_name"):
            df = df[df["screen_name"] == f_client]
            
        if f_motif := add_filter("Motif", "motif"):
            df = df[df["motif"] == f_motif]
            
        if f_sent := add_filter("Sentiment", "sentiment"):
            df = df[df["sentiment"] == f_sent]
            
        if f_urg := add_filter("Urgence", "urgence"):
            df = df[df["urgence"] == f_urg]
            
        if "is_churn_risk" in df.columns:
            churn_sel = st.selectbox("Risque churn", ["Tous", "Risque churn", "Pas de risque"])
            if churn_sel == "Risque churn":
                df = df[df["is_churn_risk"] == True]
            elif churn_sel == "Pas de risque":
                df = df[df["is_churn_risk"] == False]
        
        if "created_at" in df.columns:
            d_min = pd.to_datetime(df["created_at"]).min().date()
            d_max = pd.to_datetime(df["created_at"]).max().date()
            rng = st.date_input("Période", (d_min, d_max), min_value=d_min, max_value=d_max)
            
            if len(rng) == 2:
                mask = (pd.to_datetime(df["created_at"]).dt.date >= rng[0]) & (pd.to_datetime(df["created_at"]).dt.date <= rng[1])
                df = df[mask]
    
    st.metric("Nombre de tweets", len(df))
    st.markdown("---")
    
    render_tweet_table(df)
    
    if len(df) > 0:
        st.markdown("---")
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 Télécharger (CSV)",
            csv,
            f"export_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

if __name__ == "__main__":
    main()

