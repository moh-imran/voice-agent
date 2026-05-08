from typing import List
from app.core.interfaces import SkillPlugin
from app.core.schemas import ConversationContext, SkillResponse, IntentResult
from app.core.registry import PluginRegistry

class AuthSkill(SkillPlugin):
    name = "auth"

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def getIntents(self) -> List[str]:
        return ["authenticate", "login"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents() or intent.intent == "unknown"

    async def execute(self, context: ConversationContext) -> SkillResponse:
        last_turn = context.turnHistory[-1]["content"] if context.turnHistory else ""

        # Step 1: Ask for phone number
        if "auth_phone" not in context.entities:
            # Extract phone from intent if available
            phone = context.entities.get("phone")
            if phone:
                return SkillResponse(
                    text=f"Thank you. I've sent an OTP to {phone}. Please read it back to me.",
                    nextSkill="auth",
                    sessionPatch={"entities": {"auth_phone": phone}}
                )
            
            # Simple regex/heuristic could go here in real life, but we rely on LLM entity extraction
            return SkillResponse(
                text="To assist you better, could you please provide your phone number?",
                nextSkill="auth",
                sessionPatch={}
            )

        # Step 2: Ask for OTP
        if "auth_otp" not in context.entities:
            # Assuming any 4 digit number they say is the OTP for this mock
            otp = context.entities.get("otp") or "".join(filter(str.isdigit, last_turn))
            
            if len(otp) >= 4:
                # OTP provided, verify and login
                phone = context.entities["auth_phone"]
                crm = self.registry.resolve_crm("salesforce") # or from config
                
                customer = await crm.searchCustomer(phone)
                
                if customer:
                    return SkillResponse(
                        text=f"Thank you, {customer.name}. How can I help you today?",
                        nextSkill=None, # release active skill lock
                        sessionPatch={"authState": "verified", "customerId": customer.id}
                    )
                else:
                    return SkillResponse(
                        text="I couldn't find an account matching that phone number, but I can still answer general questions.",
                        nextSkill=None,
                        sessionPatch={"authState": "anonymous"}
                    )

            return SkillResponse(
                text="Please tell me the 4 digit code we sent to your phone.",
                nextSkill="auth",
                sessionPatch={}
            )

        # Fallback
        return SkillResponse(text="Authentication complete.", nextSkill=None, sessionPatch={})
