import os
import json
from fastapi import APIRouter, Request, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.engine.context import ContextManager
from app.core.events import event_manager
from app.core.registry import PluginRegistry

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
templates = Jinja2Templates(directory=templates_dir)

class LoginRequest(BaseModel):
    username: str
    password: str

# In a real app, use password hashing. For POC, we'll check against users.json
def verify_user(username, password):
    users_file = os.path.join(os.path.dirname(__file__), 'users.json')
    if not os.path.exists(users_file):
        return username == "admin" and password == "admin" # Default fallback
    
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
            # For POC simplicity, we'll allow plain text 'admin' or the hashed one
            if username == "admin" and password == "admin": return True
            return users.get(username) == password
    except:
        return False

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.jinja2", {"request": request})

@router.post("/login")
async def login(req: LoginRequest, response: Response):
    if verify_user(req.username, req.password):
        # Set a simple session cookie for the POC
        response.set_cookie(key="admin_session", value="authenticated_session_token", httponly=True)
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie("admin_session")
    return RedirectResponse(url="/admin/login")

def get_recent_sessions():
    context_manager = ContextManager.get_instance()
    redis_client = context_manager.redis
    keys = redis_client.keys("session:*")
    
    sessions = []
    for key in keys:
        call_id = key.split(":")[1]
        session = context_manager.get_session(call_id)
        if session:
            sessions.append(session.to_dict())
            
    sessions.sort(key=lambda x: x.get('startedAt', ''), reverse=True)
    return sessions[:50]

@router.get("/tts")
async def get_tts(text: str):
    speech_adapter = PluginRegistry.get_instance().resolve_speech('whisper')
    audio_data = await speech_adapter.synthesize(text)
    return Response(content=audio_data, media_type="audio/mpeg")

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    # Check session cookie
    if request.cookies.get("admin_session") != "authenticated_session_token":
        return RedirectResponse(url="/admin/login")

    sessions = get_recent_sessions()
    total_calls = len(sessions)
    fallbacks = sum(s.get('failCount', 0) for s in sessions)
    events = event_manager.get_history()
    
    return templates.TemplateResponse(
        "dashboard.jinja2", 
        {
            "request": request, 
            "sessions": sessions,
            "total_calls": total_calls,
            "fallbacks": fallbacks,
            "events": events
        }
    )
