"""
LLM Provider abstraction layer.
Supports: Groq, OpenAI-compatible, AWS Bedrock, Local (Ollama).
"""
from abc import ABC, abstractmethod
from typing import List, Optional, AsyncGenerator
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Message:
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    latency_ms: Optional[float] = None


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def chat_with_tools(
        self,
        messages: List[Message],
        tools: List[dict],
        temperature: float = 0.1,
    ) -> LLMResponse:
        ...


class GroqProvider(LLMProvider):
    """Groq LLaMA provider."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: List[Message], temperature: float = 0.1, max_tokens: int = 4096) -> LLMResponse:
        import time
        from groq import AsyncGroq

        client = AsyncGroq(api_key=self.api_key)
        start = time.monotonic()

        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = (time.monotonic() - start) * 1000

        return LLMResponse(
            content=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens if response.usage else None,
            model=self.model,
            latency_ms=latency,
        )

    async def chat_with_tools(self, messages: List[Message], tools: List[dict], temperature: float = 0.1) -> LLMResponse:
        import time
        from groq import AsyncGroq

        client = AsyncGroq(api_key=self.api_key)
        start = time.monotonic()

        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            tools=tools,
            tool_choice="auto",
            temperature=temperature,
        )
        latency = (time.monotonic() - start) * 1000

        msg = response.choices[0].message
        content = msg.content or ""
        if msg.tool_calls:
            tool_results = [
                {"tool": tc.function.name, "arguments": tc.function.arguments}
                for tc in msg.tool_calls
            ]
            content = str(tool_results)

        return LLMResponse(
            content=content,
            tokens_used=response.usage.total_tokens if response.usage else None,
            model=self.model,
            latency_ms=latency,
        )


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible provider (OpenAI, Together.ai, Ollama, etc.)."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def chat(self, messages: List[Message], temperature: float = 0.1, max_tokens: int = 4096) -> LLMResponse:
        import time
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        start = time.monotonic()

        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens if response.usage else None,
            model=self.model,
            latency_ms=(time.monotonic() - start) * 1000,
        )

    async def chat_with_tools(self, messages, tools, temperature=0.1):
        return await self.chat(messages, temperature)


def get_llm_provider() -> LLMProvider:
    """Factory: return the configured LLM provider."""
    from app.core.config import settings

    provider = settings.AI_PROVIDER.lower()

    if provider == "groq":
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured")
        return GroqProvider(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)

    elif provider in ("openai", "openai_compatible"):
        return OpenAICompatibleProvider(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model=settings.OPENAI_MODEL,
        )

    elif provider == "local":
        return OpenAICompatibleProvider(
            api_key="ollama",
            base_url=settings.LOCAL_LLM_BASE_URL,
            model=settings.LOCAL_LLM_MODEL,
        )

    else:
        raise ValueError(f"Unknown AI provider: {provider}")
