import asyncio
from typing import AsyncIterable, Callable
from app.core.interfaces import TelephonyAdapter
from app.core.schemas import CallMetadata, AudioChunk

class AvayaAdapter(TelephonyAdapter):
    async def initCall(self, callId: str, metadata: CallMetadata) -> None:
        print(f"[Avaya] Initializing call {callId} with metadata: {metadata}")

    async def streamAudio(self) -> AsyncIterable[AudioChunk]:
        yield AudioChunk(data=b'mock rtp payload')

    async def sendAudio(self, audio: bytes) -> None:
        print(f"[Avaya] Sending {len(audio)} bytes of audio over SIP")

    async def transfer(self, agentId: str, contextSummary: str) -> None:
        print(f"[Avaya] Warm transfer to agent {agentId} via AES. Context: {contextSummary}")

    async def hangup(self, callId: str) -> None:
        print(f"[Avaya] Sending SIP BYE for call {callId}")

    def onDTMF(self, handler: Callable[[str], None]) -> None:
        print("[Avaya] Registered DTMF handler.")

class TwilioAdapter(TelephonyAdapter):
    async def initCall(self, callId: str, metadata: CallMetadata) -> None:
        print(f"[Twilio] Call started {callId}. ANI: {metadata.ani}")

    async def streamAudio(self) -> AsyncIterable[AudioChunk]:
        yield AudioChunk(data=b'mock websocket payload')

    async def sendAudio(self, audio: bytes) -> None:
        print(f"[Twilio] Pushing {len(audio)} bytes to Media Stream websocket")

    async def transfer(self, agentId: str, contextSummary: str) -> None:
        print(f"[Twilio] <Dial><Queue>{agentId}</Queue></Dial>")

    async def hangup(self, callId: str) -> None:
        print(f"[Twilio] Ending call {callId}")

    def onDTMF(self, handler: Callable[[str], None]) -> None:
        print("[Twilio] <Gather> registered.")
