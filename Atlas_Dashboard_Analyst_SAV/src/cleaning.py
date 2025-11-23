"""
Module de nettoyage et préprocessing des tweets
"""
import pandas as pd
import numpy as np
import re
from typing import Dict, Optional, Tuple
import logging
from tqdm import tqdm

# Imports optionnels avec gestion d'erreur
try:
    import spacy
except ImportError:
    spacy = None
    logging.warning("spacy non installé. Installez-le avec: pip install spacy")

try:
    from langdetect import detect, LangDetectException
except ImportError:
    detect = None
    LangDetectException = Exception
    logging.warning("langdetect non installé. Installez-le avec: pip install langdetect")

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None
    logging.warning("deep-translator non installé. Installez-le avec: pip install deep-translator")

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ImportError:
    logging.warning("tenacity non installé. Installez-le avec: pip install tenacity")
    # Définir des décorateurs vides
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = lambda x: None
    wait_exponential = lambda **kwargs: None
    retry_if_exception_type = lambda *args: None

try:
    import emoji
except ImportError:
    emoji = None
    logging.warning("emoji non installé. Installez-le avec: pip install emoji")

from src.utils import safe_str, normalize_whitespace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Regex pour emojis
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+"
)

# Dictionnaire d'abréviations
ABBREV_DICT = {
    "mdr": "mort de rire",
    "svp": "s'il vous plaît",
    "stp": "s'il te plaît",
    "c": "c est",
    "qd": "quand",
    "j": "je",
    "t": "tu",
    "pk": "pourquoi",
    "bcp": "beaucoup",
    "jpp": "j'en peux plus",
    "pr": "pour",
    "pcq": "parce que",
    "tt": "tout",
    "tkt": "t inquiète",
    "slt": "salut",
    "bjr": "bonjour",
    "bj": "bonjour",
    "dsl": "désolé",
    "lol": "mort de rire"
}

# Chargement spaCy
if spacy is not None:
    try:
        nlp = spacy.load("fr_core_news_sm")
    except OSError:
        logger.warning("Modèle spaCy fr_core_news_sm non trouvé. Utilisation du modèle blank.")
        try:
            nlp = spacy.blank("fr")
        except Exception:
            nlp = None
            logger.error("Impossible de charger spaCy. Installez-le avec: pip install spacy && python -m spacy download fr_core_news_sm")
else:
    nlp = None
    logger.error("spacy n'est pas installé. Installez-le avec: pip install spacy")

if nlp is not None:
    STOP_WORDS = set(nlp.Defaults.stop_words) if hasattr(nlp.Defaults, "stop_words") else set()
else:
    STOP_WORDS = set()
NEGATIONS_TO_KEEP = {"pas", "plus", "jamais", "rien", "aucun", "personne"}
STOP_WORDS = STOP_WORDS.difference(NEGATIONS_TO_KEEP)


def extract_emojis(text: str) -> str:
    """Extrait les emojis d'un texte"""
    return "".join(_EMOJI_RE.findall(safe_str(text)))


def reduce_repetitions(text: str) -> str:
    """Réduit les répétitions de caractères (ex: 'coooool' -> 'cool')"""
    return re.sub(r"(.)\1{3,}", r"\1\1\1", safe_str(text))


def split_camel_case(word: str) -> str:
    """Sépare les mots en camelCase"""
    parts = re.findall(
        r"[A-ZÉÈÊÎÏÀÂÇÔÛÜ][a-zàâçéèêëîïôûùüÿñæœ]+|[A-ZÉÈÊÎÏÀÂÇÔÛÜ]+(?=[A-Z][a-z])|[A-Za-zÀ-ÖØ-öø-ÿ]+|\d+",
        word
    )
    return " ".join(parts) if len(parts) > 1 else word


def remove_punctuation(text: str, keep_emoji: bool = False) -> str:
    """Supprime la ponctuation"""
    out = []
    for c in safe_str(text):
        if c == " ":
            out.append(c)
        elif c.isalnum():
            out.append(c)
        elif keep_emoji and _EMOJI_RE.match(c):
            out.append(c)
        elif c in ".,;!?()[]{}\"'`:/\\|^~_=+*«»—–-":
            out.append(" ")
    return "".join(out)


