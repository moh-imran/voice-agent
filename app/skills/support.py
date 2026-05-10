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

    async def execute(self, context: ConversationContext, intent: IntentResult) -> SkillResponse:
        # Collect complaint description
        if "complaint_desc" not in context.entities:
            # If we are already in the complaint flow, the current utterance is their description
            if context.entities.get("in_complaint_flow"):
                desc = intent.raw
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

class TicketStatusSkill(SkillPlugin):
    name = "ticket_status"

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def getIntents(self) -> List[str]:
        return ["check_ticket", "ticket_status", "my_tickets"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents()

    async def execute(self, context: ConversationContext, intent: IntentResult) -> SkillResponse:
        if context.authState != "verified":
            return SkillResponse(
                text="To check your ticket status, I need to verify your account first. May I have your phone number?",
                nextSkill="auth",
                sessionPatch={}
            )

        ticket_id = intent.entities.get("ticketId")
        ticket_api = self.registry.resolve_ticket("zendesk")

        try:
            if ticket_id:
                ticket = await ticket_api.getTicket(ticket_id)
                return SkillResponse(
                    text=f"Your ticket {ticket.id} regarding '{ticket.subject}' is currently {ticket.status}.",
                    nextSkill=None,
                    sessionPatch={}
                )
            else:
                tickets = await ticket_api.listTickets(context.customerId)
                if not tickets:
                    return SkillResponse(text="I couldn't find any active tickets for your account.", nextSkill=None, sessionPatch={})
                
                latest = tickets[0]
                return SkillResponse(
                    text=f"Your latest ticket {latest.id} is {latest.status}. Would you like details on another ticket?",
                    nextSkill=None,
                    sessionPatch={}
                )
        except Exception:
            return SkillResponse(
                text="I'm having trouble retrieving your ticket information. Can I help you with anything else?",
                nextSkill=None,
                sessionPatch={}
            )
