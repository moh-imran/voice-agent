import os
from openai import AsyncOpenAI
from typing import List
from app.core.interfaces import SkillPlugin
from app.core.schemas import ConversationContext, SkillResponse, IntentResult

class FAQSkill(SkillPlugin):
    name = "faq"

    def __init__(self, api_key: str = None):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY", "mock"))
        
        # Mock Knowledge Base Context
        self.kb_context = """
        Agent Identity: Your name is Congni. You are a professional AI voice assistant for this store.
        Store Hours: Monday to Friday 9 AM to 8 PM. Weekends 10 AM to 5 PM.
        Return Policy: Items can be returned within 30 days of receipt if unopened.
        Shipping: Standard shipping takes 3-5 business days. Express takes 1-2 days.
        Location: 123 Main Street, Riyadh, Saudi Arabia.
        """

    def getIntents(self) -> List[str]:
        return ["ask_question", "faq", "store_hours", "return_policy"]

    def canHandle(self, intent: IntentResult) -> bool:
        return intent.intent in self.getIntents()

    async def execute(self, context: ConversationContext, intent: IntentResult) -> SkillResponse:
        question = intent.raw

        prompt = f"""
You are answering a customer's question based ONLY on the knowledge base below.
If the answer is not in the knowledge base, say you don't know and ask if they want to speak to an agent.
Keep the answer under 2 sentences.

Knowledge Base:
{self.kb_context}

Question: "{question}"
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.1
            )
            answer = response.choices[0].message.content
            return SkillResponse(text=answer, nextSkill=None, sessionPatch={})
        except Exception as e:
            print(f"FAQ RAG Error: {e}")
            return SkillResponse(
                text="I'm having trouble looking that up right now.",
                nextSkill=None,
                sessionPatch={}
            )
