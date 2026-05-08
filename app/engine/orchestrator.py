from typing import Optional
from app.engine.context import ContextManager, Session
from app.engine.intent import IntentClassifier
from app.core.registry import PluginRegistry
from app.core.schemas import ConversationContext, SkillResponse, IntentResult
from app.core.logger import get_logger

logger = get_logger()

class ConversationLoop:
    def __init__(self, context_manager: ContextManager, intent_classifier: IntentClassifier, registry: PluginRegistry):
        self.context_manager = context_manager
        self.intent_classifier = intent_classifier
        self.registry = registry

    async def process_turn(self, call_id: str, utterance: str) -> SkillResponse:
        # 1. Get or create session
        session = self.context_manager.get_session(call_id)
        if not session:
            session = self.context_manager.create_session(call_id)

        # Prepare context object for skills
        context = ConversationContext(
            callId=session.callId,
            sessionId=session.callId,
            language=session.language,
            entities=session.entities,
            turnHistory=session.turnHistory,
            authState=session.authState,
            customerId=session.customerId
        )

        # 2. Classify intent
        all_skills = self.registry.get_all_skills()
        available_intents = []
        for s in all_skills:
            available_intents.extend(s.getIntents())

        intent_result = await self.intent_classifier.classify(utterance, context, available_intents)
        
        logger.info("Intent classified", extra={
            "callId": call_id,
            "intent": intent_result.intent,
            "confidence": intent_result.confidence
        })

        # Update session entities based on intent extraction
        entities_patch = {**session.entities, **intent_result.entities}
        session = self.context_manager.update_session(call_id, {
            "entities": entities_patch,
            "language": intent_result.language,
        })
        
        context.entities = session.entities
        context.language = session.language

        # 3. Fallback check
        if intent_result.confidence < 0.6:
            session = self.context_manager.update_session(call_id, {"failCount": session.failCount + 1})
            
            if session.failCount >= 3:
                return SkillResponse(
                    text="I'm having trouble understanding. Let me transfer you to a human agent.",
                    nextSkill='handoff',
                    sessionPatch={"failCount": 0},
                    endCall=False
                )

            return SkillResponse(
                text="I didn't quite catch that, could you please rephrase?",
                nextSkill=session.activeSkill,
                sessionPatch={},
                endCall=False
            )

        if session.failCount > 0:
            session = self.context_manager.update_session(call_id, {"failCount": 0})

        # 4. Skill Routing
        target_skill = None

        if session.activeSkill:
            try:
                target_skill = self.registry.resolve_skill(session.activeSkill)
            except ValueError:
                pass

        if not target_skill or not target_skill.canHandle(intent_result):
            for skill in all_skills:
                if skill.canHandle(intent_result):
                    target_skill = skill
                    break

        if not target_skill:
            if session.authState == 'anonymous':
                try:
                    target_skill = self.registry.resolve_skill('auth')
                except ValueError:
                    pass
            
            if not target_skill:
                try:
                    target_skill = self.registry.resolve_skill('faq')
                except ValueError:
                    return SkillResponse(
                        text="I'm not sure how to help with that right now. Can I help you with anything else?",
                        nextSkill=None,
                        sessionPatch={},
                        endCall=False
                    )

        # 5. Execute skill
        try:
            logger.info("Executing skill", extra={"callId": call_id, "skill": target_skill.name})
            response = await target_skill.execute(context)
            
            if response.sessionPatch or response.nextSkill is not None:
                patch = response.sessionPatch or {}
                patch["activeSkill"] = response.nextSkill
                session = self.context_manager.update_session(call_id, patch)

            # Save turns to history
            self.context_manager.add_turn(call_id, "user", utterance)
            self.context_manager.add_turn(call_id, "assistant", response.text)

            return response
        except Exception as e:
            logger.error("Skill Execution Error", extra={"callId": call_id, "error": str(e)})
            return SkillResponse(
                text="I'm sorry, I encountered an internal error while processing that. Let me transfer you.",
                nextSkill='handoff',
                sessionPatch={},
                endCall=False
            )
