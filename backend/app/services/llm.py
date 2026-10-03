"""
LLM Service Abstraction: Handles structured calls to configured LLM providers.
Supports OpenAI, Groq, Anthropic, and Google Gemini via backend HTTP clients.
Never exposes API keys to client browsers.
"""

import os
import json
import httpx
from typing import Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel
from app.config import settings

T = TypeVar("T", bound=BaseModel)

class LLMError(Exception):
    """Base exception for LLM operations."""
    pass

class LLMNotConfiguredError(LLMError):
    """Raised when the required LLM provider API key is missing."""
    def __init__(self, provider: str):
        super().__init__(
            f"LLM Provider '{provider}' is not configured. "
            f"Please set the appropriate API key (e.g. OPENAI_API_KEY, GROQ_API_KEY) in .env file."
        )

class LLMService:
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        http_client: Optional[httpx.AsyncClient] = None
    ):
        self.provider = (provider or settings.LLM_PROVIDER or "openai").lower().strip()
        self.model = model or settings.LLM_MODEL or "gpt-4o-mini"
        self.timeout = timeout
        self._shared_client = http_client
        
        # Resolve API Key based on provider
        if api_key:
            self.api_key = api_key
        elif self.provider == "openai":
            self.api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        elif self.provider == "groq":
            self.api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        elif self.provider == "anthropic":
            self.api_key = settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY", "")
        elif self.provider in ["google", "gemini"]:
            self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        else:
            self.api_key = ""

    @property
    def is_configured(self) -> bool:
        """Checks if a valid, non-placeholder API key is set for the chosen provider."""
        return bool(
            self.api_key 
            and self.api_key.strip() 
            and not self.api_key.startswith("your_")
        )

    def _verify_configuration(self):
        if not self.is_configured:
            raise LLMNotConfiguredError(self.provider)

    async def generate_structured_output(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None
    ) -> T:
        """
        Sends prompt to LLM and parses response directly into target Pydantic model.
        """
        self._verify_configuration()

        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        default_system = (
            "You are an expert AI decision and research analyst for DecisionOS. "
            "Your task is to analyze user requests and return ONLY a valid JSON object matching the JSON schema below.\n"
            f"Required JSON Schema:\n{schema_json}"
        )
        sys_prompt = system_prompt or default_system

        if self.provider in ["openai", "groq"]:
            return await self._call_openai_compatible(prompt, sys_prompt, response_model)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt, sys_prompt, response_model)
        elif self.provider in ["google", "gemini"]:
            return await self._call_gemini(prompt, sys_prompt, response_model)
        else:
            raise LLMError(f"Unsupported LLM provider: {self.provider}")

    async def _call_openai_compatible(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Type[T]
    ) -> T:
        base_url = "https://api.openai.com/v1/chat/completions"
        if self.provider == "groq":
            base_url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        try:
            if self._shared_client and not self._shared_client.is_closed:
                response = await self._shared_client.post(base_url, headers=headers, json=payload)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(base_url, headers=headers, json=payload)
                
                if response.status_code == 401 or response.status_code == 403:
                    raise LLMError(f"Authentication failed for provider {self.provider}. Check API Key.")
                elif response.status_code >= 400:
                    raise LLMError(f"LLM API error ({response.status_code}): {response.text}")

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return response_model.model_validate_json(content)

        except httpx.HTTPError as exc:
            raise LLMError(f"Network error calling {self.provider} API: {str(exc)}")
        except Exception as exc:
            if isinstance(exc, LLMError):
                raise
            raise LLMError(f"Failed to process LLM response: {str(exc)}")

    async def _call_anthropic(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Type[T]
    ) -> T:
        base_url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model or "claude-3-5-sonnet-20241022",
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(base_url, headers=headers, json=payload)
                if response.status_code >= 400:
                    raise LLMError(f"Anthropic API error ({response.status_code}): {response.text}")
                data = response.json()
                content = data["content"][0]["text"]
                return response_model.model_validate_json(content)
        except Exception as exc:
            raise LLMError(f"Anthropic API call failed: {str(exc)}")

    async def _call_gemini(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Type[T]
    ) -> T:
        model_name = self.model if "gemini" in self.model else "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Request: {prompt}"}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code >= 400:
                    raise LLMError(f"Gemini API error ({response.status_code}): {response.text}")
                data = response.json()
                text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                return response_model.model_validate_json(text_content)
        except Exception as exc:
            raise LLMError(f"Gemini API call failed: {str(exc)}")
