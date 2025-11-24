import os
import httpx
import time
import asyncio
from typing import List, Dict, Optional, Any
from fastapi import HTTPException

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED" 

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if time.time() - self.last_failure_time > self.recovery_seconds:
            self.state = "HALF_OPEN"
            return True
        return False

class MistralClient:
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.mistral.ai",
        default_model: str = "mistral-medium",
        fallback_models: Optional[List[str]] = None,
        max_concurrency: int = 3,
        max_retries: int = 2,
        backoff_base: float = 1.0,
        failure_threshold: int = 4,
        recovery_seconds: int = 60,
    ):
        if not api_key:
            raise ValueError("api_key required")
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.default_model = default_model
        self.fallback_models = fallback_models if fallback_models is not None else ["mistral-small", "mistral-tiny"]
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.circuit = CircuitBreaker(failure_threshold=failure_threshold, recovery_seconds=recovery_seconds)

        self._client = httpx.AsyncClient(base_url=self.api_url, headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}, timeout=60.0)

    async def close(self):
        await self._client.aclose()

    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.7) -> str:
        if not self.circuit.can_execute():
            raise HTTPException(status_code=503, detail="Service IA temporairement indisponible (Circuit Open)")

        tgt_model = model or self.default_model
        models_to_try = [tgt_model] + self.fallback_models

        async with self.semaphore:
            for m_name in models_to_try:
                for attempt in range(self.max_retries + 1):
                    try:
                        payload = {
                            "model": m_name,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": 1000
                        }
                        
                        resp = await self._client.post("/v1/chat/completions", json=payload)
                        
                        if resp.status_code == 200:
                            self.circuit.record_success()
                            data = resp.json()
                            return data["choices"][0]["message"]["content"]
                        
                        if resp.status_code in [429, 500, 502, 503, 504]:
                            if attempt < self.max_retries:
                                await asyncio.sleep(self.backoff_base * (2 ** attempt))
                                continue
                            else:
                                self.circuit.record_failure()
                        
                        elif resp.status_code == 400:
                            # Bad request (often invalid model), try next model
                            break
                        
                        else:
                            # Other error
                            if attempt == self.max_retries:
                                self.circuit.record_failure()
                                
                    except httpx.RequestError:
                        if attempt == self.max_retries:
                            self.circuit.record_failure()
                        else:
                            await asyncio.sleep(0.5)

        raise HTTPException(status_code=503, detail="Echec de la génération IA après plusieurs tentatives")

    async def get_embedding(self, text: str) -> List[float]:
        if not self.circuit.can_execute():
            # Return dummy embedding if circuit open
            return [0.0] * 1024

        try:
            resp = await self._client.post("/v1/embeddings", json={"model": "mistral-embed", "input": [text]})
            if resp.status_code == 200:
                self.circuit.record_success()
                return resp.json()["data"][0]["embedding"]
            else:
                self.circuit.record_failure()
                return [0.0] * 1024
        except:
            self.circuit.record_failure()
            return [0.0] * 1024
