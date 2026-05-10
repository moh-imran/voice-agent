import json
from openai import AsyncOpenAI
from typing import List
from app.core.schemas import IntentResult, ConversationContext

class IntentClassifier:
    def __init__(self, api_key: str, model: str = 'gpt-4o'):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def classify(self, utterance: str, context: ConversationContext, available_intents: List[str]) -> IntentResult:
        prompt = f"""
You are an intent classification engine for "Congni", a professional voice agent.
Analyze the user's utterance and extract the following in JSON format:
- "intent": Best matching intent from this list: [{', '.join(available_intents)}, "thank_you", "goodbye", "unknown"]
- "confidence": A number between 0.0 and 1.0.
- "entities": A key-value object (e.g. orderId, phone, otp, sku).
- "language": ISO code (e.g. en-US).

CONTEXTUAL RULES:
1. If the current active skill is "auth" and the user says only numbers, treat them as "phone" or "otp".
2. If the user is polite (greeting, thanks, bye), map to those intents.

Current Session State:
- Active Skill: {context.activeSkill or "None"}
- Known Entities: {json.dumps(context.entities)}
- User Utterance: "{utterance}"
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
            
            parsed = json.loads(content)
            
            return IntentResult(
                intent=parsed.get("intent", "unknown"),
                confidence=float(parsed.get("confidence", 0.0)),
                entities=parsed.get("entities", {}),
                language=parsed.get("language", context.language),
                raw=utterance
            )
        except Exception as e:
            print(f"Failed to classify intent: {e}")
            return IntentResult(
                intent="unknown",
                confidence=0.0,
                entities={},
                language=context.language,
                raw=utterance
            )
