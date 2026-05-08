from typing import List
from app.core.interfaces import SkillPlugin
from app.core.schemas import ConversationContext, SkillResponse, IntentResult
from app.core.registry import PluginRegistry

class OrderTrackingSkill(SkillPlugin):
    name = "order_tracking"

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def getIntents(self) -> List[str]:
        return ["track_order", "where_is_my_order", "order_status"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents()

    async def execute(self, context: ConversationContext) -> SkillResponse:
        # Require authentication first
        if context.authState != "verified":
            return SkillResponse(
                text="I can help you track your order, but I need to look up your account first.",
                nextSkill="auth", # Yield to AuthSkill
                sessionPatch={}
            )

        order_id = context.entities.get("orderId")
        commerce = self.registry.resolve_commerce("magento") # Dynamic based on config in real scenario

        if not order_id:
            # If no specific order ID provided, just fetch a mock recent one
            order_id = "ORD-999"

        try:
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
