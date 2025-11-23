import re
from datetime import datetime

def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def normalize_agent_signature(text: str) -> str:
    """
    Ensure the text ends with the agent signature.
    If missing, append it.
    If present but malformed, fix it.
    """
    signature = "\n-- Agent Free"
    # Check if it ends with signature (ignoring whitespace)
    if text.strip().endswith("-- Agent Free"):
        return text
    
    # Check if it contains it but maybe not at the very end or slightly different
    # Simple approach: just append if not strictly present at end
    return text.rstrip() + signature