def expand_abbreviations(text: str, abbrev_dict: Dict[str, str]) -> str:
    """Développe les abréviations"""
    t = safe_str(text)
    for abbr, full in sorted(abbrev_dict.items(), key=lambda kv: len(kv[0]), reverse=True):
        t = re.sub(r"\b" + re.escape(abbr) + r"\b", full, t, flags=re.IGNORECASE)
    return t


def filter_tweets(
    df: pd.DataFrame, 
    text_col: str = "full_text",
    user_col: str = "screen_name",
    exclude_free: bool = True
) -> pd.DataFrame:
    """
    Filtre les tweets: supprime RT, doublons, NaN, et optionnellement les tweets de Free
    
    Args:
        df: DataFrame à filtrer
        text_col: Colonne contenant le texte des tweets
        user_col: Colonne contenant le nom d'utilisateur (pour exclure Free)
        exclude_free: Si True, exclut les tweets des comptes Free
    """
    df_filtered = df.dropna(subset=[text_col]).copy()
    
    # Supprimer les RT
    df_filtered = df_filtered[
        ~df_filtered[text_col].astype(str).str.startswith(("RT", "rt"), na=False)
    ].copy()
    
    # Exclure les tweets de Free (comptes contenant "free" dans le nom)
    if exclude_free and user_col in df_filtered.columns:
        initial_count = len(df_filtered)
        # Normaliser en minuscules pour la recherche
        df_filtered["_user_lower"] = df_filtered[user_col].astype(str).str.lower()
        # Exclure les comptes contenant "free" (free, freebox, free_assistance, etc.)
        df_filtered = df_filtered[
            ~df_filtered["_user_lower"].str.contains("free", na=False)
        ].copy()
        df_filtered = df_filtered.drop(columns=["_user_lower"])
        free_count = initial_count - len(df_filtered)
        if free_count > 0:
            logger.info(f"Tweets Free exclus: {free_count}")
    
    # Supprimer les doublons
    df_filtered = df_filtered.drop_duplicates(subset=[text_col])
    
    logger.info(f"Tweets filtrés: {len(df_filtered)}/{len(df)} (clients uniquement)")
    return df_filtered


def detect_language(text: str) -> str:
    """
    Détecte la langue d'un texte
    """
    if detect is None:
        logger.warning("langdetect non disponible, détection basique")
        s = safe_str(text).lower()
        fr = any(x in s for x in [" le ", " la ", " les ", " des ", " pour ", " parce "])
        en = any(x in s for x in [" the ", " and ", " you ", " for "])
        es = any(x in s for x in [" el ", " la ", " los ", " gracias "])
        return "fr" if fr else ("en" if en else ("es" if es else "und"))
    
    try:
        return detect(safe_str(text))
    except (LangDetectException, Exception):
        s = safe_str(text).lower()
        fr = any(x in s for x in [" le ", " la ", " les ", " des ", " pour ", " parce "])
        en = any(x in s for x in [" the ", " and ", " you ", " for "])
        es = any(x in s for x in [" el ", " la ", " los ", " gracias "])
        return "fr" if fr else ("en" if en else ("es" if es else "und"))


class TranslationError(Exception):
    pass


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
    retry=retry_if_exception_type((TranslationError, Exception)),
)
def _translate_once(text: str, src: Optional[str]) -> str:
    """Traduit un texte une fois avec retry"""
    if GoogleTranslator is None:
        raise TranslationError("deep-translator non installé")
    
    try:
        out = GoogleTranslator(source=src or "auto", target="fr").translate(text)
        if not isinstance(out, str) or not out.strip():
            raise TranslationError("Empty translation")
        return out
    except Exception as e:
        raise TranslationError(str(e))


