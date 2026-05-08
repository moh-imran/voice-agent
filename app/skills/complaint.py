from typing import List
from app.core.interfaces import SkillPlugin
from app.core.schemas import ConversationContext, SkillResponse, IntentResult, TicketInput
from app.core.registry import PluginRegistry

class ComplaintSkill(SkillPlugin):
    name = "complaint"

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def getIntents(self) -> List[str]:
        return ["file_complaint", "issue", "broken_item"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents()

    async def execute(self, context: ConversationContext) -> SkillResponse:
        # Collect complaint description
        if "complaint_desc" not in context.entities:
            last_turn = context.turnHistory[-1]["content"] if context.turnHistory else ""
            
            # If we are already in the complaint flow, the last turn is their description
            if context.entities.get("in_complaint_flow"):
                desc = last_turn
                ticket_api = self.registry.resolve_ticket("zendesk")
                
                try:
                    ticket = await ticket_api.createTicket(TicketInput(
                        customerId=context.customerId or "anonymous",
                        subject="Voice Complaint",
                        body=desc
                    ))
                    
                    return SkillResponse(
                        text=f"I'm very sorry for the inconvenience. I have logged ticket number {ticket.id} for you. A specialist will follow up shortly.",
                        nextSkill=None,
                        sessionPatch={"entities": {"complaint_desc": desc}}
                    )
                except Exception:
                    return SkillResponse(
                        text="I failed to log the ticket. Let me transfer you to an agent.",
                        nextSkill="handoff",
                        sessionPatch={}
                    )

            return SkillResponse(
                text="I'm sorry to hear you're having an issue. Could you briefly describe the problem?",
                nextSkill="complaint",
                sessionPatch={"entities": {"in_complaint_flow": True}}
            )

        return SkillResponse(
            text="Is there anything else I can assist you with?",
            nextSkill=None,
            sessionPatch={}
        )
