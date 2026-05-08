from datetime import datetime
from typing import List
from app.core.interfaces import TicketAdapter
from app.core.schemas import Ticket, TicketInput

class ZendeskAdapter(TicketAdapter):
    async def createTicket(self, data: TicketInput) -> Ticket:
        print(f"[Zendesk] POST /api/v2/tickets.json")
        return Ticket(
            id="ZD-10023", status="open", priority=data.priority,
            subject=data.subject, notes=[data.body or "Ticket created."],
            createdAt=datetime.utcnow()
        )

    async def getTicket(self, id: str) -> Ticket:
        print(f"[Zendesk] GET /api/v2/tickets/{id}.json")
        return Ticket(
            id=id, status="pending", priority="high",
            subject="Where is my delivery?", notes=["Customer called."],
            createdAt=datetime.utcnow()
        )

    async def updateTicket(self, id: str, status: str) -> Ticket:
        print(f"[Zendesk] PUT /api/v2/tickets/{id}.json")
        return await self.getTicket(id)

    async def listTickets(self, customerId: str) -> List[Ticket]:
        print(f"[Zendesk] GET /api/v2/users/{customerId}/tickets/requested.json")
        return [await self.getTicket("ZD-9999")]
