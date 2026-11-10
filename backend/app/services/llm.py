"""Thin LLM wrapper. Swap the provider here without touching the rest of the app."""
import json
import re

from ..config import settings


class LLM:
    def __init__(self) -> None:
        self.client = None
        if settings.anthropic_api_key:
            from anthropic import Anthropic

            self.client = Anthropic(api_key=settings.anthropic_api_key)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        resp = self.client.messages.create(
            model=settings.llm_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in resp.content if block.type == "text")

    def complete_json(self, system: str, user: str, max_tokens: int = 1024) -> dict:
        text = self.complete(
            system + "\n\nRespond with a single valid JSON object and nothing else.", user, max_tokens
        )
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise ValueError("LLM did not return JSON")
        return json.loads(match.group(0))


llm = LLM()
