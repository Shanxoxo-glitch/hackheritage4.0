"""
Client for Sohon's perception scoring service (services/scoring, port 8100).

    frontend / orchestrator  ->  backend  ->  scoring :8100  ->  distress + threat + voice

Contracts #1-3 (contracts/api-contracts.md); response field names are consumed verbatim
by app/api/v1/perception.py and stored on the DistressScore row.

Design rules
  * never let a scoring outage fail a case: every method raises ScoringUnavailable and the
    caller degrades to its own heuristic (the scoring service itself returns HTTP 503
    {"error": "model_unavailable", "signal": ...} when one model cannot be loaded).
  * no retries beyond one: the caller is on a request path.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger("scoring_client")


class ScoringUnavailable(RuntimeError):
    """Scoring service unreachable, timed out, or reported a model as unavailable."""


class ScoringClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.SCORING_URL).rstrip("/")
        self.timeout = timeout if timeout is not None else settings.SCORING_TIMEOUT_SECONDS

    async def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=payload)
        except Exception as exc:                                   # connect error / timeout / DNS
            raise ScoringUnavailable(f"{type(exc).__name__}: {exc}") from exc
        if res.status_code == 503:
            body = _safe_json(res)
            raise ScoringUnavailable(f"model_unavailable: {body.get('signal')} ({body.get('detail')})")
        if res.status_code >= 400:
            raise ScoringUnavailable(f"HTTP {res.status_code}: {res.text[:200]}")
        return res.json()

    async def health(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/healthz")
                res.raise_for_status()
                return res.json()
        except Exception as exc:
            raise ScoringUnavailable(f"{type(exc).__name__}: {exc}") from exc

    async def score_text(self, text: str, interaction_id: str | None = None) -> dict:
        """Contract #1 -> {"sentiment": {...}, "threat": {...}, "flags": [...], ...}"""
        return await self._post("/v1/signals/text", {"text": text, "interaction_id": interaction_id})

    async def score_threat(self, text: str, interaction_id: str | None = None) -> dict:
        """Contract #3 -> {"threat": {...}, ...}"""
        return await self._post("/v1/signals/threat", {"text": text, "interaction_id": interaction_id})

    async def score_voice_base64(self, audio_base64: str, interaction_id: str | None = None) -> dict:
        """Contract #2 -> {"voice": {...}, ...}"""
        return await self._post("/v1/signals/voice", {"audio_base64": audio_base64,
                                                      "interaction_id": interaction_id})


def _safe_json(res) -> dict:
    try:
        body = res.json()
        return body if isinstance(body, dict) else {"detail": str(body)[:200]}
    except Exception:
        return {"detail": res.text[:200]}


scoring_client = ScoringClient()
