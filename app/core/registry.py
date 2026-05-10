from typing import Dict, Optional
from app.core.interfaces import (
    TelephonyAdapter, SpeechAdapter, CRMAdapter, CommerceAdapter, TicketAdapter, SkillPlugin
)

class PluginRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginRegistry, cls).__new__(cls)
            cls._instance._telephony_adapters = {}
            cls._instance._speech_adapters = {}
            cls._instance._crm_adapters = {}
            cls._instance._commerce_adapters = {}
            cls._instance._ticket_adapters = {}
            cls._instance._skills = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> "PluginRegistry":
        if cls._instance is None:
            cls()
        return cls._instance

    def register_telephony(self, name: str, adapter: TelephonyAdapter):
        self._telephony_adapters[name] = adapter

    def register_speech(self, name: str, adapter: SpeechAdapter):
        self._speech_adapters[name] = adapter

    def register_crm(self, name: str, adapter: CRMAdapter):
        self._crm_adapters[name] = adapter

    def register_commerce(self, name: str, adapter: CommerceAdapter):
        self._commerce_adapters[name] = adapter

    def register_ticket(self, name: str, adapter: TicketAdapter):
        self._ticket_adapters[name] = adapter

    def register_skill(self, skill: SkillPlugin):
        self._skills[skill.name] = skill

    def resolve_telephony(self, name: str) -> TelephonyAdapter:
        if name not in self._telephony_adapters:
            raise ValueError(f"Telephony adapter {name} not found")
        return self._telephony_adapters[name]

    def resolve_speech(self, name: str) -> SpeechAdapter:
        if name not in self._speech_adapters:
            raise ValueError(f"Speech adapter {name} not found")
        return self._speech_adapters[name]

    def resolve_crm(self, name: str) -> CRMAdapter:
        if name not in self._crm_adapters:
            raise ValueError(f"CRM adapter {name} not found")
        return self._crm_adapters[name]

    def resolve_commerce(self, name: str) -> CommerceAdapter:
        if name not in self._commerce_adapters:
            raise ValueError(f"Commerce adapter {name} not found")
        return self._commerce_adapters[name]

    def resolve_ticket(self, name: str) -> TicketAdapter:
        if name not in self._ticket_adapters:
            raise ValueError(f"Ticket adapter {name} not found")
        return self._ticket_adapters[name]

    def resolve_skill(self, name: str) -> SkillPlugin:
        if name not in self._skills:
            raise ValueError(f"Skill {name} not found")
        return self._skills[name]

    def get_all_skills(self) -> list[SkillPlugin]:
        return list(self._skills.values())

    def get_all_crms(self) -> list[CRMAdapter]:
        return list(self._crm_adapters.values())

    def get_all_commerce(self) -> list[CommerceAdapter]:
        return list(self._commerce_adapters.values())

    def get_all_telephony(self) -> list[TelephonyAdapter]:
        return list(self._telephony_adapters.values())
