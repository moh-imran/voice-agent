from datetime import datetime
from typing import List, Any
from app.core.interfaces import CommerceAdapter
from app.core.schemas import Order, Product, Cart, OrderItem
from app.core.events import emit_event

class MagentoAdapter(CommerceAdapter):
    async def getOrder(self, id: str) -> Order:
        print(f"[Magento] GET /V1/orders/{id}")
        return Order(
            id=id, state="processing", amount=1200.50, currency="SAR",
            items=[OrderItem(sku="LAPTOP-123", qty=1)],
            eta="2026-05-10", trackingUrl="https://aramex.com/track/123",
            createdAt=datetime.utcnow()
        )

    async def getPricing(self, sku: str) -> Product:
        print(f"[Magento] GET /V1/products/{sku}")
        return Product(sku=sku, name="MacBook Pro M3", price=1200.50, currency="SAR", inStock=True)

    async def placeOrder(self, cart: Cart) -> Order:
        print(f"[Magento] POST /V1/carts/mine/order")
        return await self.getOrder("ORD-999")

    async def cancelOrder(self, id: str) -> None:
        print(f"[Magento] POST /V1/orders/{id}/cancel")

    async def getReturns(self, customerId: str) -> List[Any]:
        print(f"[Magento] GET /V1/returns?customerId={customerId}")
        return []

class ShopifyAdapter(CommerceAdapter):
    async def getOrder(self, id: str) -> Order:
        print(f"[Shopify] GET /admin/api/2024-04/orders/{id}.json")
        return Order(
            id=id, state="shipped", amount=450.00, currency="USD",
            items=[OrderItem(sku="SHOES-42", qty=2)],
            eta="2026-05-12", trackingUrl="https://fedex.com/track/456",
            createdAt=datetime.utcnow()
        )

    async def getPricing(self, sku: str) -> Product:
        print(f"[Shopify] GraphQL query variants for SKU {sku}")
        return Product(sku=sku, name="Nike Air Max", price=225.00, currency="USD", inStock=True)

    async def placeOrder(self, cart: Cart) -> Order:
        print(f"[Shopify] POST /admin/api/orders.json")
        order = await self.getOrder("SHP-777")
        await emit_event("order_placed", {
            "orderId": order.id,
            "amount": order.amount,
            "customer": cart.customerId
        })
        return order

    async def cancelOrder(self, id: str) -> None:
        print(f"[Shopify] POST /admin/api/orders/{id}/cancel.json")
        await emit_event("order_cancelled", {"orderId": id})

    async def getReturns(self, customerId: str) -> List[Any]:
        return []
