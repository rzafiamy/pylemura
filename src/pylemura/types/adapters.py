"""Provider adapter interfaces — mirrors lemura/src/types/adapters.ts"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Literal, Optional


MessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass
class ContentBlock:
    type: str  # "text" | "image_url" | ...
    text: Optional[str] = None
    image_url: Optional[dict[str, str]] = None
    data: Optional[Any] = None


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # JSON string


@dataclass
class ToolResult:
    tool_call_id: str
    content: str


@dataclass
class NormalizedMessage:
    role: MessageRole
    content: str | list[ContentBlock]
    tool_calls: Optional[list[ToolCall]] = None
    tool_call_id: Optional[str] = None  # for role='tool'
    name: Optional[str] = None           # for role='tool'


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class CompletionRequest:
    model: str
    messages: list[NormalizedMessage]
    tools: list[dict[str, Any]] = field(default_factory=list)
    max_tokens: int = 2000
    temperature: float = 0.7
    stream: bool = False
    stop: Optional[list[str]] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""
    raw: Optional[Any] = None


@dataclass
class CompletionChunk:
    delta: str = ""
    tool_call_delta: Optional[dict[str, Any]] = None
    finish_reason: Optional[str] = None
    index: int = 0


@dataclass
class ModelInfo:
    id: str
    context_window: int
    supports_tools: bool = True
    supports_vision: bool = False
    supports_streaming: bool = True


@dataclass
class TranscriptionRequest:
    audio_data: bytes
    mime_type: str = "audio/wav"
    language: Optional[str] = None


@dataclass
class TranscriptionResponse:
    text: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = None


@dataclass
class SynthesisRequest:
    text: str
    voice: Optional[str] = None
    speed: float = 1.0
    format: str = "mp3"


@dataclass
class AudioChunk:
    data: bytes
    is_final: bool = False


@dataclass
class VisionRequest:
    image_data: Optional[bytes] = None
    image_url: Optional[str] = None
    prompt: str = "Describe this image."
    model: Optional[str] = None


@dataclass
class VisionResponse:
    description: str
    raw: Optional[Any] = None


@dataclass
class ImageGenRequest:
    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    n: int = 1
    model: Optional[str] = None


@dataclass
class ImageGenResponse:
    urls: list[str] = field(default_factory=list)
    b64_images: list[str] = field(default_factory=list)
    raw: Optional[Any] = None


class IProviderAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...

    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]: ...

    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
        raise NotImplementedError("This adapter does not support transcription")

    async def synthesize(self, request: SynthesisRequest) -> AsyncIterator[AudioChunk]:
        raise NotImplementedError("This adapter does not support synthesis")

    async def describe_image(self, request: VisionRequest) -> VisionResponse:
        raise NotImplementedError("This adapter does not support vision")

    async def generate_image(self, request: ImageGenRequest) -> ImageGenResponse:
        raise NotImplementedError("This adapter does not support image generation")

    def estimate_tokens(self, text: str) -> int:
        # Rough approximation: ~4 chars per token
        return max(1, len(text) // 4)

    @abstractmethod
    def get_model_info(self) -> ModelInfo: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
