from fastapi import APIRouter, Request, Response
from typing import Optional, Dict, Any
import httpx
import math
import logging

logger = logging.getLogger("fusion_proxy")

router = APIRouter(tags=["fusion"])

RISK_ENGINE_URL = "http://127.0.0.1:8200"

@router.post("/v1/fusion")
@router.post("/api/v1/fusion")
async def fusion_endpoint(request: Request):
    """
    Unified Gateway Proxy for Risk Engine Bayesian Fusion.
    Proxies to services/risk-engine (:8200/v1/fusion) with zero-downtime
    local Bayesian linear-Gaussian synthesis fallback.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    # 1. Forward to live Risk Engine on port 8200
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(f"{RISK_ENGINE_URL}/v1/fusion", json=body)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"Risk engine returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.debug(f"Direct connection to risk-engine on :8200 skipped ({e}), using calibrated Bayesian fallback.")

    # 2. Hermetic Bayesian Linear-Gaussian Fallback (matches services/risk-engine/app/fusion.py)
    prior_mu = 0.35
    prior_var = 0.45 ** 2
    
    # Sensor values
    sentiment_val = None
    if isinstance(body.get("sentiment"), dict) and "score" in body["sentiment"]:
        sentiment_val = float(body["sentiment"]["score"])
        
    threat_val = None
    if isinstance(body.get("threat"), dict) and "prob" in body["threat"]:
        threat_val = float(body["threat"]["prob"])
        
    voice_val = None
    if isinstance(body.get("voice_stress"), dict) and "score" in body["voice_stress"]:
        voice_val = float(body["voice_stress"]["score"])

    # Default detector sigmas
    sigmas = {
        "sentiment": 0.15,
        "threat": 0.10,
        "voice_stress": 0.20,
    }

    inv_vars = {"prior": 1.0 / prior_var}
    sum_prec_x_val = prior_mu / prior_var
    active_signals: Dict[str, float] = {}

    if sentiment_val is not None:
        p = 1.0 / (sigmas["sentiment"] ** 2)
        inv_vars["sentiment"] = p
        sum_prec_x_val += p * sentiment_val
        active_signals["sentiment"] = sentiment_val

    if threat_val is not None:
        p = 1.0 / (sigmas["threat"] ** 2)
        inv_vars["threat"] = p
        sum_prec_x_val += p * threat_val
        active_signals["threat"] = threat_val

    if voice_val is not None:
        p = 1.0 / (sigmas["voice_stress"] ** 2)
        inv_vars["voice_stress"] = p
        sum_prec_x_val += p * voice_val
        active_signals["voice_stress"] = voice_val

    total_prec = sum(inv_vars.values())
    post_var = 1.0 / total_prec
    composite = sum_prec_x_val / total_prec
    post_std = math.sqrt(post_var)

    triggers = []
    # Threat override rule
    if threat_val is not None and threat_val >= 0.90:
        composite = max(composite, 0.80)
        triggers.append("threat_force")

    # Clamping
    composite = max(0.0, min(1.0, composite))
    confidence = max(0.5, min(0.99, 1.0 - (post_std * 1.5)))

    # Classification label
    if composite >= 0.85:
        label = "CRITICAL"
    elif composite >= 0.65:
        label = "HIGH"
    elif composite >= 0.40:
        label = "ELEVATED"
    else:
        label = "LOW"

    # Normalized weights
    sensor_total_prec = sum(inv_vars[k] for k in active_signals.keys()) or 1.0
    weights = {k: round(inv_vars[k] / sensor_total_prec, 3) for k in active_signals.keys()}
    contributions = {k: round(weights[k] * active_signals[k], 3) for k in active_signals.keys()}
    top_signals = sorted(active_signals.keys(), key=lambda k: contributions.get(k, 0.0), reverse=True)

    return {
        "composite_score": round(composite, 4),
        "confidence": round(confidence, 4),
        "label": label,
        "triggers": triggers,
        "top_signals": top_signals,
        "contributions": contributions,
        "weights": weights,
        "posterior_std": round(post_std, 4),
        "conflict": False,
        "conflict_chi2": 0.0,
        "degraded": len(active_signals) < 3,
        "case_id": body.get("case_id")
    }


TRIGGER_LEXICON = [
    "die", "dying", "kill", "killing", "suicide", "hurt", "harm", "end my life", "no reason to live",
    "follow", "following", "threat", "threatened", "threatening", "locked", "weapon", "knife", "gun",
    "destroy", "attack", "panicking", "panic", "scared", "terrified", "frightened", "fear",
    "cannot take", "can't take", "overwhelmed", "hopeless", "dhamki", "chhod", "bachao", "dar",
    "court", "bail", "accused", "witness", "police", "jail", "intimidation"
]


@router.post("/v1/triggers/extract")
@router.post("/api/v1/triggers/extract")
async def extract_triggers_endpoint(request: Request):
    """
    Server-side extraction of distress & threat trigger words.
    Uses OPENROUTER_API_KEY from backend .env with google/gemma-4-31b-it:free
    and falls back to deterministic SC/ST PoA trauma lexicon.
    """
    from app.config import settings
    import re
    import json

    try:
        body = await request.json()
    except Exception:
        body = {}
    text = body.get("text", "")
    lower_text = text.lower()

    detected_triggers = [w for w in TRIGGER_LEXICON if w in lower_text]

    llm_triggers = []
    api_key = getattr(settings, "OPENROUTER_API_KEY", None)
    if api_key and text.strip():
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                or_resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://sahayak.gov.in",
                        "X-Title": "Sahayak Distress Predictor",
                    },
                    json={
                        "model": "google/gemma-4-31b-it:free",
                        "messages": [
                            {
                                "role": "user",
                                "content": (
                                    f'Analyze this victim statement under SC/ST PoA Act trauma: "{text}". '
                                    'List the top distress or threat trigger words as a JSON array of strings: '
                                    '{"trigger_words": ["word1", "word2"]}. Reply ONLY with raw JSON.'
                                ),
                            }
                        ],
                    },
                )
                if or_resp.status_code == 200:
                    data = or_resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    json_match = re.search(r"\{[\s\S]*\}", content)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        if isinstance(parsed.get("trigger_words"), list):
                            llm_triggers = [str(w).lower() for w in parsed["trigger_words"]]
        except Exception as e:
            logger.debug(f"OpenRouter trigger extraction fallback: {e}")

    final_triggers = list(dict.fromkeys(llm_triggers + detected_triggers))
    return {"trigger_words": final_triggers, "text": text}

