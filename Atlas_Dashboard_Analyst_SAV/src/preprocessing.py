import re
import pandas as pd

OFFICIAL_ACCOUNTS = {
    "free", "Free", "Freebox", "freebox", "Free_1337", "free_mobile",
    "FreeboxActus", "FreeNewsActu", "GroupeIliad", "free_assistance",
    "FreeboxTV", "Freebox_Assistance",
}

def clean_text(text: str) -> str:
    text = str(text)
    text = re.sub(r"http\S+", " ", text)      # enlever URLs
    text = re.sub(r"@\w+", " ", text)         # enlever mentions
    text = re.sub(r"#(\w+)", r"\1", text)     # #hashtag -> mot
    text = text.lower()
    text = re.sub(r"\s+", " ", text)          # espaces multiples
    return text.strip()

def basic_filter(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # enlever RT
    df = df[~df["full_text"].str.startswith("RT ", na=False)]
    # enlever comptes officiels
    if "screen_name" in df.columns:
        df = df[~df["screen_name"].isin(OFFICIAL_ACCOUNTS)]
    # texte nettoyé
    df["full_text_clean"] = df["full_text"].apply(clean_text)
    return df
