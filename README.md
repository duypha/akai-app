# Akai - AI Screen Assistant

Your friendly AI buddy that can see your screen and help with anything.

## Overview

Akai is an AI-powered screen assistant that can:
- 🎤 Listen to users via voice (Deepgram Nova-3)
- 📺 See user's screen through screen sharing
- 🤖 Analyze problems using Claude Vision AI
- 🔊 Respond with voice and text
- 💬 Have natural conversations about IT issues
- 📋 Guide users through step-by-step task plans
- 🗂️ Search a curated IT knowledge base

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add:
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- `DEEPGRAM_API_KEY` - Get from https://console.deepgram.com/ (required for voice input)
- `OPENAI_API_KEY` - Get from https://platform.openai.com/ (optional, for voice output)

### 3. Run the Server

```bash
cd backend
python run.py
```

### 4. Open in Browser

Go to: http://localhost:8000

## Features

- ✅ Session management with short codes
- ✅ Text chat with Claude AI (context-aware)
- ✅ Screen sharing via WebRTC
- ✅ Screenshot capture and analysis (Claude Vision)
- ✅ Voice input (Deepgram Nova-3 STT)
- ✅ Voice output (OpenAI TTS)
- ✅ Real-time WebSocket communication
- ✅ Knowledge Base (20+ IT problems, 50+ solutions)
- ✅ Task Planner (16 templates for common IT fixes)
- ✅ Solution feedback tracking

## Project Structure

```
akai-app/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application
│   │   └── services/
│   │       ├── claude_service.py    # Claude Vision & Chat
│   │       ├── speech_service.py    # Deepgram STT & OpenAI TTS
│   │       ├── session_manager.py   # Session handling
│   │       ├── knowledge_base.py    # IT problem/solution database
│   │       ├── task_planner.py      # Step-by-step task plans
│   │       └── database.py          # SQLite persistence
│   ├── tests/
│   │   ├── test_knowledge_base.py
│   │   ├── test_task_planner.py
│   │   └── test_session_manager.py
│   ├── requirements.txt
│   ├── run.py
│   └── .env
├── frontend-react/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── contexts/
│   │   └── hooks/
│   ├── public/
│   └── package.json
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/session/create` | POST | Create new session |
| `/api/session/join` | POST | Join with code |
| `/api/chat` | POST | Send chat message |
| `/api/screen/analyze` | POST | Analyze screenshot |
| `/api/voice/transcribe` | POST | Speech to text |
| `/api/voice/synthesize` | POST | Text to speech |
| `/api/knowledge/search` | GET | Search knowledge base |
| `/api/knowledge/solutions/{id}/feedback` | POST | Record solution feedback |
| `/api/tasks/templates` | GET | List task templates |
| `/api/tasks/create-from-message` | POST | Auto-detect and create task plan |
| `/api/tasks/{plan_id}/start` | POST | Start a task plan |
| `/api/tasks/{plan_id}/steps/{step_id}/complete` | POST | Complete a step |
| `/ws/{session_id}` | WS | Real-time communication |
| `/health` | GET | Service health check |

## Usage

1. **Start a Session**: Click "Start New Session" or enter a code
2. **Describe Your Problem**: Type or speak your issue
3. **Share Screen**: Click "Share Screen" to let AI see your computer
4. **Get Help**: AI will analyze and guide you step by step
5. **Follow the Plan**: Use the task panel to tick off steps

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## Next Phases

- **Phase 3**: Mouse/keyboard control, camera integration
- **Phase 4**: Enterprise deployment, MDM support

## License

Internal use only.
