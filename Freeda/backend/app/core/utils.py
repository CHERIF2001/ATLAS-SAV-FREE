import re
from datetime import datetime

def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def normalize_agent_signature(text: str) -> str:
    signature = "\n-- Agent Free"
    if text.strip().endswith("-- Agent Free"):
        return text
    return text.rstrip() + signature
