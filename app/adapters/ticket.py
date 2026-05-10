from datetime import datetime
from typing import List
from app.core.interfaces import TicketAdapter
from app.core.schemas import Ticket, TicketInput
from app.core.events import emit_event

class ZendeskAdapter(TicketAdapter):
    async def createTicket(self, data: TicketInput) -> Ticket:
        print(f"[Zendesk] POST /api/v2/tickets.json")
        ticket = Ticket(
            id="ZD-10023", status="open", priority=data.priority,
            subject=data.subject, notes=[data.body or "Ticket created."],
            createdAt=datetime.utcnow()
        )
        await emit_event("ticket_created", {"ticketId": ticket.id, "subject": ticket.subject})
        return ticket

    async def getTicket(self, id: str) -> Ticket:
        print(f"[Zendesk] GET /api/v2/tickets/{id}.json")
        return Ticket(
            id=id, status="pending", priority="high",
            subject="Where is my delivery?", notes=["Customer called."],
            createdAt=datetime.utcnow()
        )

    async def updateTicket(self, id: str, status: str) -> Ticket:
        print(f"[Zendesk] PUT /api/v2/tickets/{id}.json")
        ticket = await self.getTicket(id)
        await emit_event("ticket_updated", {"ticketId": id, "status": status})
        return ticket

    async def listTickets(self, customerId: str) -> List[Ticket]:
        print(f"[Zendesk] GET /api/v2/users/{customerId}/tickets/requested.json")
        return [await self.getTicket("ZD-9999")]
