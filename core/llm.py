"""
core/llm.py
Shared Gemini client used by every agent, the Asha chat engine and server.py.

Why this exists:
- The old code hardcoded "gemini-1.5-flash", which Google has retired (HTTP 404).
  Every call failed silently and fell back to templates, so a valid key looked "broken".
- This client calls the Gemini REST API directly (no SDK), with a timeout,
  a model fallback chain, and records the last error so /api/llm/status can show it.

Config (.env):
  GEMINI_API_KEY   required for LLM mode
  GEMINI_MODEL     optional, comma-separated list tried in order
                   default: gemini-flash-lite-latest,gemini-3.5-flash-lite,gemini-flash-latest
  GEMINI_TIMEOUT   optional, seconds per request (default 20)
"""

from __future__ import annotations
import json
import logging
import os
import threading
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODELS = "gemini-flash-lite-latest,gemini-3.5-flash-lite,gemini-flash-latest"


class LLMResponse:
    """Mimics the SDK response shape (`.text`) so existing callers keep working."""

    def __init__(self, text: str, model: str):
        self.text = text
        self.model = model


class GeminiClient:
    def __init__(self) -> None:
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.models: List[str] = [
            m.strip() for m in os.environ.get("GEMINI_MODEL", DEFAULT_MODELS).split(",") if m.strip()
        ]
        self.timeout = float(os.environ.get("GEMINI_TIMEOUT", "20"))
        self.temperature = 0.7
        self.max_output_tokens = 1024
        self._lock = threading.Lock()
        self.stats: Dict[str, Any] = {
            "calls": 0,
            "successes": 0,
            "failures": 0,
            "last_model_used": None,
            "last_error": None,
            "last_success_at": None,
        }

    @property
    def configured(self) -> bool:
        placeholder = {"", "your_gemini_api_key_here", "your_google_api_key_here"}
        return self.api_key not in placeholder

    def _post(self, model: str, prompt: str) -> str:
        url = f"{API_BASE}/{model}:generateContent"
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens,
            },
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()

    def generate_content(self, prompt: str) -> LLMResponse:
        """Try each configured model in order. Raises RuntimeError if all fail."""
        if not self.configured:
            raise RuntimeError("GEMINI_API_KEY is not set")

        errors = []
        with self._lock:
            self.stats["calls"] += 1
        for model in self.models:
            try:
                text = self._post(model, prompt)
                if not text:
                    raise RuntimeError("empty response")
                with self._lock:
                    self.stats["successes"] += 1
                    self.stats["last_model_used"] = model
                    self.stats["last_error"] = None
                    self.stats["last_success_at"] = datetime.now().isoformat()
                return LLMResponse(text, model)
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "ignore")[:200].replace("\n", " ")
                errors.append(f"{model}: HTTP {e.code} {detail}")
                # 400/401/403 = key problem; trying other models won't help
                if e.code in (400, 401, 403):
                    break
            except Exception as e:  # timeout, network, parse
                errors.append(f"{model}: {type(e).__name__}: {e}")

        msg = " | ".join(errors)
        with self._lock:
            self.stats["failures"] += 1
            self.stats["last_error"] = msg
        logger.warning(f"[GeminiClient] All models failed: {msg}")
        raise RuntimeError(msg)

    def status(self, live_test: bool = False) -> Dict[str, Any]:
        live = None
        if live_test and self.configured:
            try:
                r = self.generate_content("Reply with exactly: OK")
                live = {"ok": True, "model": r.model, "reply": r.text[:50]}
            except Exception as e:
                live = {"ok": False, "error": str(e)[:400]}
        info = {
            "configured": self.configured,
            "key_preview": (self.api_key[:6] + "…") if self.configured else None,
            "models": self.models,
            "timeout_s": self.timeout,
            **self.stats,
        }
        if live is not None:
            info["live_test"] = live
        info["mode"] = "gemini" if (self.configured and self.stats["last_error"] is None) else (
            "gemini (errors - see last_error)" if self.configured else "template-fallback (no key)"
        )
        return info


_client: Optional[GeminiClient] = None


def get_llm() -> GeminiClient:
    """Process-wide singleton. Call after load_dotenv()."""
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
