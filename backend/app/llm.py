import json

from .config import settings


def generate(system: str, user: str, max_tokens: int = 1500) -> str:
    """One function for both providers, so the rest of the app doesn't care which is used."""
    provider = settings.llm_provider

    if provider == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=90_000),
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                temperature=0.1,
            ),
        )
        return response.text or ""

    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in message.content if block.type == "text")

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}")


def parse_json(raw: str) -> dict:
    """LLMs sometimes wrap JSON in ```json fences or add chatter; extract the object."""
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM output")
    return json.loads(raw[start : end + 1])

import time

_generate_once = generate


def generate(system: str, user: str, max_tokens: int = 1500) -> str:
    """Retry when Google is temporarily overloaded or slow."""
    transient_markers = ("503", "504", "429", "500", "UNAVAILABLE", "DEADLINE_EXCEEDED")
    for attempt in range(3):
        try:
            return _generate_once(system, user, max_tokens)
        except Exception as exc:
            transient = any(m in str(exc) for m in transient_markers)
            if not transient or attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))