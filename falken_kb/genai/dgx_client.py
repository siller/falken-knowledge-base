"""LLM-Client (DGX-namespace, jetzt OpenRouter).

OpenAI-kompatible Chat-Completions + Embeddings.
Modell-Fallback-Chain bei Rate-Limit (kostenlose Modelle gehen schnell in 429).
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from openai import APIError, OpenAI

from ..config import settings

logger = logging.getLogger(__name__)


def _parse_json_loose(text: str) -> dict | None:
    """Parse JSON tolerant gegen Markdown-Wrapper / Prefix-/Suffix-Geschwafel.

    Strategie:
    1. direkt
    2. Markdown-Fence entfernen (```json ... ```)
    3. erste { bis letzte } extrahieren
    Liefert None wenn alles scheitert.
    """
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
    # Letzter Versuch: ersten { bis letzten } extrahieren
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            return None
    return None


class DGXClient:
    """Thin wrapper um openai.OpenAI mit OpenRouter-Defaults + Modell-Fallback."""

    def __init__(self) -> None:
        if not settings.dgx_api_key:
            raise RuntimeError("DGX_API_KEY ist nicht gesetzt — bitte .env prüfen")
        self.client = OpenAI(
            base_url=settings.dgx_base_url,
            api_key=settings.dgx_api_key,
        )
        self.primary_model = settings.dgx_chat_model
        self.fallback_models = [m.strip() for m in settings.dgx_chat_fallbacks.split(",") if m.strip()]
        self.all_models = [self.primary_model] + self.fallback_models
        self.embed_model = settings.dgx_embed_model
        self.embed_dim = settings.dgx_embed_dim

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Chat-Completion mit Modell-Fallback bei Rate-Limit."""
        last_err = None
        for model in self.all_models:
            for attempt in range(3):  # 3 retries pro Modell bei transient errors
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                if response_format:
                    kwargs["response_format"] = response_format
                try:
                    resp = self.client.chat.completions.create(**kwargs)
                    if model != self.primary_model:
                        logger.info("Verwendet Fallback-Modell: %s", model)
                    return resp.choices[0].message.content or ""
                except APIError as e:
                    msg = str(e)
                    last_err = e
                    # Rate-Limit oder Provider-Error → nächstes Modell
                    if "429" in msg or "rate" in msg.lower() or "no endpoints" in msg.lower() or "provider returned error" in msg.lower():
                        logger.warning("Modell %s rate-limited/error (attempt %d), wechsle...", model, attempt+1)
                        if attempt == 0:
                            time.sleep(2)  # kurz warten + 1× retry
                            continue
                        break  # nach 2 attempts → nächstes Modell
                    raise
        raise RuntimeError(f"Alle Modelle fehlgeschlagen. Letzter Fehler: {last_err}")

    def chat_with_schema(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any],
        schema_name: str = "Response",
        max_tokens: int = 1024,
        temperature: float = 0.1,
        required_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Structured-Output via json_object + Schema-in-Prompt.

        Robust: probiert die Modell-Chain durch, bis ein Modell parsbares JSON
        liefert das alle required_keys enthält. Gibt {} zurück wenn alle scheitern
        (Handler sollen defensiv mit .get() lesen).
        """
        schema_msg = {
            "role": "system",
            "content": (
                "Antworte AUSSCHLIESSLICH mit gültigem JSON gemäß folgendem JSON-Schema. "
                "Keine Erklärungen, kein Markdown, nur JSON.\n\n"
                f"Schema (name={schema_name}):\n{json.dumps(json_schema, indent=2)}"
            ),
        }
        req_keys = required_keys or json_schema.get("required", [])
        last_text = ""
        for model in self.all_models:
            try:
                text = self._chat_single_model(
                    model,
                    [schema_msg, *messages],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
            except APIError as e:
                logger.warning("chat_with_schema: Modell %s API-Error: %s", model, str(e)[:200])
                continue
            last_text = text
            parsed = _parse_json_loose(text)
            if parsed is None:
                logger.warning("chat_with_schema: Modell %s kein parsbares JSON: %s", model, text[:200])
                continue
            missing = [k for k in req_keys if k not in parsed]
            if missing:
                logger.warning("chat_with_schema: Modell %s fehlende Keys %s in %s", model, missing, str(parsed)[:200])
                continue
            return parsed
        logger.error("chat_with_schema: kein Modell lieferte valides JSON. Letzter Versuch: %s", last_text[:300])
        return {}

    def _chat_single_model(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Single-Modell-Call mit 2 retries bei transient errors."""
        last_err = None
        for attempt in range(2):
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if response_format:
                kwargs["response_format"] = response_format
            try:
                resp = self.client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except APIError as e:
                last_err = e
                msg = str(e)
                if "429" in msg or "rate" in msg.lower() or "no endpoints" in msg.lower():
                    if attempt == 0:
                        time.sleep(2)
                        continue
                raise
        raise last_err  # type: ignore[misc]

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embeddings mit dimensions=768 (kompatibel zu pgvector(768)-Schema)."""
        if not texts:
            return []
        kwargs = {"model": self.embed_model, "input": texts}
        # text-embedding-3-small unterstützt dimensions-Parameter
        if "text-embedding-3" in self.embed_model:
            kwargs["dimensions"] = self.embed_dim
        resp = self.client.embeddings.create(**kwargs)
        return [d.embedding for d in resp.data]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
