from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.utils.log_utils import log_error

DEFAULT_MODELS = [
    os.environ.get("PRIMARY_MODEL", "gpt-5.1-mini"),
    "gpt-5-mini",
    "gpt-5-nano",
]


class ModelRouter:
    def __init__(self, api_key: Optional[str] = None, models: Optional[List[str]] = None):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            log_error("OPENAI_API_KEY not set; API calls will fail until provided.")
        self.client = OpenAI(api_key=key)
        self.models = models or DEFAULT_MODELS

    def _create_response(self, *, model: Optional[str] = None, **kwargs: Any):
        last_error = None
        candidate_models = [model] if model else self.models
        for candidate in candidate_models:
            try:
                response = self.client.responses.create(model=candidate, **kwargs)
                return response
            except Exception as exc:  # noqa: BLE001 broad but necessary for fallback
                last_error = exc
                log_error(f"Model {candidate} failed: {exc}")
                continue
        raise RuntimeError(f"All model calls failed. Last error: {last_error}")

    def complete(
        self,
        prompt: str,
        json_mode: bool = False,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload = {
            "input": [{"role": "user", "content": prompt}],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        response = self._create_response(model=model, **payload)
        return self._extract_output(response)

    def stream_chat(self, messages: List[Dict[str, str]], model: Optional[str] = None):
        chosen_model = model or self.models[0]
        return self.client.responses.create(
            model=chosen_model,
            input=messages,
            stream=True,
        )

    @staticmethod
    def _extract_output(response: Any) -> Dict[str, Any]:
        text = getattr(response, "output_text", None)
        if text:
            return {"output_text": text}
        if hasattr(response, "output"):  # type: ignore[attr-defined]
            try:
                first = response.output[0]
                if hasattr(first, "content") and first.content:
                    maybe_text = getattr(first.content[0], "text", None)
                    if maybe_text and hasattr(maybe_text, "value"):
                        return {"output_text": maybe_text.value}
            except Exception:  # noqa: BLE001
                pass
            return {"output_text": str(response.output)}
        return {"output_text": ""}
