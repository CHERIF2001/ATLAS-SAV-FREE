"""
Inspecteur Mistral pour votre clé :
- liste les modèles accessibles
- teste rapidement chaque modèle (POST ping) pour vérifier statut et latence
- tente de récupérer infos d'usage/account si disponibles
- affiche des recommandations d'optimisation pour un usage SAV économique

Usage:
    python backend/mistral_inspector.py

Installez les dépendances via `pip install -r backend/requirements.txt` si nécessaire.
"""
import json
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv


BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

API_KEY = os.getenv("MISTRAL_API_KEY")
API_URL = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai").rstrip("/")


def print_header(title: str):
    print("\n" + "=" * 10 + f" {title} " + "=" * 10)


def show_env():
    print_header("Env")
    print("MISTRAL_API_KEY set:", bool(API_KEY))
    print("MISTRAL_API_URL:", API_URL)


def list_models(client: httpx.Client):
    print_header("Listing models (GET /v1/models)")
    url = f"{API_URL}/v1/models"
    try:
        r = client.get(url)
    except Exception as e:
        print("Request error:", e)
        return None

    print("Status:", r.status_code)
    try:
        j = r.json()
    except Exception:
        print("Non-JSON response:\n", r.text)
        return None

    # pretty print models list if present
    models = j if isinstance(j, list) else j.get("data") or j.get("models") or j
    try:
        print(json.dumps(models, indent=2, ensure_ascii=False)[:4000])
    except Exception:
        print(models)
    return models


def probe_models(client: httpx.Client, models):
    print_header("Probe models with small chat request")
    if not models:
        print("No models to probe")
        return

    results = []
    for m in models:
        # model may be dict with id field or a plain id string
        model_id = m.get("id") if isinstance(m, dict) and m.get("id") else (m if isinstance(m, str) else None)
        if not model_id:
            continue
        url = f"{API_URL}/v1/chat/completions"
        payload = {"model": model_id, "messages": [{"role": "user", "content": "Ping"}], "max_tokens": 1}
        start = time.time()
        try:
            r = client.post(url, json=payload, timeout=15.0)
            latency = time.time() - start
            try:
                body = r.json()
            except Exception:
                body = r.text
            print(f"Model {model_id}: status={r.status_code}, latency={latency:.2f}s, body_preview={str(body)[:300]}")
            results.append({"model": model_id, "status": r.status_code, "latency": latency, "body": body})
        except Exception as e:
            latency = time.time() - start
            print(f"Model {model_id}: request error after {latency:.2f}s -> {e}")
            results.append({"model": model_id, "status": None, "error": str(e)})

    return results


def try_usage_endpoints(client: httpx.Client):
    print_header("Try usage/account endpoints (best-effort)")
    endpoints = [
        f"{API_URL}/v1/usage",
        f"{API_URL}/v1/account",
        f"{API_URL}/v1/billing",
    ]
    for url in endpoints:
        try:
            r = client.get(url, timeout=10.0)
            print(f"GET {url} -> {r.status_code}")
            try:
                print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:1000])
            except Exception:
                print(r.text[:1000])
        except Exception as e:
            print(f"GET {url} -> error: {e}")


def print_recommendations(probe_results):
    print_header("Recommendations & Optimization Tips")
    print("1) Choix du modèle:")
    print("   - Préférez 'mistral-medium' si disponible (meilleur compromis qualité/coût). 'mistral-small' utile en fallback pour capacité ou latence.")
    print("2) Limiter le contexte:")
    print("   - Conservez un historique recent (ex: last 6-8 messages). Résumez l'historique si nécessaire pour respecter la fenêtre de contexte.")
    print("3) Paramètres de génération:")
    print("   - max_tokens: limitez (ex: 256) pour réduire coût; temperature: 0.0-0.3 pour ton professionnel.")
    print("4) Throttling & retries:")
    print("   - Utilisez retry exponential backoff pour 429/503; circuit-breaker pour éviter surcharge.")
    print("5) Caching & templates:")
    print("   - Cachez réponses standards (FAQ), utilisez prompts templates pour uniformité.")
    print("6) Monitoring:")
    print("   - Collectez latence, erreurs, coûts; alerte si 429 ou taux d'erreur augmente.")
    print("7) Fallbacks:")
    print("   - Si modèle principal renvoie 429, basculez temporairement vers 'mistral-small'.")
    print("8) Test rapide des résultats probe:")
    if not probe_results:
        print("   - Aucun probe disponible")
        return
    ok = [r for r in probe_results if r.get('status') == 200]
    slow = sorted([r for r in probe_results if r.get('status') == 200], key=lambda x: x.get('latency', 999))
    if ok:
        print(f"   - Modèles répondant OK: {[r['model'] for r in ok]} (ex: choisir le plus rapide/qualitatif)")
    else:
        print("   - Aucun modèle ne répond correctement: vérifiez la clé ou quotas.")


def main():
    print_header("Mistral Inspector")
    show_env()
    if not API_KEY:
        print("Please set MISTRAL_API_KEY in backend/.env before running this script.")
        return

    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
    with httpx.Client(base_url=API_URL, headers=headers, timeout=20.0) as client:
        models = list_models(client)
        probe = None
        if models:
            # normalize models list into items
            items = []
            if isinstance(models, list):
                items = models
            elif isinstance(models, dict) and 'models' in models:
                items = models['models']
            elif isinstance(models, dict) and 'data' in models:
                items = models['data']
            else:
                # maybe models is a dict keyed by id
                if isinstance(models, dict):
                    for k, v in models.items():
                        if isinstance(v, dict) and v.get('id'):
                            items.append(v)
            probe = probe_models(client, items)
            try_usage_endpoints(client)

        print_recommendations(probe)


if __name__ == '__main__':
    main()
