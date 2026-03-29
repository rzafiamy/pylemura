"""OpenAI-compatible adapter — mirrors lemura/src/adapters/OpenAICompatibleAdapter.ts
Zero external dependencies: uses only urllib + http.client from stdlib.
"""
from __future__ import annotations
import asyncio
import http.client
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional

from pylemura.types.adapters import (
    AudioChunk,
    CompletionChunk,
    CompletionRequest,
    CompletionResponse,
    IProviderAdapter,
    ImageGenRequest,
    ImageGenResponse,
    ModelInfo,
    NormalizedMessage,
    SynthesisRequest,
    TokenUsage,
    ToolCall,
    TranscriptionRequest,
    TranscriptionResponse,
    VisionRequest,
    VisionResponse,
)
from pylemura.types.errors import LemuraAdapterError


@dataclass
class OpenAICompatibleAdapterConfig:
    base_url: str = "https://api.openai.com/v1"
    api_key: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    extra_headers: dict[str, str] = field(default_factory=dict)


class OpenAICompatibleAdapter(IProviderAdapter):
    NAME = "openai_compatible"
    VERSION = "1.1.0"

    def __init__(self, config: Optional[OpenAICompatibleAdapterConfig] = None) -> None:
        self._cfg = config or OpenAICompatibleAdapterConfig()
        if not self._cfg.api_key:
            self._cfg.api_key = (
                os.environ.get("OPENAI_API_KEY")
                or os.environ.get("API_KEY")
                or ""
            )

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def version(self) -> str:
        return self.VERSION

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        payload = self._build_payload(request, stream=False)
        data = await self._post_json("/chat/completions", payload)
        return self._parse_completion(data)

    async def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]:
        payload = self._build_payload(request, stream=True)
        async for chunk in self._post_stream("/chat/completions", payload):
            yield chunk

    # ------------------------------------------------------------------
    # Vision
    # ------------------------------------------------------------------

    async def describe_image(self, request: VisionRequest) -> VisionResponse:
        import base64
        content: list[dict[str, Any]] = [{"type": "text", "text": request.prompt}]
        if request.image_url:
            content.append({"type": "image_url", "image_url": {"url": request.image_url}})
        elif request.image_data:
            b64 = base64.b64encode(request.image_data).decode()
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        payload = {
            "model": request.model or self._cfg.default_model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 1000,
        }
        data = await self._post_json("/chat/completions", payload)
        text = data["choices"][0]["message"].get("content", "")
        return VisionResponse(description=text, raw=data)

    # ------------------------------------------------------------------
    # Image generation
    # ------------------------------------------------------------------

    async def generate_image(self, request: ImageGenRequest) -> ImageGenResponse:
        payload = {
            "model": request.model or "dall-e-3",
            "prompt": request.prompt,
            "size": request.size,
            "quality": request.quality,
            "n": request.n,
        }
        data = await self._post_json("/images/generations", payload)
        urls = [item.get("url", "") for item in data.get("data", [])]
        b64s = [item.get("b64_json", "") for item in data.get("data", [])]
        return ImageGenResponse(urls=urls, b64_images=b64s, raw=data)

    # ------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------

    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
        # Use multipart/form-data upload
        loop = asyncio.get_event_loop()
        data = await asyncio.wait_for(
            loop.run_in_executor(None, self._transcribe_sync, request),
            timeout=self._cfg.timeout,
        )
        return TranscriptionResponse(text=data.get("text", ""), language=data.get("language"))

    def _transcribe_sync(self, request: TranscriptionRequest) -> dict[str, Any]:
        boundary = "----PylemuraBoundary"
        body_parts: list[bytes] = []
        body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nwhisper-1\r\n".encode())
        body_parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"audio.wav\"\r\nContent-Type: {request.mime_type}\r\n\r\n".encode()
            + request.audio_data
            + b"\r\n"
        )
        if request.language:
            body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n{request.language}\r\n".encode())
        body_parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(body_parts)

        headers = {
            **self._auth_headers(),
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        return self._http_post_sync(f"{self._cfg.base_url}/audio/transcriptions", headers, body)

    # ------------------------------------------------------------------
    # Synthesis (streaming audio)
    # ------------------------------------------------------------------

    async def synthesize(self, request: SynthesisRequest) -> AsyncIterator[AudioChunk]:
        payload = {
            "model": "tts-1",
            "input": request.text,
            "voice": request.voice or "alloy",
            "speed": request.speed,
            "response_format": request.format,
        }
        loop = asyncio.get_event_loop()
        data = await asyncio.wait_for(
            loop.run_in_executor(None, self._post_bytes_sync, "/audio/speech", payload),
            timeout=self._cfg.timeout,
        )

        async def _gen() -> AsyncIterator[AudioChunk]:
            yield AudioChunk(data=data, is_final=True)

        return _gen()

    def _post_bytes_sync(self, path: str, payload: dict[str, Any]) -> bytes:
        body = json.dumps(payload).encode()
        headers = {**self._auth_headers(), "Content-Type": "application/json"}
        url = self._cfg.base_url.rstrip("/") + path
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self._cfg.timeout) as resp:
            return resp.read()

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            id=self._cfg.default_model,
            context_window=128_000,
            supports_tools=True,
            supports_vision="vision" in self._cfg.default_model or "gpt-4" in self._cfg.default_model,
            supports_streaming=True,
        )

    async def health_check(self) -> bool:
        try:
            await self._post_json(
                "/chat/completions",
                {
                    "model": self._cfg.default_model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                },
            )
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internal HTTP helpers (urllib — zero external deps)
    # ------------------------------------------------------------------

    def _build_payload(self, request: CompletionRequest, stream: bool) -> dict[str, Any]:
        messages = [self._serialize_message(m) for m in request.messages]
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": stream,
        }
        if request.tools:
            payload["tools"] = request.tools
            payload["tool_choice"] = "auto"
        if request.stop:
            payload["stop"] = request.stop
        payload.update(request.extra)
        return payload

    def _serialize_message(self, msg: NormalizedMessage) -> dict[str, Any]:
        d: dict[str, Any] = {"role": msg.role}
        if isinstance(msg.content, list):
            d["content"] = [
                {"type": b.type, **({"text": b.text} if b.text else {}), **({"image_url": b.image_url} if b.image_url else {})}
                for b in msg.content
            ]
        else:
            d["content"] = msg.content
        if msg.tool_calls:
            d["tool_calls"] = [
                {"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": tc.arguments}}
                for tc in msg.tool_calls
            ]
        if msg.tool_call_id:
            d["tool_call_id"] = msg.tool_call_id
        if msg.name:
            d["name"] = msg.name
        return d

    def _parse_completion(self, data: dict[str, Any]) -> CompletionResponse:
        choice = data["choices"][0]
        message = choice.get("message", {})
        content = message.get("content") or ""
        finish_reason = choice.get("finish_reason", "stop")

        tool_calls: list[ToolCall] = []
        for tc in message.get("tool_calls") or []:
            fn = tc.get("function", {})
            tool_calls.append(ToolCall(
                id=tc.get("id", ""),
                name=fn.get("name", ""),
                arguments=fn.get("arguments", "{}"),
            ))

        usage_raw = data.get("usage") or {}
        usage = TokenUsage(
            prompt_tokens=usage_raw.get("prompt_tokens", 0),
            completion_tokens=usage_raw.get("completion_tokens", 0),
            total_tokens=usage_raw.get("total_tokens", 0),
        )

        return CompletionResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            model=data.get("model", ""),
            raw=data,
        )

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        loop = asyncio.get_event_loop()
        body = json.dumps(payload).encode()
        headers = {**self._auth_headers(), "Content-Type": "application/json"}
        url = self._cfg.base_url.rstrip("/") + path

        last_error: Exception = RuntimeError("No attempts made")
        for attempt in range(self._cfg.max_retries):
            try:
                data = await asyncio.wait_for(
                    loop.run_in_executor(None, self._http_post_sync, url, headers, body),
                    timeout=self._cfg.timeout,
                )
                return data
            except LemuraAdapterError as e:
                if "429" in str(e) or "503" in str(e):
                    last_error = e
                    await asyncio.sleep(self._cfg.retry_delay * (2 ** attempt))
                    continue
                raise
            except asyncio.TimeoutError:
                last_error = LemuraAdapterError(
                    f"Request to {path} timed out",
                    problem=f"No response within {self._cfg.timeout}s",
                    hints=["Check your network connection", "Increase timeout in config"],
                )
                break
        raise last_error

    def _http_post_sync(self, url: str, headers: dict[str, str], body: bytes) -> dict[str, Any]:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self._cfg.timeout) as resp:
                raw = resp.read().decode()
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode()
            except Exception:
                pass
            raise LemuraAdapterError(
                f"HTTP {e.code}: {e.reason}",
                problem=error_body[:500] if error_body else f"HTTP error {e.code}",
                hints=self._error_hints(e.code),
            ) from e
        except Exception as e:
            raise LemuraAdapterError(str(e)) from e

    async def _post_stream(self, path: str, payload: dict[str, Any]) -> AsyncIterator[CompletionChunk]:
        """Stream SSE chunks from the API using asyncio + http.client in a thread."""
        url = self._cfg.base_url.rstrip("/") + path
        body = json.dumps(payload).encode()
        headers = {**self._auth_headers(), "Content-Type": "application/json"}

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        def _read_stream():
            parsed = urllib.parse.urlparse(url)
            use_ssl = parsed.scheme == "https"
            host = parsed.netloc
            path_qs = parsed.path + (f"?{parsed.query}" if parsed.query else "")

            conn_cls = http.client.HTTPSConnection if use_ssl else http.client.HTTPConnection
            conn = conn_cls(host, timeout=self._cfg.timeout)
            try:
                conn.request("POST", path_qs, body=body, headers=headers)
                resp = conn.getresponse()
                if resp.status >= 400:
                    error_body = resp.read().decode()
                    loop.call_soon_threadsafe(queue.put_nowait, f"__error__:{resp.status}:{error_body[:200]}")
                    return
                while True:
                    line = resp.readline()
                    if not line:
                        break
                    loop.call_soon_threadsafe(queue.put_nowait, line.decode("utf-8"))
            finally:
                conn.close()
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        # Run HTTP in background thread
        loop.run_in_executor(None, _read_stream)

        # Accumulate partial tool_call deltas
        tool_call_acc: dict[int, dict[str, Any]] = {}

        while True:
            line = await queue.get()
            if line is None:
                break
            line = line.strip()
            if not line:
                continue
            if line.startswith("__error__:"):
                parts = line.split(":", 2)
                raise LemuraAdapterError(
                    f"Stream error HTTP {parts[1]}",
                    problem=parts[2] if len(parts) > 2 else "",
                    hints=self._error_hints(int(parts[1]) if parts[1].isdigit() else 0),
                )
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk_data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            choice = chunk_data.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            finish_reason = choice.get("finish_reason")

            text_delta = delta.get("content") or ""

            # Accumulate tool_call deltas
            tc_delta_info: Optional[dict[str, Any]] = None
            for tc in delta.get("tool_calls") or []:
                idx = tc.get("index", 0)
                if idx not in tool_call_acc:
                    tool_call_acc[idx] = {"id": tc.get("id", ""), "name": "", "arguments": ""}
                if tc.get("id"):
                    tool_call_acc[idx]["id"] = tc["id"]
                fn = tc.get("function", {})
                if fn.get("name"):
                    tool_call_acc[idx]["name"] += fn["name"]
                if fn.get("arguments"):
                    tool_call_acc[idx]["arguments"] += fn["arguments"]
                tc_delta_info = {"index": idx, "delta": tc}

            yield CompletionChunk(
                delta=text_delta,
                tool_call_delta=tc_delta_info,
                finish_reason=finish_reason,
            )

    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._cfg.api_key:
            headers["Authorization"] = f"Bearer {self._cfg.api_key}"
        headers.update(self._cfg.extra_headers)
        return headers

    @staticmethod
    def _error_hints(code: int) -> list[str]:
        if code == 401:
            return ["Check your API key", "Ensure OPENAI_API_KEY is set correctly"]
        if code == 429:
            return ["Rate limit exceeded — reduce request frequency", "Check your quota"]
        if code == 503:
            return ["Service temporarily unavailable — retry later"]
        return []
