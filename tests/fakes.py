from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel

from thesisforge.llm.router import LLMRouter


class FakeLLMRouter(LLMRouter):
    """Hermetic fake for LLMRouter to avoid tautological mocking."""

    def __init__(self, settings=None, keystore_repo=None):
        super().__init__(settings, keystore_repo)
        self.recorded_prompts = []
        self.canned_response = "Fake text response"
        self.canned_json_response = {"fake_key": "fake_value"}
        self.canned_stream_tokens = ["Fake", " ", "stream", " ", "tokens"]

    async def complete(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str:
        self.recorded_prompts.append((system_prompt, prompt))
        return self.canned_response

    async def complete_json(
        self, prompt: str, system_prompt: str | None = None, response_model=None, **kwargs
    ) -> dict[str, Any] | BaseModel:
        self.recorded_prompts.append((system_prompt, prompt))

        # If the test gave us a dict to return, return it (optionally validating)
        resp = self.canned_json_response
        if response_model:
            return response_model.model_validate(resp)
        return resp

    async def stream_completion(
        self, prompt: str, system_prompt: str | None = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        self.recorded_prompts.append((system_prompt, prompt))
        for token in self.canned_stream_tokens:
            yield token
