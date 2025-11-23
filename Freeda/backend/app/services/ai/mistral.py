import asyncio
import json
import logging
import random
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self._failure_count = 0
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._opened_at = 0.0

    def record_success(self):
        self._failure_count = 0
        if self._state != "CLOSED":
            self._state = "CLOSED"
            logger.info("CircuitBreaker: closed")

    def record_failure(self):
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"
            self._opened_at = time.time()
            logger.warning("CircuitBreaker: opened due to failures")

    def allows_request(self) -> bool:
        if self._state == "CLOSED":
            return True
        if self._state == "OPEN":
            if time.time() - self._opened_at > self.recovery_seconds:
                self._state = "HALF_OPEN"
                logger.info("CircuitBreaker: moving to HALF_OPEN")
                return True
            return False
        # HALF_OPEN
        return True


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
        # Prefer smaller/tiny fallbacks by default to avoid capacity limits
        self.fallback_models = fallback_models if fallback_models is not None else ["mistral-small", "mistral-tiny"]
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.circuit = CircuitBreaker(failure_threshold=failure_threshold, recovery_seconds=recovery_seconds)

        self._client = httpx.AsyncClient(base_url=self.api_url, headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}, timeout=60.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def _request_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            # circuit breaker check
            if not self.circuit.allows_request():
                raise HTTPException(status_code=503, detail="Service temporarily unavailable (circuit open)")

            try:
                resp = await self._client.post("/v1/chat/completions", json=payload)
            except httpx.RequestError as e:
                last_exc = e
                logger.warning("Mistral request error (attempt %s): %s", attempt, e)
                # record failure and backoff
                self.circuit.record_failure()
                if attempt == self.max_retries:
                    break
                await asyncio.sleep(self._jitter_backoff(attempt))
                continue

            status = resp.status_code
            try:
                body = resp.json()
            except Exception:
                body = resp.text

            # Handle success
            if status == 200:
                self.circuit.record_success()
                return body

            # transient errors: retry
            if status in (429, 502, 503):
                logger.warning("Mistral transient status %s: %s", status, body)
                self.circuit.record_failure()
                if attempt == self.max_retries:
                    break
                await asyncio.sleep(self._jitter_backoff(attempt))
                continue

            # invalid model -> bubble up to caller for fallback decision
            if status == 400 and isinstance(body, dict) and "Invalid model" in str(body.get("message", "")):
                # do not record as circuit failure here; caller may try fallback
                raise HTTPException(status_code=400, detail=body)

            # other client errors: do not retry
            logger.error("Mistral returned non-retriable status %s: %s", status, body)
            self.circuit.record_failure()
            raise HTTPException(status_code=502, detail={"status": status, "body": body})

        # exhausted
        logger.error("Mistral request failed after retries: %s", last_exc)
        raise HTTPException(status_code=503, detail="Mistral API unavailable after retries")

    def _jitter_backoff(self, attempt: int) -> float:
        base = self.backoff_base * (2 ** (attempt - 1))
        return min(base, 60.0) * random.random()

    async def chat(self, messages: List[dict], model: Optional[str] = None, max_tokens: int = 512, temperature: float = 0.3) -> str:
        if model is None:
            model = self.default_model

        payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}

        async with self.semaphore:
            try:
                body = await self._request_with_retry(payload)
            except HTTPException as e:
                # If invalid model, attempt fallbacks
                if e.status_code == 400 and self.fallback_models:
                    logger.info("Model invalid, attempting fallbacks: %s", self.fallback_models)
                    for fb in self.fallback_models:
                        if fb == model:
                            continue
                        try:
                            payload["model"] = fb
                            body = await self._request_with_retry(payload)
                            return self._extract_text(body)
                        except HTTPException:
                            continue
                raise

            return self._extract_text(body)

    def _extract_text(self, body: Any) -> str:
        # Expect choices[0].message.content or similar
        if isinstance(body, dict):
            choices = body.get("choices") or []
            if choices and isinstance(choices, list):
                first = choices[0]
                if isinstance(first, dict):
                    msg = first.get("message") or {}
                    if isinstance(msg, dict):
                        content = msg.get("content") or msg.get("text")
                        if isinstance(content, dict):
                            return content.get("text", "").strip()
                        if content:
                            return str(content).strip()
                    # fallback to first.text
                    text = first.get("text") or first.get("content")
                    if text:
                        return str(text).strip()
            # last resort: stringify
            try:
                return json.dumps(body, ensure_ascii=False)
            except Exception:
                return str(body)
        return str(body)
