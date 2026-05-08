import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.engine.context import ContextManager

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
templates = Jinja2Templates(directory=templates_dir)

# Helper to access Redis directly for dashboard scans (simplified for scaffolding)
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
            
    # Sort by startedAt descending
    sessions.sort(key=lambda x: x.get('startedAt', ''), reverse=True)
    return sessions[:50] # return top 50 recent

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    sessions = get_recent_sessions()
    
    # Calculate simple stats
    total_calls = len(sessions)
    fallbacks = sum(s.get('failCount', 0) for s in sessions)
    
    return templates.TemplateResponse(
        "dashboard.jinja2", 
        {
            "request": request, 
            "sessions": sessions,
            "total_calls": total_calls,
            "fallbacks": fallbacks
        }
    )
