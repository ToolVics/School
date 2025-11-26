from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from app.utils.log_utils import log_error


class ModelRouter:
    def __init__(self, api_key: Optional[str] = None, models: Optional[List[str]] = None):
        # Ensure .env is loaded even if config was not imported first (e.g., direct CLI usage)
        dotenv_path = find_dotenv()
        if dotenv_path:
            load_dotenv(dotenv_path)

        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            message = (
                "OPENAI_API_KEY not set; please set it in your environment or .env file before running the pipeline."
            )
            log_error(message)
            raise RuntimeError(message)
        self.client = OpenAI(api_key=key)
        self.models = self._build_model_preference(models)

    def _create_response(self, *, model: Optional[str] = None, **kwargs: Any):
        last_error = None
        candidate_models = self._combine_candidates(model)
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
        last_error = None
        for candidate in self._combine_candidates(model):
            try:
                return self.client.responses.create(
                    model=candidate,
                    input=messages,
                    stream=True,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                log_error(f"Stream model {candidate} failed: {exc}")
                continue
        raise RuntimeError(f"All stream model calls failed. Last error: {last_error}")

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

    @staticmethod
    def _build_model_preference(models_override: Optional[List[str]] = None) -> List[str]:
        base = models_override or [
            os.environ.get("PRIMARY_MODEL", "gpt-5.1-mini"),
            "gpt-5-mini",
            "gpt-5-nano",
        ]
        ordered: List[str] = []
        for model_name in base:
            if model_name and model_name not in ordered:
                ordered.append(model_name)
        return ordered

    def _combine_candidates(self, preferred: Optional[str]) -> List[str]:
        if preferred:
            candidates = [preferred] + [m for m in self.models if m != preferred]
        else:
            candidates = list(self.models)
        return [c for c in candidates if c]
