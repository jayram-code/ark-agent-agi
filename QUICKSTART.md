# 🚀 Quick Start Guide - ARK Agent AGI

## One-Command Deployment with Docker

### Prerequisites
- Docker & Docker Compose installed
- Google API Key (free from https://makersuite.google.com/app/apikey)

### Setup (30 seconds!)

1. **Clone and configure:**
```bash
git clone <your-repo>
cd ark-agent-agi

# Copy environment template
cp .env.example .env

# Edit .env and add your API key:
# GOOGLE_API_KEY=AIza...
# GEMINI_MODEL=gemini-1.5-pro  # or gemini-2.0-flash if you have paid tier
```

2. **Start everything:**
```bash
docker-compose up -d
```

3. **Open in browser:**
- 🌐 **Web UI**: http://localhost:8001
- 📡 **API Docs**: http://localhost:8000/docs
- 🏥 **Health Check**: http://localhost:8000/health

### Try It Out

**Web UI:**
1. Go to http://localhost:8001
2. Paste: *"My order #12345 never arrived! This is unacceptable!"*
3. Click "Run Agent"
4. Watch the magic! ✨

**API (curl):**
```bash
curl -X POST http://localhost:8000/api/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I want a refund for order #12345",
    "customer_id": "C001"
  }'
```

**Chrome Extension:**
1. `docker-compose down` (stop containers first)
2. `uvicorn src.api:app --reload` (run locally)
3. Load extension in Chrome (see below)
4. Go to Gmail and click extension icon!

### Stop Services
```bash
docker-compose down
```

---

## Alternative: Local Python Setup

### Install
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Backend
```bash
uvicorn src.api:app --reload
```

### Run Web UI
```bash
uvicorn app.main:app --reload --port 8001
```

### Run Chrome Extension
1. Open Chrome → `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `extension/` folder
5. Go to Gmail
6. Click extension icon 🎯

---

## 🎥 Video Demo

Want to see it in action? Check out our [2-minute demo video](DEMO_LINK_HERE)

## 🐛 Troubleshooting

**Port already in use?**
```bash
# Change ports in docker-compose.yml
ports:
  - "8080:8000"  # Use 8080 instead of 8000
```

**API key not working?**
- Make sure `.env` file exists in project root
- Check API key is valid at https://makersuite.google.com/app/apikey
- Try `GEMINI_MODEL=gemini-1.5-pro` if Flash is unavailable

**Rate limits?**
- Switch to `gemini-1.5-pro` in `.env`
- Add 1-2 second delays between requests

---

## 📊 What Happens Behind the Scenes

```
Your Email → Email Agent (classify intent)
         → Sentiment Agent (analyze emotion)
         → Priority Agent (calculate urgency)
         → Specialist Agent (refund/shipping/tech)
         → Response (<1s with Flash, 2-3s with Pro)
```

**Session Tracking**: Every conversation is saved to `logs/session_{id}.json`

**Memory**: Agent remembers customer history across conversations!

**Observability**: Check `logs/events.log` for detailed traces

---

Made with ❤️ for the hackathon judges!
