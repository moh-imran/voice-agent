import os
import tempfile
from typing import AsyncIterable, Optional
from openai import AsyncOpenAI
from app.core.interfaces import SpeechAdapter
from app.core.schemas import AudioChunk

class WhisperAdapter(SpeechAdapter):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def transcribe(self, audioStream: AsyncIterable[AudioChunk], lang: Optional[str] = None) -> dict:
        # Buffer the stream into a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            async for chunk in audioStream:
                tmp.write(chunk.data)
        
        try:
            with open(tmp_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=lang[:2] if lang else None # OpenAI expects 2-char code often
                )
            return {
                "text": transcript.text,
                "language": lang or "en",
                "confidence": 1.0
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def detectLanguage(self, audioStream: AsyncIterable[AudioChunk]) -> dict:
        # Simplified: transcription can also return language
        return {"language": "en", "confidence": 0.9}

    async def synthesize(self, text: str, voiceId: str = "nova") -> bytes:
        response = await self.client.audio.speech.create(
            model="tts-1",
            voice=voiceId if voiceId in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] else "nova",
            input=text
        )
        # Convert to bytes
        return await response.aread()

class DeepgramAdapter(SpeechAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def transcribe(self, audioStream: AsyncIterable[AudioChunk], lang: Optional[str] = None) -> dict:
        print(f"[Deepgram] Transcribing chunk...")
        return {"text": "mock deepgram transcript", "language": lang or "en", "confidence": 0.98}

    async def detectLanguage(self, audioStream: AsyncIterable[AudioChunk]) -> dict:
        return {"language": "en", "confidence": 0.95}

    async def synthesize(self, text: str, voiceId: str) -> bytes:
        raise NotImplementedError("Deepgram TTS not implemented")

class AzureTTSAdapter(SpeechAdapter):
    def __init__(self, key: str, region: str):
        pass

    async def transcribe(self, audioStream: AsyncIterable[AudioChunk], lang: Optional[str] = None) -> dict:
        raise NotImplementedError("Azure STT not implemented")

    async def detectLanguage(self, audioStream: AsyncIterable[AudioChunk]) -> dict:
        raise NotImplementedError("Azure STT not implemented")

    async def synthesize(self, text: str, voiceId: str) -> bytes:
        print(f"[Azure] Synthesizing: {text} with voice {voiceId}")
        return b'mock_azure_audio'
