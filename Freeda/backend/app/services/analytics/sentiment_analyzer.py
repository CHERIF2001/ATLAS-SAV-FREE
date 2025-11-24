from typing import List, Dict

class SentimentAnalyzer:
    def __init__(self):
        pass
    
    async def analyze(self, messages: List[Dict]) -> Dict:
        return {"sentiment": "neutre", "confidence": 0.5}
