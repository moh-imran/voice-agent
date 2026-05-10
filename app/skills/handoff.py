from typing import List
from app.core.interfaces import SkillPlugin
from app.core.schemas import ConversationContext, SkillResponse, IntentResult
from app.core.registry import PluginRegistry

class HandoffSkill(SkillPlugin):
    name = "handoff"

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def getIntents(self) -> List[str]:
        return ["talk_to_human", "agent", "handoff", "escalate"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents()

    async def execute(self, context: ConversationContext, intent: IntentResult) -> SkillResponse:
        telephony = self.registry.resolve_telephony("twilio") # Hardcoded for demo, normally from config

        summary = f"Customer ID: {context.customerId}. Language: {context.language}."
        
        # We fire and forget the transfer API call
        try:
            await telephony.transfer("QUEUE_SALES", summary)
        except Exception as e:
            print(f"Failed to initiate transfer: {e}")

        return SkillResponse(
            text="Please hold while I connect you to the next available representative.",
            nextSkill=None,
            sessionPatch={},
            endCall=True # Instructs the orchestrator to hang up the audio loop
        )
