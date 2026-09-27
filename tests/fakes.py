import json
from collections.abc import AsyncGenerator
from typing import Any
from pydantic import BaseModel

from thesisforge.llm.router import LLMRouter

class FakeLLMRouter(LLMRouter):
    """Hermetic fake for LLMRouter to avoid tautological mocking."""
    
    def __init__(self, settings: Any = None, keystore_repo: Any = None) -> None:
        super().__init__(settings, keystore_repo)
        self.recorded_prompts: list[tuple[str | None, str]] = []
        self.canned_response = "Fake text response"
        self.canned_json_response: dict[str, Any] = {"fake_key": "fake_value"}
        self.canned_stream_tokens = ["Fake", " ", "stream", " ", "tokens"]
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.2,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        self.recorded_prompts.append((system_prompt, prompt))
        return self.canned_response
        
    async def complete_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> dict[str, Any]:
        self.recorded_prompts.append((system_prompt, prompt))
        return self.canned_json_response
        
    async def stream_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        self.recorded_prompts.append((system_prompt, prompt))
        for token in self.canned_stream_tokens:
            yield token
