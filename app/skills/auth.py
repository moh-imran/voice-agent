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
        # If it's a numeric input (OTP or Phone), AuthSkill should handle it
        has_digits = any(char.isdigit() for char in intent.raw)
        return intent.intent in self.getIntents() or intent.intent == "unknown" or has_digits

    async def execute(self, context: ConversationContext, intent: IntentResult) -> SkillResponse:
        utterance = intent.raw

        # Step 1: Ask for phone number
        if "auth_phone" not in context.entities:
            # Extract phone from intent if available
            phone = intent.entities.get("phone")
            
            # Heuristic fallback if LLM missed it: look for 10+ digits in the utterance
            if not phone:
                digits = "".join(filter(str.isdigit, utterance))
                if len(digits) >= 10:
                    phone = digits

            if phone:
                return SkillResponse(
                    text=f"Thank you. I've sent an OTP to {phone}. Please read it back to me.",
                    nextSkill="auth",
                    sessionPatch={"entities": {"auth_phone": phone}}
                )
            
            return SkillResponse(
                text="To assist you better, could you please provide your phone number?",
                nextSkill="auth",
                sessionPatch={}
            )

        # Step 2: Ask for OTP
        if "auth_otp" not in context.entities:
            # Assuming any 4 digit number they say is the OTP for this mock
            otp = intent.entities.get("otp") or "".join(filter(str.isdigit, utterance))
            
            if len(otp) >= 4:
                # OTP provided, verify and login
                phone = context.entities["auth_phone"]
                # Resolve whichever CRM is registered
                crms = self.registry.get_all_crms()
                crm = crms[0] if crms else None
                
                if not crm:
                    raise ValueError("No CRM adapter registered")
                
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
