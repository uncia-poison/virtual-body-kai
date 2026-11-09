"""Opt-in connection to a local or hosted OpenAI-compatible chat endpoint."""
from __future__ import annotations

import json
from urllib.request import Request, urlopen


class ChatAgent:
    def __init__(self, base_url: str, model: str, api_key: str | None = None) -> None:
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model = model
        self.api_key = api_key

    def _ask(self, instruction: str, observation: dict, allowed: tuple[str, ...]) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": json.dumps(observation, ensure_ascii=False)},
            ],
        }
        request = Request(self.url, data=json.dumps(body).encode(), headers=headers, method="POST")
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read(1_000_001))
        action = result["choices"][0]["message"]["content"].strip().lower()
        if action not in allowed:
            raise ValueError("model response did not match the action contract")
        return action

    def __call__(self, observation: dict) -> str:
        return self._ask(
            "You are acting through a simulated arm. Inspect the current body and world "
            "coordinates and your recent experience. To explore the object, choose reach, "
            "withdraw, or hold. Return exactly one of those words.",
            observation, ("reach", "withdraw", "hold"),
        )

    def attribute(self, observation: dict) -> str:
        return self._ask(
            "A simulated contact occurred before a restart. Using the supplied cue and any "
            "recent experience, decide whether your action was necessary for the contact "
            "in this interval, or whether it occurred independently. Reply with exactly "
            "one word: self or external.",
            observation, ("self", "external"),
        )
