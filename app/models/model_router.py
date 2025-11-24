from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from openai import OpenAI
from app.utils.log_utils import log_error

DEFAULT_MODELS = [
    os.environ.get('PRIMARY_MODEL', 'gpt-5.1-mini'),
    'gpt-5-mini',
    'gpt-5-nano',
]


class ModelRouter:
    def __init__(self, api_key: Optional[str] = None, models: Optional[List[str]] = None):
        key = api_key or os.environ.get('OPENAI_API_KEY')
        if not key:
            log_error('OPENAI_API_KEY not set; API calls will fail until provided.')
        self.client = OpenAI(api_key=key)
        self.models = models or DEFAULT_MODELS

    def _create_response(self, **kwargs: Any):
        last_error = None
        for model in self.models:
            try:
                response = self.client.responses.create(model=model, **kwargs)
                return response
            except Exception as exc:  # noqa: BLE001 broad but necessary for fallback
                last_error = exc
                log_error(f"Model {model} failed: {exc}")
                continue
        raise RuntimeError(f"All model calls failed. Last error: {last_error}")

    def complete(self, prompt: str, json_mode: bool = False, **kwargs: Any) -> Dict[str, Any]:
        response = self._create_response(
            input=prompt,
            response_format={'type': 'json_object'} if json_mode else None,
            **kwargs,
        )
        return self._extract_output(response)

    def stream_chat(self, messages: List[Dict[str, str]], model: Optional[str] = None):
        chosen_model = model or self.models[0]
        return self.client.responses.create(
            model=chosen_model,
            messages=messages,
            stream=True,
        )

    @staticmethod
    def _extract_output(response: Any) -> Dict[str, Any]:
        # openai v1 responses include .output_text when not streaming
        text = getattr(response, 'output_text', None)
        if text:
            return {'output_text': text}
        # fallback extraction
        if hasattr(response, 'output'):  # type: ignore[attr-defined]
            return {'output_text': str(response.output)}
        return {'output_text': ''}
