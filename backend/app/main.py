"""
Akai - AI Screen Assistant
Full LLM capabilities with real-time screen vision
"""

import os
import uuid
import base64
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import services
from app.services.claude_service import ClaudeService
from app.services.speech_service import SpeechService
from app.services.session_manager import SessionManager
from app.services.knowledge_base import KnowledgeBase
from app.services.task_planner import TaskPlanner

# Initialize services
claude_service = ClaudeService()
speech_service = SpeechService()
session_manager = SessionManager()
knowledge_base = KnowledgeBase()
task_planner = TaskPlanner()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    print("🚀 Akai starting up...")
    print(f"📍 Server running at http://localhost:{os.getenv('PORT', 8000)}")
    print("🧠 AI ready")
    print("👁️ Screen vision enabled")
    yield
    print("👋 Akai shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Akai",
    description="AI Screen Assistant - Your friendly AI buddy that can see your screen",
    version="0.3.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React build static files
REACT_BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend-react", "build")
app.mount("/static", StaticFiles(directory=os.path.join(REACT_BUILD_DIR, "static")), name="static")


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.get("/")
async def home():
    """Serve the React frontend"""
    return FileResponse(os.path.join(REACT_BUILD_DIR, "index.html"))


@app.post("/api/session/create")
async def create_session():
    """Create a new support session"""
    session = session_manager.create_session()
    return {
        "session_id": session["id"],
        "code": session["code"],
        "created_at": session["created_at"],
        "message": "Session created successfully"
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/api/session/join")
async def join_session(code: str = Form(...)):
    """Join a session using short code"""
    session = session_manager.get_session_by_code(code)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid session code")
    return {
        "session_id": session["id"],
        "message": "Joined session successfully"
    }


@app.post("/api/voice/transcribe")
async def transcribe_audio(audio: UploadFile = File(...), session_id: str = Form(...)):
    """Transcribe audio using Whisper API"""
    try:
        # Read audio data
        audio_data = await audio.read()

        # Transcribe using Whisper
        transcript = await speech_service.transcribe(audio_data, audio.filename)

        # Add to session history
        session_manager.add_message(session_id, "user", transcript)

        return {
            "transcript": transcript,
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/synthesize")
async def synthesize_speech(text: str = Form(...)):
    """Convert text to speech using TTS"""
    try:
        audio_base64 = await speech_service.synthesize(text)
        return {
            "audio": audio_base64,
            "format": "mp3"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/screen/analyze")
async def analyze_screen(
    screenshot: UploadFile = File(...),
    session_id: str = Form(...),
    user_message: Optional[str] = Form(None)
):
    """Analyze screenshot using Claude Vision"""
    try:
        # Read image data
        image_data = await screenshot.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Get session context
        session = session_manager.get_session(session_id)
        conversation_history = session.get("messages", []) if session else []

        # Analyze with Claude Vision
        analysis = await claude_service.analyze_screen(
            image_base64=image_base64,
            user_message=user_message,
            conversation_history=conversation_history
        )

        # Add AI response to session
        session_manager.add_message(session_id, "assistant", analysis["response"])

        return {
            "response": analysis["response"],
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    session_id: str = Form(...),
    screenshot: Optional[UploadFile] = File(None)
):
    """Chat with AI assistant, optionally with screenshot"""
    try:
        # Get session context
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        conversation_history = session.get("messages", [])

        # Add user message to history
        session_manager.add_message(session_id, "user", message)

        # Process with or without screenshot
        if screenshot and screenshot.filename:
            image_data = await screenshot.read()
            print(f"📸 Screenshot received: {len(image_data)} bytes, filename: {screenshot.filename}")
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            response = await claude_service.analyze_screen(
                image_base64=image_base64,
                user_message=message,
                conversation_history=conversation_history
            )
        else:
            print(f"💬 Text-only chat (no screenshot)")
            response = await claude_service.chat(
                message=message,
                conversation_history=conversation_history
            )

        # Add AI response to session
        session_manager.add_message(session_id, "assistant", response["response"])

        return {
            "response": response["response"],
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Knowledge Base Endpoints
# ============================================================================

@app.get("/api/knowledge/categories")
async def get_kb_categories():
    """Get all Knowledge Base categories"""
    categories = knowledge_base.get_categories()
    return {"categories": categories}


@app.get("/api/knowledge/search")
async def search_kb(query: str, category: Optional[str] = None):
    """Search the Knowledge Base for problems and solutions"""
    results = knowledge_base.search(query, category)
    return {
        "query": query,
        "category": category,
        "count": len(results),
        "results": results
    }


@app.get("/api/knowledge/problems/{problem_id}")
async def get_kb_problem(problem_id: str):
    """Get a specific problem from the Knowledge Base"""
    problem = knowledge_base.get_problem(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@app.get("/api/knowledge/solutions/{solution_id}")
async def get_kb_solution(solution_id: str):
    """Get a specific solution from the Knowledge Base"""
    solution = knowledge_base.get_solution(solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")
    return solution


@app.post("/api/knowledge/solutions/{solution_id}/feedback")
async def record_solution_feedback(solution_id: str, success: bool = Form(...)):
    """Record feedback on whether a solution worked"""
    recorded = knowledge_base.record_feedback(solution_id, success)
    if not recorded:
        raise HTTPException(status_code=404, detail="Solution not found")
    return {
        "solution_id": solution_id,
        "success": success,
        "message": "Feedback recorded"
    }


@app.get("/api/knowledge/quick-solutions")
async def get_quick_solutions(min_success_rate: float = 0.7, min_uses: int = 3):
    """Get solutions with high success rates"""
    solutions = knowledge_base.get_quick_solutions(min_success_rate, min_uses)
    return {
        "count": len(solutions),
        "solutions": solutions
    }


# ============================================================================
# Task Planner Endpoints
# ============================================================================

@app.get("/api/tasks/templates")
async def get_task_templates(category: Optional[str] = None):
    """Get available task templates"""
    templates = task_planner.get_templates(category)
    return {
        "count": len(templates),
        "templates": templates
    }


@app.post("/api/tasks/create")
async def create_task_plan(
    session_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    steps: str = Form(...)  # JSON string of steps array
):
    """Create a new task plan"""
    import json
    try:
        steps_list = json.loads(steps)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid steps JSON")

    plan = task_planner.create_plan(
        session_id=session_id,
        title=title,
        description=description,
        steps=steps_list
    )
    return plan.to_dict()


@app.post("/api/tasks/create-from-message")
async def create_task_from_message(
    session_id: str = Form(...),
    message: str = Form(...)
):
    """Auto-detect template from message and create a task plan"""
    result = task_planner.create_from_message(session_id, message)
    if not result:
        return {
            "matched": False,
            "message": "No matching template found"
        }
    return {
        "matched": True,
        "template": result["template"],
        "plan": result["plan"]
    }


@app.get("/api/tasks/session/{session_id}")
async def get_session_tasks(session_id: str):
    """Get all task plans for a session"""
    plans = task_planner.get_plans_for_session(session_id)
    return {
        "session_id": session_id,
        "count": len(plans),
        "plans": plans
    }


@app.get("/api/tasks/session/{session_id}/active")
async def get_active_task(session_id: str):
    """Get the active task plan for a session"""
    plan = task_planner.get_active_plan(session_id)
    return {
        "session_id": session_id,
        "has_active_plan": plan is not None,
        "plan": plan
    }


@app.get("/api/tasks/{plan_id}")
async def get_task_plan(plan_id: str):
    """Get a specific task plan"""
    plan = task_planner.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Task plan not found")
    return plan


@app.post("/api/tasks/{plan_id}/start")
async def start_task_plan(plan_id: str):
    """Start executing a task plan"""
    result = task_planner.start_plan(plan_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot start plan (not found or already started)")
    return result


@app.post("/api/tasks/{plan_id}/steps/{step_id}/complete")
async def complete_task_step(plan_id: str, step_id: str):
    """Mark a task step as completed"""
    result = task_planner.complete_step(plan_id, step_id)
    if not result:
        raise HTTPException(status_code=404, detail="Plan or step not found")
    return result


@app.post("/api/tasks/{plan_id}/steps/{step_id}/fail")
async def fail_task_step(plan_id: str, step_id: str, error_message: str = Form(...)):
    """Mark a task step as failed"""
    result = task_planner.fail_step(plan_id, step_id, error_message)
    if not result:
        raise HTTPException(status_code=404, detail="Plan or step not found")
    return result


@app.post("/api/tasks/{plan_id}/steps/{step_id}/skip")
async def skip_task_step(plan_id: str, step_id: str):
    """Skip a task step"""
    result = task_planner.skip_step(plan_id, step_id)
    if not result:
        raise HTTPException(status_code=404, detail="Plan or step not found")
    return result


# ============================================================================
# WebSocket for Real-time Communication
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"✅ Client connected: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"❌ Client disconnected: {session_id}")

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, session_id)

    try:
        while True:
            data = await websocket.receive_json()

            # Handle different message types
            msg_type = data.get("type")

            if msg_type == "screen_share":
                # Received screen frame
                frame_data = data.get("frame")
                user_message = data.get("message")

                if frame_data and user_message:
                    # Get context
                    kb_context = knowledge_base.get_context_for_query(user_message)
                    task_context = task_planner.get_context_for_session(session_id)

                    # Send KB match event if solutions found
                    if kb_context.get("has_matches"):
                        await manager.send_message(session_id, {
                            "type": "kb_match",
                            "problems": kb_context.get("problems", []),
                            "top_solutions": kb_context.get("top_solutions", [])
                        })

                    # Analyze screen with Claude and context
                    response = await claude_service.analyze_screen_with_context(
                        image_base64=frame_data,
                        user_message=user_message,
                        conversation_history=session_manager.get_session(session_id).get("messages", []),
                        kb_context=kb_context,
                        task_context=task_context
                    )

                    session_manager.add_message(session_id, "assistant", response["response"])

                    await manager.send_message(session_id, {
                        "type": "ai_response",
                        "response": response["response"],
                        "had_kb_context": response.get("had_kb_context", False),
                        "had_task_context": response.get("had_task_context", False)
                    })

            elif msg_type == "voice":
                # Received voice data (base64 encoded)
                audio_data = base64.b64decode(data.get("audio", ""))

                # Transcribe
                transcript = await speech_service.transcribe(audio_data)

                session_manager.add_message(session_id, "user", transcript)

                await manager.send_message(session_id, {
                    "type": "transcript",
                    "text": transcript
                })

            elif msg_type == "chat":
                # Text chat message with KB and task context
                message = data.get("message")
                session = session_manager.get_session(session_id)

                session_manager.add_message(session_id, "user", message)

                # Search Knowledge Base for matching solutions
                kb_context = knowledge_base.get_context_for_query(message)

                # Check for matching task template
                template_match = task_planner.detect_template(message)

                # Get active task plan
                task_context = task_planner.get_context_for_session(session_id)

                # Send KB match event if solutions found
                if kb_context.get("has_matches"):
                    await manager.send_message(session_id, {
                        "type": "kb_match",
                        "problems": kb_context.get("problems", []),
                        "top_solutions": kb_context.get("top_solutions", [])
                    })

                # Send template detected event if match found
                if template_match and not task_context.get("has_active_plan"):
                    await manager.send_message(session_id, {
                        "type": "template_detected",
                        "template": template_match
                    })

                # Call Claude with context
                response = await claude_service.chat_with_context(
                    message=message,
                    conversation_history=session.get("messages", []),
                    kb_context=kb_context,
                    task_context=task_context
                )

                session_manager.add_message(session_id, "assistant", response["response"])

                await manager.send_message(session_id, {
                    "type": "ai_response",
                    "response": response["response"],
                    "had_kb_context": response.get("had_kb_context", False),
                    "had_task_context": response.get("had_task_context", False)
                })

            elif msg_type == "task_action":
                # Handle task-related actions
                action = data.get("action")
                plan_id = data.get("plan_id")
                step_id = data.get("step_id")
                template_id = data.get("template_id")

                if action == "create_from_template" and template_id:
                    plan = task_planner.create_from_template(session_id, template_id)
                    if plan:
                        await manager.send_message(session_id, {
                            "type": "task_created",
                            "plan": plan.to_dict()
                        })

                elif action == "start_plan" and plan_id:
                    result = task_planner.start_plan(plan_id)
                    if result:
                        await manager.send_message(session_id, {
                            "type": "task_started",
                            "plan": result,
                            "current_step": result.get("current_step")
                        })

                elif action == "complete_step" and plan_id and step_id:
                    result = task_planner.complete_step(plan_id, step_id)
                    if result:
                        await manager.send_message(session_id, {
                            "type": "step_completed",
                            "plan": result["plan"],
                            "completed_step": result["completed_step"],
                            "next_step": result.get("next_step"),
                            "is_complete": result.get("is_complete", False)
                        })

                elif action == "fail_step" and plan_id and step_id:
                    error_msg = data.get("error_message", "Step failed")
                    result = task_planner.fail_step(plan_id, step_id, error_msg)
                    if result:
                        await manager.send_message(session_id, {
                            "type": "step_failed",
                            "plan": result["plan"],
                            "failed_step": result["failed_step"],
                            "error_message": error_msg
                        })

                elif action == "skip_step" and plan_id and step_id:
                    result = task_planner.skip_step(plan_id, step_id)
                    if result:
                        await manager.send_message(session_id, {
                            "type": "step_completed",
                            "plan": result["plan"],
                            "skipped_step": result["skipped_step"],
                            "next_step": result.get("next_step"),
                            "is_complete": result.get("is_complete", False)
                        })

            elif msg_type == "kb_feedback":
                # Record solution feedback
                solution_id = data.get("solution_id")
                success = data.get("success", False)

                if solution_id:
                    knowledge_base.record_feedback(solution_id, success)
                    await manager.send_message(session_id, {
                        "type": "feedback_recorded",
                        "solution_id": solution_id,
                        "success": success
                    })

            elif msg_type == "ping":
                await manager.send_message(session_id, {"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.3.0",
        "name": "Akai",
        "capabilities": [
            "general_chat",
            "screen_vision",
            "code_analysis",
            "it_support",
            "creative_tasks"
        ],
        "services": {
            "claude": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 512
            },
            "knowledge_base": {
                "categories": len(knowledge_base.get_categories()),
                "problems": len(knowledge_base.problems),
                "solutions": len(knowledge_base.solutions)
            },
            "task_planner": {
                "templates": len(task_planner.templates),
                "active_plans": len([p for p in task_planner.plans.values() if p.status.value == "in_progress"])
            }
        }
    }


# Catch-all: serve React index.html for any non-API routes (client-side routing)
@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    """Serve React app for all non-API routes"""
    file_path = os.path.join(REACT_BUILD_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(REACT_BUILD_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "true").lower() == "true"
    )
