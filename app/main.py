import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from app.core.config import load_config
from app.core.registry import PluginRegistry
from app.engine.context import ContextManager
from app.engine.llm import LLMOrchestrator
from app.engine.intent import IntentClassifier
from app.engine.orchestrator import ConversationLoop

from app.adapters.speech import WhisperAdapter, DeepgramAdapter, AzureTTSAdapter
from app.adapters.telephony import AvayaAdapter, TwilioAdapter
from app.adapters.commerce import MagentoAdapter, ShopifyAdapter
from app.adapters.crm import SalesforceAdapter, HubSpotAdapter
from app.adapters.ticket import ZendeskAdapter

from app.skills import AuthSkill, OrderTrackingSkill, ComplaintSkill, FAQSkill, HandoffSkill
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
if 'order_tracking' in config.skills: registry.register_skill(OrderTrackingSkill(registry))
if 'complaint' in config.skills: registry.register_skill(ComplaintSkill(registry))
if 'faq' in config.skills: registry.register_skill(FAQSkill(openai_key))
if 'handoff' in config.skills: registry.register_skill(HandoffSkill(registry))

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

@app.get("/debug/session/{call_id}")
async def get_session(call_id: str):
    session = context_manager.get_session(call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()

if __name__ == "__main__":
    print("Starting FastAPI debug server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=3000, reload=True)