def translate_to_french(text: str, lang_hint: Optional[str]) -> str:
    """
    Traduit un texte en français si nécessaire
    """
    if not text or len(safe_str(text).strip()) < 3:
        return safe_str(text)
    
    if (lang_hint or "").lower() == "fr":
        return safe_str(text)
    
    try:
        return _translate_once(safe_str(text), src=lang_hint)
    except Exception:
        logger.warning(f"Échec traduction pour: {text[:50]}...")
        return safe_str(text)


def cleaning_with_translation(text: str) -> Tuple[str, str, str]:
    """
    Nettoie et traduit un texte
    Retourne: (langue, texte_traduit_fr, texte_nettoyé)
    """
    t = safe_str(text)
    
    # Nettoyage de base
    t = re.sub(r"http\S+|www\.\S+", " ", t)
    t = re.sub(r"@\w+", " ", t)
    t = t.replace("#", " ")
    t = t.replace("\n", " ").replace("\\n", " ")
    
    # Détection langue et traduction
    lang = detect_language(t)
    t_fr_raw = translate_to_french(t, lang)
    
    # Normalisation
    t_fr = t_fr_raw.lower()
    t_fr = reduce_repetitions(t_fr)
    t_fr = " ".join(split_camel_case(w) for w in t_fr.split())
    t_fr = remove_punctuation(t_fr, keep_emoji=False)
    t_fr = expand_abbreviations(t_fr, ABBREV_DICT)
    t_fr = _EMOJI_RE.sub(" ", t_fr)
    t_fr = normalize_whitespace(t_fr)
    
    return lang, t_fr_raw, t_fr


def preprocess_text(text: str, keep_numbers: bool = False) -> str:
    """
    Préprocessing avec spaCy: tokenisation, lemmatisation, stopwords
    """
    if pd.isna(text) or not safe_str(text):
        return ""
    
    if nlp is None:
        logger.warning("spaCy non disponible, retour du texte original")
        return safe_str(text)
    
    doc = nlp(safe_str(text))
    tokens = []
    
    for tok in doc:
        if not (tok.is_alpha or (keep_numbers and tok.like_num)):
            continue
        lemma = (tok.lemma_ or tok.text).lower()
        if not lemma or lemma == "nan" or lemma in STOP_WORDS:
            continue
        tokens.append(lemma)
    
    return " ".join(tokens)


def pipeline_cleaning(text: str) -> Dict[str, str]:
    """
    Pipeline complet de nettoyage
    """
    raw = safe_str(text)
    emojis = extract_emojis(raw)
    lang, t_fr_raw, t_clean = cleaning_with_translation(raw)
    
    return {
        "lang": lang,
        "text_translated_fr": t_fr_raw,
        "text_clean": t_clean,
        "emojis": emojis
    }


def run_cleaning_on_df(
    df: pd.DataFrame, 
    text_col: str = "full_text",
    user_col: str = "screen_name",
    exclude_free: bool = True
) -> pd.DataFrame:
    """
    Applique le pipeline de nettoyage sur un DataFrame
    
    Args:
        df: DataFrame à nettoyer
        text_col: Colonne contenant le texte des tweets
        user_col: Colonne contenant le nom d'utilisateur (pour exclure Free)
        exclude_free: Si True, exclut les tweets des comptes Free
    """
    assert text_col in df.columns, f"Colonne '{text_col}' absente"
    
    df = df.copy()
    df[text_col] = df[text_col].astype(str)
    df_filtered = filter_tweets(df, text_col=text_col, user_col=user_col, exclude_free=exclude_free)
    
    logger.info("Début du nettoyage...")
    tqdm.pandas(desc="Nettoyage")
    res = df_filtered[text_col].progress_apply(
        lambda s: pd.Series(pipeline_cleaning(s))
    )
    
    for col in ["lang", "text_translated_fr", "text_clean", "emojis"]:
        df_filtered[col] = res[col].values
    
    logger.info("Préprocessing avec spaCy...")
    df_filtered["text_preproc"] = df_filtered["text_clean"].progress_apply(
        lambda x: preprocess_text(x)
    )
    
    df_filtered = df_filtered.reset_index(drop=True)
    logger.info(f"Nettoyage terminé: {len(df_filtered)} tweets")
    
    return df_filtered

