from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class Customer(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    tier: Optional[str] = "Standard"

class OrderItem(BaseModel):
    sku: str
    qty: int

class Order(BaseModel):
    id: str
    state: str
    amount: float
    currency: str = "USD"
    items: List[OrderItem] = Field(default_factory=list)
    eta: Optional[str] = None
    trackingUrl: Optional[str] = None
    createdAt: datetime

class Product(BaseModel):
    sku: str
    name: str
    price: float
    currency: str = "USD"
    inStock: bool

class Cart(BaseModel):
    customerId: str
    items: List[OrderItem] = Field(default_factory=list)

class CaseInput(BaseModel):
    customerId: str
    subject: str
    description: str

class TicketInput(BaseModel):
    customerId: str
    subject: str
    body: Optional[str] = None
    priority: Optional[str] = "normal"

class Ticket(BaseModel):
    id: str
    status: str
    priority: str
    subject: str
    notes: List[str] = Field(default_factory=list)
    createdAt: datetime

# Audio & State interfaces (Types)
class AudioChunk(BaseModel):
    data: bytes

class CallMetadata(BaseModel):
    ani: str
    dnis: str
    language: str

class IntentResult(BaseModel):
    intent: str
    confidence: float
    entities: Dict[str, Any] = Field(default_factory=dict)
    language: str
    raw: str

class SkillResponse(BaseModel):
    text: str
    nextSkill: Optional[str] = None
    sessionPatch: Optional[Dict[str, Any]] = None
    endCall: bool = False

class ConversationContext(BaseModel):
    callId: str
    sessionId: str
    language: str
    entities: Dict[str, Any]
    turnHistory: List[Dict[str, str]]
    authState: str
    customerId: Optional[str] = None
    activeSkill: Optional[str] = None
