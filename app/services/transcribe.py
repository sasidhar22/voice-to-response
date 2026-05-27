import asyncio
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
from fastapi import WebSocket, WebSocketDisconnect
from app.config import settings


class _TranscriptHandler(TranscriptResultStreamHandler):
    def __init__(self, output_stream, queue: asyncio.Queue):
        super().__init__(output_stream)
        self._queue = queue

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        for result in transcript_event.transcript.results:
            if not result.is_partial:
                text = result.alternatives[0].transcript.strip()
                if text:
                    await self._queue.put(text)


class TranscribeService:
    def __init__(self):
        self._client = TranscribeStreamingClient(region=settings.aws_region)

    async def stream(self, websocket: WebSocket, transcript_queue: asyncio.Queue) -> None:
        stream = await self._client.start_stream_transcription(
            language_code=settings.transcribe_language_code,
            media_sample_rate_hz=settings.transcribe_sample_rate,
            media_encoding="pcm",
        )
        handler = _TranscriptHandler(stream.output_stream, transcript_queue)

        async def send_audio():
            try:
                async for chunk in websocket.iter_bytes():
                    await stream.input_stream.send_audio_event(audio_chunk=chunk)
            except WebSocketDisconnect:
                pass
            finally:
                await stream.input_stream.end_stream()

        await asyncio.gather(send_audio(), handler.handle_events())
