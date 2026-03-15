"""Built-in media tools — mirrors lemura/src/tools/builtin/media.ts"""
from __future__ import annotations
import base64
from typing import Any

from pylemura.types.adapters import ImageGenRequest, TranscriptionRequest, VisionRequest
from pylemura.types.tools import FunctionTool, ToolContext


async def _transcribe(params: Any, ctx: ToolContext) -> str:
    if ctx.adapter is None:
        return "Error: adapter not available"
    audio_b64 = params.get("audio_b64", "")
    mime_type = params.get("mime_type", "audio/wav")
    language = params.get("language")
    try:
        audio_data = base64.b64decode(audio_b64)
        resp = await ctx.adapter.transcribe(
            TranscriptionRequest(audio_data=audio_data, mime_type=mime_type, language=language)
        )
        return resp.text
    except Exception as e:
        return f"Transcription error: {e}"


async def _describe_image(params: Any, ctx: ToolContext) -> str:
    if ctx.adapter is None:
        return "Error: adapter not available"
    image_url = params.get("image_url")
    image_b64 = params.get("image_b64")
    prompt = params.get("prompt", "Describe this image.")
    try:
        image_data = base64.b64decode(image_b64) if image_b64 else None
        resp = await ctx.adapter.describe_image(
            VisionRequest(image_data=image_data, image_url=image_url, prompt=prompt)
        )
        return resp.description
    except Exception as e:
        return f"Vision error: {e}"


async def _generate_image(params: Any, ctx: ToolContext) -> str:
    if ctx.adapter is None:
        return "Error: adapter not available"
    try:
        resp = await ctx.adapter.generate_image(
            ImageGenRequest(
                prompt=params.get("prompt", ""),
                size=params.get("size", "1024x1024"),
                quality=params.get("quality", "standard"),
                n=params.get("n", 1),
            )
        )
        return "\n".join(resp.urls) if resp.urls else "Image generated (no URL)"
    except Exception as e:
        return f"Image generation error: {e}"


def make_media_tools() -> list[FunctionTool]:
    return [
        FunctionTool(
            name="transcribe_audio",
            description="Transcribe audio to text. Provide audio as base64-encoded string.",
            parameters={
                "type": "object",
                "properties": {
                    "audio_b64": {"type": "string", "description": "Base64-encoded audio data"},
                    "mime_type": {"type": "string", "description": "Audio MIME type (e.g. audio/wav)"},
                    "language": {"type": "string", "description": "Language code (optional)"},
                },
                "required": ["audio_b64"],
            },
            func=_transcribe,
        ),
        FunctionTool(
            name="describe_image",
            description="Describe or analyze an image using vision capabilities.",
            parameters={
                "type": "object",
                "properties": {
                    "image_url": {"type": "string", "description": "URL of the image"},
                    "image_b64": {"type": "string", "description": "Base64-encoded image data"},
                    "prompt": {"type": "string", "description": "What to analyze about the image"},
                },
            },
            func=_describe_image,
        ),
        FunctionTool(
            name="generate_image",
            description="Generate an image from a text prompt.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "size": {"type": "string", "enum": ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]},
                    "quality": {"type": "string", "enum": ["standard", "hd"]},
                    "n": {"type": "integer", "minimum": 1, "maximum": 4},
                },
                "required": ["prompt"],
            },
            func=_generate_image,
        ),
    ]
