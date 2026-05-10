import requests
import uuid

def test_turn():
    call_id = str(uuid.uuid4())
    url = "http://127.0.0.1:3000/debug/turn"
    
    payload = {
        "callId": call_id,
        "utterance": "I want to track my order ORD-123"
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_turn()
