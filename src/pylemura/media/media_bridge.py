"""Media bridge — mirrors lemura/src/media/MediaBridge.ts"""
from __future__ import annotations
from typing import AsyncIterator, Optional

from pylemura.types.adapters import (
    AudioChunk,
    ImageGenRequest,
    ImageGenResponse,
    IProviderAdapter,
    SynthesisRequest,
    TranscriptionRequest,
    TranscriptionResponse,
    VisionRequest,
    VisionResponse,
)


class MediaBridge:
    def __init__(self, adapter: IProviderAdapter) -> None:
        self._adapter = adapter

    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
        return await self._adapter.transcribe(request)

    async def synthesize(self, request: SynthesisRequest) -> AsyncIterator[AudioChunk]:
        return await self._adapter.synthesize(request)

    async def synthesize_to_array(self, request: SynthesisRequest) -> list[AudioChunk]:
        chunks: list[AudioChunk] = []
        async for chunk in await self._adapter.synthesize(request):
            chunks.append(chunk)
        return chunks

    async def describe_image(self, request: VisionRequest) -> VisionResponse:
        return await self._adapter.describe_image(request)

    async def generate_image(self, request: ImageGenRequest) -> ImageGenResponse:
        return await self._adapter.generate_image(request)

    def supports_vision(self) -> bool:
        info = self._adapter.get_model_info()
        return getattr(info, "supports_vision", False)
