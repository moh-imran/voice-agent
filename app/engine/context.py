import json
import redis
from datetime import datetime
from typing import Optional, Dict, Any, List

class Session:
    def __init__(self, callId: str, **kwargs):
        self.callId = callId
        self.callerId = kwargs.get('callerId', 'unknown')
        self.language = kwargs.get('language', 'en-US')
        self.dialect = kwargs.get('dialect')
        self.authState = kwargs.get('authState', 'anonymous')
        self.customerId = kwargs.get('customerId')
        self.activeSkill = kwargs.get('activeSkill')
        self.turnHistory = kwargs.get('turnHistory', [])
        self.entities = kwargs.get('entities', {})
        self.failCount = kwargs.get('failCount', 0)
        started_at = kwargs.get('startedAt')
        self.startedAt = started_at if isinstance(started_at, str) else datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__

class ContextManager:
    _instance = None
    TTL_SECONDS = 30 * 60

    def __new__(cls, redis_url: str = None):
        if cls._instance is None:
            if not redis_url:
                raise ValueError("Must provide redis_url for initialization")
            cls._instance = super(ContextManager, cls).__new__(cls)
            cls._instance.redis = redis.from_url(redis_url, decode_responses=True)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ContextManager":
        if cls._instance is None:
            raise RuntimeError("ContextManager not initialized")
        return cls._instance

    def _get_key(self, callId: str) -> str:
        return f"session:{callId}"

    def get_session(self, callId: str) -> Optional[Session]:
        data = self.redis.get(self._get_key(callId))
        if not data:
            return None
        return Session(**json.loads(data))

    def create_session(self, callId: str, initial_data: dict = None) -> Session:
        initial_data = initial_data or {}
        session = Session(callId, **initial_data)
        self.redis.setex(self._get_key(callId), self.TTL_SECONDS, json.dumps(session.to_dict()))
        return session

    def update_session(self, callId: str, patch: dict) -> Session:
        existing = self.get_session(callId)
        if existing:
            data = existing.to_dict()
            data.update(patch)
            session = Session(**data)
        else:
            session = self.create_session(callId, patch)
        
        self.redis.setex(self._get_key(callId), self.TTL_SECONDS, json.dumps(session.to_dict()))
        return session

    def add_turn(self, callId: str, role: str, content: str) -> Session:
        session = self.get_session(callId)
        if not session:
            raise ValueError(f"Session {callId} not found")
        
        session.turnHistory.append({"role": role, "content": content})
        if len(session.turnHistory) > 20:
            session.turnHistory = session.turnHistory[-20:]
            
        return self.update_session(callId, {"turnHistory": session.turnHistory})
