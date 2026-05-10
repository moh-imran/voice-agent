import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Response, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from app.core.config import load_config
from app.core.registry import PluginRegistry
from app.engine.context import ContextManager
from app.engine.llm import LLMOrchestrator
from app.engine.intent import IntentClassifier
from app.engine.orchestrator import ConversationLoop
from app.core.schemas import AudioChunk

from app.adapters.speech import WhisperAdapter, DeepgramAdapter, AzureTTSAdapter
from app.adapters.telephony import AvayaAdapter, TwilioAdapter, TelnyxAdapter
from app.adapters.commerce import MagentoAdapter, ShopifyAdapter
from app.adapters.crm import SalesforceAdapter, HubSpotAdapter
from app.adapters.ticket import ZendeskAdapter

from app.skills import (
    AuthSkill, OrderTrackingSkill, PlaceOrderSkill, OrderCancellationSkill,
    ProductSkill, ComplaintSkill, TicketStatusSkill, FAQSkill, HandoffSkill, SmallTalkSkill
)
from app.core.events import event_manager
from app.admin.routes import router as admin_router

app = FastAPI(title="Voice Agent API")

# --- Bootstrap ---
config = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml'))
registry = PluginRegistry.get_instance()
context_manager = ContextManager(config.redis.url)

openai_key = os.getenv("OPENAI_API_KEY", "mock-key")
llm = LLMOrchestrator(openai_key, config.llm.model)
intent_classifier = IntentClassifier(openai_key, config.llm.model)
loop = ConversationLoop(context_manager, intent_classifier, registry)

# Register Speech
registry.register_speech('whisper', WhisperAdapter(openai_key))
registry.register_speech('deepgram', DeepgramAdapter(os.getenv("DEEPGRAM_API_KEY", "mock-key")))
registry.register_speech('azure-tts', AzureTTSAdapter("mock-key", "eastus"))

# Register Telephony
if config.telephony == 'avaya': registry.register_telephony('avaya', AvayaAdapter())
if config.telephony == 'twilio': registry.register_telephony('twilio', TwilioAdapter())
if config.telephony == 'telnyx': registry.register_telephony('telnyx', TelnyxAdapter())

# Register Commerce
if config.commerce == 'magento': registry.register_commerce('magento', MagentoAdapter())
if config.commerce == 'shopify': registry.register_commerce('shopify', ShopifyAdapter())

# Register CRM
if config.crm == 'salesforce': registry.register_crm('salesforce', SalesforceAdapter())
if config.crm == 'hubspot': registry.register_crm('hubspot', HubSpotAdapter())

# Register Ticketing
if config.ticketing == 'zendesk': registry.register_ticket('zendesk', ZendeskAdapter())

# Register Skills
if 'auth' in config.skills: registry.register_skill(AuthSkill(registry))
if 'order_tracking' in config.skills: 
    registry.register_skill(OrderTrackingSkill(registry))
    registry.register_skill(PlaceOrderSkill(registry))
    registry.register_skill(OrderCancellationSkill(registry))

registry.register_skill(ProductSkill(registry))
if 'complaint' in config.skills: 
    registry.register_skill(ComplaintSkill(registry))
    registry.register_skill(TicketStatusSkill(registry))
if 'faq' in config.skills: registry.register_skill(FAQSkill(openai_key))
if 'handoff' in config.skills: registry.register_skill(HandoffSkill(registry))
registry.register_skill(SmallTalkSkill(registry))

print(f'Plugin registry initialized with {len(registry.get_all_skills())} skills.')

app.include_router(admin_router, prefix="/admin", tags=["admin"])

# --- API Endpoints ---
class TurnRequest(BaseModel):
    callId: str
    utterance: str

@app.post("/debug/turn")
async def process_turn(req: TurnRequest):
    try:
        response = await loop.process_turn(req.callId, req.utterance)
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/voice-turn")
async def process_voice_turn(callId: str, audio: UploadFile = File(...)):
    try:
        # 1. Transcribe
        speech_adapter = registry.resolve_speech('whisper')
        
        async def audio_generator():
            while chunk := await audio.read(65536):
                yield AudioChunk(data=chunk)
        
        transcript = await speech_adapter.transcribe(audio_generator())
        utterance = transcript["text"]
        
        # 2. Process via Agent
        agent_response = await loop.process_turn(callId, utterance)
        
        # 3. Synthesize response
        audio_data = await speech_adapter.synthesize(agent_response.text)
        
        import urllib.parse
        
        # Return audio and metadata in headers (URL-encoded to avoid latin-1 errors)
        return Response(
            content=audio_data, 
            media_type="audio/mpeg",
            headers={
                "X-Transcript": urllib.parse.quote(utterance),
                "X-Response-Text": urllib.parse.quote(agent_response.text),
                "X-Next-Skill": urllib.parse.quote(agent_response.nextSkill or "none"),
                "X-End-Call": "true" if agent_response.endCall else "false",
                "Access-Control-Expose-Headers": "X-Transcript, X-Response-Text, X-Next-Skill, X-End-Call"
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/session/{call_id}")
async def get_session(call_id: str):
    session = context_manager.get_session(call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    await event_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_manager.disconnect(websocket)

if __name__ == "__main__":
    print("Starting FastAPI debug server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=3000, reload=True)
