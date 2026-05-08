from abc import ABC, abstractmethod
from typing import AsyncIterable, Optional, List, Callable, Any
from app.core.schemas import (
    AudioChunk, CallMetadata, Customer, Order, Product, 
    Cart, CaseInput, TicketInput, Ticket, IntentResult, 
    ConversationContext, SkillResponse
)

class TelephonyAdapter(ABC):
    @abstractmethod
    async def initCall(self, callId: str, metadata: CallMetadata) -> None:
        pass
    
    @abstractmethod
    async def streamAudio(self) -> AsyncIterable[AudioChunk]:
        pass
    
    @abstractmethod
    async def sendAudio(self, audio: bytes) -> None:
        pass
    
    @abstractmethod
    async def transfer(self, agentId: str, contextSummary: str) -> None:
        pass
    
    @abstractmethod
    async def hangup(self, callId: str) -> None:
        pass
    
    @abstractmethod
    def onDTMF(self, handler: Callable[[str], None]) -> None:
        pass


class SpeechAdapter(ABC):
    @abstractmethod
    async def transcribe(self, audioStream: AsyncIterable[AudioChunk], lang: Optional[str] = None) -> dict:
        """Returns dict with text, language, confidence"""
        pass
        
    @abstractmethod
    async def detectLanguage(self, audioStream: AsyncIterable[AudioChunk]) -> dict:
        """Returns dict with language, confidence"""
        pass
        
    @abstractmethod
    async def synthesize(self, text: str, voiceId: str) -> bytes:
        pass


class CRMAdapter(ABC):
    @abstractmethod
    async def getCustomer(self, id: str) -> Customer:
        pass
        
    @abstractmethod
    async def searchCustomer(self, phone: str) -> Optional[Customer]:
        pass
        
    @abstractmethod
    async def createCase(self, data: CaseInput) -> dict:
        pass
        
    @abstractmethod
    async def updateCase(self, id: str, data: dict) -> dict:
        pass


class CommerceAdapter(ABC):
    @abstractmethod
    async def getOrder(self, id: str) -> Order:
        pass
        
    @abstractmethod
    async def getPricing(self, sku: str) -> Product:
        pass
        
    @abstractmethod
    async def placeOrder(self, cart: Cart) -> Order:
        pass
        
    @abstractmethod
    async def cancelOrder(self, id: str) -> None:
        pass
        
    @abstractmethod
    async def getReturns(self, customerId: str) -> List[Any]:
        pass


class TicketAdapter(ABC):
    @abstractmethod
    async def createTicket(self, data: TicketInput) -> Ticket:
        pass
        
    @abstractmethod
    async def getTicket(self, id: str) -> Ticket:
        pass
        
    @abstractmethod
    async def updateTicket(self, id: str, status: str) -> Ticket:
        pass
        
    @abstractmethod
    async def listTickets(self, customerId: str) -> List[Ticket]:
        pass


class SkillPlugin(ABC):
    name: str

    @abstractmethod
    def getIntents(self) -> List[str]:
        pass

    @abstractmethod
    def canHandle(self, intent: IntentResult) -> bool:
        pass

    @abstractmethod
    async def execute(self, context: ConversationContext) -> SkillResponse:
        pass
