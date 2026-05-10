from typing import List
from app.core.interfaces import SkillPlugin
from app.core.schemas import ConversationContext, SkillResponse, IntentResult, Cart
from app.core.registry import PluginRegistry

class OrderTrackingSkill(SkillPlugin):
    name = "order_tracking"

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def getIntents(self) -> List[str]:
        return ["track_order", "where_is_my_order", "order_status"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents()

    async def execute(self, context: ConversationContext, intent: IntentResult) -> SkillResponse:
        # Require authentication first
        if context.authState != "verified":
            return SkillResponse(
                text="I can help you track your order, but I need to look up your account first.",
                nextSkill="auth",
                sessionPatch={}
            )

        order_id = intent.entities.get("orderId") or context.entities.get("orderId") or "ORD-999"
        
        # Resolve active commerce adapter
        commerce_adapters = self.registry.get_all_commerce()
        commerce = commerce_adapters[0] if commerce_adapters else None
        
        if not commerce:
            raise ValueError("No commerce adapter registered")

        try:
            # We use the active commerce adapter from config
            active_commerce = intent.entities.get("commerce_provider", "shopify")
            commerce = self.registry.resolve_commerce(active_commerce)
            
            order = await commerce.getOrder(order_id)
            return SkillResponse(
                text=f"Your order {order.id} is currently {order.state}. It is expected to arrive on {order.eta}.",
                nextSkill=None,
                sessionPatch={}
            )
        except Exception as e:
            return SkillResponse(
                text="I'm having trouble retrieving your order details right now. Can I help you with anything else?",
                nextSkill=None,
                sessionPatch={}
            )

class PlaceOrderSkill(SkillPlugin):
    name = "place_order"

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def getIntents(self) -> List[str]:
        return ["place_order", "buy_item", "purchase"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents()

    async def execute(self, context: ConversationContext, intent: IntentResult) -> SkillResponse:
        # Require authentication first
        if context.authState != "verified":
            return SkillResponse(
                text="To place an order, I first need to verify your account. May I have your phone number?",
                nextSkill="auth",
                sessionPatch={}
            )

        # In a real scenario, we'd look for product entities
        product_name = intent.entities.get("product") or context.entities.get("product", "item")
        
        try:
            # Resolve active commerce adapter
            commerce_adapters = self.registry.get_all_commerce()
            commerce = commerce_adapters[0] if commerce_adapters else None
            
            if not commerce:
                raise ValueError("No commerce adapter registered")

            # Try to use the specific one if possible, otherwise use the first one
            try:
                active_commerce = self.registry.resolve_commerce("shopify")
            except:
                active_commerce = commerce

            order = await active_commerce.placeOrder(Cart(customerId=context.customerId or "guest", items=[]))
            
            return SkillResponse(
                text=f"Great! I've placed your order for the {product_name}. Your order number is {order.id}. You will receive a confirmation SMS shortly.",
                nextSkill=None,
                sessionPatch={}
            )
        except Exception as e:
            return SkillResponse(
                text="I'm sorry, I couldn't complete the purchase at this moment. Would you like to speak to an agent?",
                nextSkill="handoff",
                sessionPatch={}
            )

class OrderCancellationSkill(SkillPlugin):
    name = "order_cancellation"

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def getIntents(self) -> List[str]:
        return ["cancel_order", "stop_order", "delete_order"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents()

    async def execute(self, context: ConversationContext, intent: IntentResult) -> SkillResponse:
        if context.authState != "verified":
            return SkillResponse(
                text="To cancel an order, I need to verify your account first. May I have your phone number?",
                nextSkill="auth",
                sessionPatch={}
            )

        order_id = intent.entities.get("orderId") or context.entities.get("orderId")
        if not order_id:
            return SkillResponse(
                text="Which order would you like to cancel? Please provide the order number.",
                nextSkill="order_cancellation",
                sessionPatch={}
            )

        try:
            commerce_adapters = self.registry.get_all_commerce()
            commerce = commerce_adapters[0] if commerce_adapters else None
            await commerce.cancelOrder(order_id)
            
            return SkillResponse(
                text=f"I have successfully cancelled order {order_id}. You will receive a cancellation email shortly.",
                nextSkill=None,
                sessionPatch={}
            )
        except Exception:
            return SkillResponse(
                text="I'm having trouble cancelling that order. Let me connect you with a representative who can help.",
                nextSkill="handoff",
                sessionPatch={}
            )
