"""LLM Router for BYOK multi-provider orchestration using LiteLLM and tenacity."""

import json
import os
from collections.abc import AsyncGenerator
from typing import Any

import litellm
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_none,
    wait_random_exponential,
)

from thesisforge.config import AppSettings, get_settings
from thesisforge.core.logging import get_logger
from thesisforge.exceptions import LLMProviderError
from thesisforge.repository.keystore_repository import SecureKeyStoreRepository

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
os.environ["LITELLM_TELEMETRY"] = "False"

litellm.telemetry = False
litellm.suppress_debug_info = True
litellm.drop_params = True

logger = get_logger(__name__)


class LLMRouter:
    """Orchestrates LLM calls across multiple providers with automatic retries and BYOK."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        keystore_repo: SecureKeyStoreRepository | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.keystore_repo = keystore_repo

    async def resolve_api_key(self, provider: str) -> str | None:
        """Resolve API key from keystore database, falling back to environment settings."""
        normalized = provider.strip().lower()

        # 1. Try keystore repository if available
        if self.keystore_repo is not None:
            db_key = await self.keystore_repo.get_key(normalized)
            if db_key:
                return db_key

        # 2. Fall back to settings / env variables
        if normalized in ("openrouter", "openrouter_api_key"):
            return self.settings.openrouter_api_key
        if normalized in ("gemini", "google", "gemini_api_key"):
            return self.settings.gemini_api_key
        if normalized in ("openai", "openai_api_key"):
            return self.settings.openai_api_key
        if normalized in ("groq", "groq_api_key"):
            return self.settings.groq_api_key
        if normalized in ("nvidia", "nim", "nvidia_nim_api_key"):
            return self.settings.nvidia_nim_api_key

        return None

    def _normalize_model_name(self, model: str, provider: str) -> str:
        """Normalize model identifier for LiteLLM routing."""
        normalized_provider = provider.strip().lower()
        if "/" in model:
            return model

        if normalized_provider == "openrouter":
            return f"openrouter/{model}"
        if normalized_provider == "gemini":
            return f"gemini/{model}"
        if normalized_provider == "groq":
            return f"groq/{model}"
        if normalized_provider == "ollama":
            return f"ollama/{model}"
        return model

    async def _execute_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        api_key: str | None,
        response_format: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Internal wrapped completion with dynamic tenacity retry logic."""
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "timeout": self.settings.timeout_seconds,
            **kwargs,
        }
        if api_key:
            params["api_key"] = api_key
        if response_format:
            params["response_format"] = response_format

        is_test = self.settings.environment == "test"
        wait_strategy = wait_none() if is_test else wait_random_exponential(min=1, max=8)
        attempts = 1 if is_test else self.settings.max_retries

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(attempts),
            wait=wait_strategy,
            retry=retry_if_exception_type((Exception,)),
            reraise=True,
        ):
            with attempt:
                return await litellm.acompletion(**params)

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.3,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """Execute a text completion request."""
        target_provider = provider or self.settings.default_provider
        raw_model = model or self.settings.default_model
        resolved_model = self._normalize_model_name(raw_model, target_provider)
        api_key = await self.resolve_api_key(target_provider)

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response_format = {"type": "json_object"} if json_mode else None

        try:
            logger.info(
                "Dispatching LLM completion request.",
                extra={
                    "model": resolved_model,
                    "provider": target_provider,
                    "json_mode": json_mode,
                },
            )
            response = await self._execute_completion(
                model=resolved_model,
                messages=messages,
                temperature=temperature,
                api_key=api_key,
                response_format=response_format,
                **kwargs,
            )
            content = str(response.choices[0].message.content or "")
            return content
        except Exception as err:
            logger.exception(
                "LLM completion failed.", extra={"model": resolved_model, "error": str(err)}
            )
            raise LLMProviderError(f"Error en proveedor LLM ({resolved_model}): {err}") from err

    async def complete_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute completion and parse result strictly as JSON dict."""
        raw_text = await self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            temperature=temperature,
            json_mode=True,
            **kwargs,
        )

        cleaned = raw_text.strip()
        # Strip markdown code blocks if wrapped in ```json ... ```
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            return {"data": parsed}
        except json.JSONDecodeError as err:
            logger.warning(
                "JSON decode failed on LLM response, attempting fallback extraction.",
                extra={"raw_text": raw_text},
            )
            raise LLMProviderError(f"El modelo no retornó un JSON válido: {err}") from err

    async def stream_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream completion tokens asynchronously."""
        target_provider = provider or self.settings.default_provider
        raw_model = model or self.settings.default_model
        resolved_model = self._normalize_model_name(raw_model, target_provider)
        api_key = await self.resolve_api_key(target_provider)

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await litellm.acompletion(
                model=resolved_model,
                messages=messages,
                temperature=temperature,
                api_key=api_key,
                stream=True,
                timeout=self.settings.timeout_seconds,
                **kwargs,
            )
            async for chunk in response:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta
        except Exception as err:
            logger.exception(
                "LLM streaming failed.", extra={"model": resolved_model, "error": str(err)}
            )
            raise LLMProviderError(f"Error en streaming LLM ({resolved_model}): {err}") from err
