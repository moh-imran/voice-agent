from typing import Optional
from app.core.interfaces import CRMAdapter
from app.core.schemas import Customer, CaseInput

class SalesforceAdapter(CRMAdapter):
    async def getCustomer(self, id: str) -> Customer:
        print(f"[Salesforce] SOQL: SELECT Id FROM Contact WHERE Id = '{id}'")
        return Customer(id=id, name="Ahmed Al-Farsi", phone="+966500000000", email="ahmed@example.com", tier="Gold")

    async def searchCustomer(self, phone: str) -> Optional[Customer]:
        print(f"[Salesforce] SOQL: SELECT Id FROM Contact WHERE Phone = '{phone}'")
        if phone == "0000": return None
        return Customer(id="SF-CONT-123", name="Sara Ahmed", phone=phone, tier="Silver")

    async def createCase(self, data: CaseInput) -> dict:
        print(f"[Salesforce] POST /services/data/v60.0/sobjects/Case/")
        return {"id": "SF-CASE-456", **data.model_dump()}

    async def updateCase(self, id: str, data: dict) -> dict:
        print(f"[Salesforce] PATCH /services/data/v60.0/sobjects/Case/{id}")
        return {"id": id, **data}

class HubSpotAdapter(CRMAdapter):
    async def getCustomer(self, id: str) -> Customer:
        print(f"[HubSpot] GET /crm/v3/objects/contacts/{id}")
        return Customer(id=id, name="John Doe", phone="+15551234567")

    async def searchCustomer(self, phone: str) -> Optional[Customer]:
        print(f"[HubSpot] POST /crm/v3/objects/contacts/search")
        if phone == "0000": return None
        return Customer(id="HS-CONT-999", name="Jane Smith", phone=phone)

    async def createCase(self, data: CaseInput) -> dict:
        print(f"[HubSpot] POST /crm/v3/objects/tickets")
        return {"id": "HS-TKT-111", **data.model_dump()}

    async def updateCase(self, id: str, data: dict) -> dict:
        print(f"[HubSpot] PATCH /crm/v3/objects/tickets/{id}")
        return {"id": id, **data}
