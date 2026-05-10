from typing import List
from app.core.interfaces import SkillPlugin
from app.core.schemas import ConversationContext, SkillResponse, IntentResult
from app.core.registry import PluginRegistry

class SmallTalkSkill(SkillPlugin):
    name = "small_talk"

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def getIntents(self) -> List[str]:
        return ["thank_you", "goodbye", "greeting"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents()

    async def execute(self, context: ConversationContext, intent: IntentResult) -> SkillResponse:
        if intent.intent == "thank_you":
            return SkillResponse(
                text="You're very welcome! Is there anything else I can help you with today?",
                nextSkill=None,
                sessionPatch={}
            )
        if intent.intent == "goodbye":
            return SkillResponse(
                text="Goodbye! Thank you for calling. Have a wonderful day!",
                nextSkill=None,
                sessionPatch={},
                endCall=True
            )
        
        return SkillResponse(
            text="Hello! I am Congni, your AI assistant. How can I help you today?",
            nextSkill=None,
            sessionPatch={}
        )
