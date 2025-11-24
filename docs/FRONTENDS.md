# 🎨 Frontend Options - ARK Agent AGI

You have **3 complete frontend interfaces** to interact with the agent system!

## 1. 🌐 Web UI (FastAPI + HTML) - RECOMMENDED FOR DEMOS

### Features
- Clean, modern interface
- Real-time agent processing
- JSON response viewer
- Perfect for live demos!

### Quick Start
```bash
# Terminal 1: Start API
uvicorn src.api:app --reload

# Terminal 2: Start Web UI  
uvicorn app.main:app --reload --port 8001

# Open browser
http://localhost:8001
```

### What You See
```
┌──────────────────────────────────────┐
│  ARK Agent AGI — Demo                │
├──────────────────────────────────────┤
│ Input Text (Email/Query):            │
│ ┌──────────────────────────────────┐│
│ │ My order hasn't arrived!        ││
│ │ Very frustrated with service... ││
│ └──────────────────────────────────┘│
│ Customer ID: C001                    │
│ [Run Agent]                          │
├──────────────────────────────────────┤
│ Response:                            │
│ ┌──────────────────────────────────┐│
│ │ {                                ││
│ │   "intent": "shipping_inquiry",  ││
│ │   "sentiment": "frustrated",     ││
│ │   "priority": 7.5,              ││
│ │   "routing": "shipping_agent",   ││
│ │   "ticket_id": "TKT-12345"      ││
│ │ }                                ││
│ └──────────────────────────────────┘│
└──────────────────────────────────────┘
```

---

## 2. 🔌 Chrome Extension (Gmail Integration) - COOLEST FOR JUDGES!

### Features
- Extracts email content from Gmail
- One-click agent processing
- Popup shows agent response
- **Perfect for "wow factor"!** ✨

### Installation
```bash
1. Start API backend first:
   uvicorn src.api:app --reload

2. Open Chrome → chrome://extensions

3. Enable "Developer mode" (top right toggle)

4. Click "Load unpacked"

5. Navigate to and select:
   c:\Users\jaisu\ark-agent-agi\extension

6. Pin the extension to toolbar (puzzle icon)
```

### Usage
```bash
1. Go to Gmail: https://mail.google.com

2. Open any email

3. Click the ARK Agent extension icon

4. Click "📥 Extract Email Content"
   → Email text appears in textarea

5. Click "🚀 Run Agent"
   → AI processes the email

6. See results in popup:
   - Intent detected
   - Sentiment analyzed
   - Priority calculated
   - Ticket created!
```

### Demo Flow for Judges
```
1. Show Gmail inbox with complaint email
2. Click extension → Extract
3. Click Run Agent
4. Show response in <3 seconds
5. Judges = 🤯
```

---

## 3. 📡 REST API (For Developers)

### Endpoints

**Base URL**: `http://localhost:8000`

#### Health Check
```bash
GET /health

Response:
{"status": "ok"}
```

#### Run Agent
```bash
POST /api/v1/run

Body:
{
  "text": "I want a refund for order #12345",
  "customer_id": "C001",
  "session_id": "optional-session-id"
}

Response:
{
  "ok": true,
  "result": {
    "intent": "refund_request",
    "sentiment": {
      "emotion": "frustrated",
      "score": -0.6
    },
    "priority": 8.5,
    "routing": "refund_agent",
    "ticket_id": "TKT-67890"
  }
}
```

#### API Docs (Interactive)
```bash
http://localhost:8000/docs
```
- Try endpoints directly in browser
- See request/response schemas
- Test authentication

---

## 4. 💻 CLI (Human-in-the-Loop)

For approving escalated tasks:

```bash
# List pending escalations
python human_cli.py list

# Approve a task
python human_cli.py approve TASK_ID --feedback "Approved, proceed"

# Reject a task
python human_cli.py reject TASK_ID --reason "Invalid request"
```

---

## 🎬 Recommended Demo Sequence

### For Hackathon Judges (5 min)

**1. Docker Quick Start (1 min)**
```bash
docker-compose up -d
# Open http://localhost:8001
```

**2. Web UI Demo (2 min)**
- Paste shipping inquiry
- Show fast routing (<1s with Flash)
- Highlight session tracking in logs/

**3. Chrome Extension (2 min)**
- Open Gmail
- Extract real email
- Run agent
- Show AI classification

**Bonus**: Show `logs/events.log` for observability!

---

## 🐛 Troubleshooting

**API not responding?**
```bash
# Check if running
curl http://localhost:8000/health

# Restart
docker-compose restart api
```

**Extension not finding API?**
```bash
# Check popup.js line 45
const API_URL = "http://localhost:8000";

# Make sure API is running locally (not in Docker)
uvicorn src.api:app --reload
```

**CORS errors in extension?**
```bash
# Add to src/api.py:

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 What to Show Judges

### Must-Show Features
1. ✅ **Dual model support** (show .env config)
2. ✅ **Multi-agent routing** (logs show each agent)
3. ✅ **Session persistence** (check logs/session_*.json)
4. ✅ **Fast response** (<3s end-to-end)
5. ✅ **Chrome extension** (easiest "wow" moment)

### Nice-to-Show
- Memory: Run 2 queries from same customer_id
- Escalation: High-priority case → check human_queue.json
- Tools: Show knowledge base lookup in logs
- Observability: metrics, traces, session replay

---

## 🎥 Recording Tips

If making a demo video:

```bash
# Good flow:
1. Show README (10s)
2. docker-compose up (5s)
3. Open web UI (10s) → paste email → run
4. Show Chrome extension (20s)
5. Show logs/session file (10s)
6. Outro: "Ready for production!" (5s)

Total: 60 seconds!
```

---

Made with ❤️ for judges who appreciate both tech AND UX!
