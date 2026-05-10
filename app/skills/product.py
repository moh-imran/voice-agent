from typing import List
from app.core.interfaces import SkillPlugin
from app.core.schemas import ConversationContext, SkillResponse, IntentResult
from app.core.registry import PluginRegistry

class ProductSkill(SkillPlugin):
    name = "product_info"

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def getIntents(self) -> List[str]:
        return ["get_pricing", "check_stock", "product_details"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents()

    async def execute(self, context: ConversationContext, intent: IntentResult) -> SkillResponse:
        product_name = intent.entities.get("product") or intent.entities.get("sku")
        
        if not product_name:
            return SkillResponse(
                text="Which product are you interested in?",
                nextSkill="product_info",
                sessionPatch={}
            )

        try:
            commerce_adapters = self.registry.get_all_commerce()
            commerce = commerce_adapters[0] if commerce_adapters else None
            
            product = await commerce.getPricing(product_name)
            
            stock_status = "in stock" if product.inStock else "currently out of stock"
            
            return SkillResponse(
                text=f"The {product.name} is priced at {product.price} {product.currency} and is {stock_status}. Would you like to add it to your cart?",
                nextSkill=None,
                sessionPatch={"entities": {"product": product.name, "sku": product.sku}}
            )
        except Exception:
            return SkillResponse(
                text=f"I'm sorry, I couldn't find details for '{product_name}'. Can I check another product for you?",
                nextSkill=None,
                sessionPatch={}
            )
