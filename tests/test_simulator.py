import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import uuid
import fakeredis
from unittest.mock import patch

from app.main import app
from app.engine.context import ContextManager
from app.core.schemas import IntentResult

class CallSimulator:
    def __init__(self, client: AsyncClient):
        self.client = client
        self.call_id = str(uuid.uuid4())

    async def turn(self, utterance: str) -> dict:
        response = await self.client.post(
            "/debug/turn", 
            json={"callId": self.call_id, "utterance": utterance}
        )
        assert response.status_code == 200
        return response.json()

    async def get_session(self) -> dict:
        response = await self.client.get(f"/debug/session/{self.call_id}")
        assert response.status_code == 200
        return response.json()

@pytest_asyncio.fixture
async def simulator():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield CallSimulator(client)

@pytest.fixture(autouse=True)
def clean_redis():
    # Make sure we use a fake redis for tests
    manager = ContextManager.get_instance()
    manager.redis = fakeredis.FakeStrictRedis(decode_responses=True)
    yield
    manager.redis.flushall()

@pytest.mark.asyncio
@patch('app.engine.intent.IntentClassifier.classify')
async def test_order_tracking_flow(mock_classify, simulator: CallSimulator):
    # Mocking unauthenticated tracking intent
    mock_classify.return_value = IntentResult(
        intent="track_order", confidence=0.9, entities={}, language="en-US", raw="Where is my order?"
    )
    # 1. Ask about order (unauthenticated)
    res = await simulator.turn("Where is my order?")
    assert res["nextSkill"] == "auth"
    assert "account" in res["text"].lower()

    # 2. Provide phone number (now AuthSkill is active)
    mock_classify.return_value = IntentResult(
        intent="unknown", confidence=0.9, entities={"phone": "0500000000"}, language="en-US", raw="My phone is 0500000000"
    )
    res = await simulator.turn("My phone is 0500000000")
    assert res["nextSkill"] == "auth"
    assert "otp" in res["text"].lower()

    # 3. Provide OTP
    mock_classify.return_value = IntentResult(
        intent="unknown", confidence=0.9, entities={}, language="en-US", raw="1234"
    )
    res = await simulator.turn("1234")
    assert res["nextSkill"] is None
    
    session = await simulator.get_session()
    assert session["authState"] == "verified"
    
    # 4. Ask about order again (now authenticated)
    mock_classify.return_value = IntentResult(
        intent="track_order", confidence=0.9, entities={}, language="en-US", raw="Where is my order?"
    )
    res = await simulator.turn("Where is my order?")
    assert res["nextSkill"] is None
    assert "ORD-999" in res["text"] or "processing" in res["text"]

@pytest.mark.asyncio
@patch('app.engine.intent.IntentClassifier.classify')
async def test_handoff_flow(mock_classify, simulator: CallSimulator):
    mock_classify.return_value = IntentResult(
        intent="handoff", confidence=0.9, entities={}, language="en-US", raw="I want to speak to a human agent right now"
    )
    res = await simulator.turn("I want to speak to a human agent right now")
    assert res["endCall"] is True
    assert "hold" in res["text"].lower()

@pytest.mark.asyncio
@patch('app.engine.intent.IntentClassifier.classify')
async def test_fallback_escalation(mock_classify, simulator: CallSimulator):
    # Send garbage that the IntentClassifier shouldn't understand
    mock_classify.return_value = IntentResult(
        intent="unknown", confidence=0.0, entities={}, language="en-US", raw="garbage"
    )
    await simulator.turn("asdofiahsofihasfoi")
    await simulator.turn("zxcvzxcvzxcvzxcv")
    res = await simulator.turn("qwerqwerqwerqwer")
    
    # After 3 failures, it should force a handoff
    assert res["nextSkill"] == "handoff"
    assert "transfer" in res["text"].lower()
