"""
LLM Client — wraps OpenAI GPT-4o for natural language generation.

Set OPENAI_API_KEY in a .env file or environment to enable LLM mode.
All calls include a deterministic fallback — the system works fully without an API key.
"""
from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            try:
                from openai import OpenAI
                _client = OpenAI(api_key=api_key)
                logger.info("[LLM] OpenAI client initialised (GPT-4o mode)")
            except ImportError:
                logger.warning("[LLM] openai package not installed — deterministic fallback active")
    return _client


def llm_enabled() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY")) and _get_client() is not None


def generate_text(system_prompt: str, user_prompt: str, fallback: str, max_tokens: int = 400) -> str:
    """
    Call GPT-4o to generate a plain text response.
    Returns `fallback` if LLM is unavailable or the call fails.
    """
    client = _get_client()
    if not client:
        return fallback
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("[LLM] Call failed (%s) — deterministic fallback used", exc)
        return fallback


def generate_json(system_prompt: str, user_prompt: str, fallback: dict, max_tokens: int = 600) -> dict:
    """
    Call GPT-4o and parse the response as JSON.
    Returns `fallback` dict if LLM is unavailable, the call fails, or JSON is malformed.
    """
    client = _get_client()
    if not client:
        return fallback
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as exc:
        logger.warning("[LLM] JSON call failed (%s) — deterministic fallback used", exc)
        return fallback
