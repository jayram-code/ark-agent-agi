# app/main.py
import os
import json
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from google.cloud import storage
from pathlib import Path
import importlib
import sys

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# init
app = FastAPI(title="ARK Agent AGI - Cloud Run API (Demo)")
logging.basicConfig(level=logging.INFO)

# config from env
GCS_BUCKET = os.getenv("GCS_BUCKET")  # required if using persistent storage
GCS_PREFIX = os.getenv("GCS_PREFIX", "ark-agent")
LOCAL_MODELS_DIR = Path("/app/models")
LOCAL_DATA_DIR = Path("/app/data")
LOCAL_RUNTIME = Path("/app/runtime")
LOCAL_MODELS_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_RUNTIME.mkdir(parents=True, exist_ok=True)

def download_from_gcs(bucket_name, prefix, local_dir: Path):
    if not bucket_name:
        logging.info("No GCS_BUCKET configured; skipping download.")
        return
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blobs = client.list_blobs(bucket_name, prefix=prefix)
        for blob in blobs:
            if blob.name.endswith("/"): continue
            rel_path = blob.name[len(prefix):].lstrip("/")
            target = local_dir / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            logging.info(f"Downloading gs://{bucket_name}/{blob.name} -> {target}")
            blob.download_to_filename(str(target))
    except Exception as e:
        logging.error(f"Failed to download from GCS: {e}")

@app.on_event("startup")
def startup():
    logging.info("Startup: ensure persistent files available")
    if GCS_BUCKET:
        download_from_gcs(GCS_BUCKET, GCS_PREFIX, LOCAL_MODELS_DIR)
        download_from_gcs(GCS_BUCKET, f"{GCS_PREFIX}/db", LOCAL_RUNTIME)
    # optionally load models here (defer heavy load until first request)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/run")
async def run_agent(request: Request, background: BackgroundTasks):
    """
    Entry point for REST: payload structure:
    {
      "source":"email"|"api"|"webhook",
      "text": "...",
      "customer_id":"C001",
      "metadata": { ... }
    }
    """
    payload = await request.json()
    # minimal processing: handoff to orchestrator.run(payload)
    try:
        # lazy import of your orchestrator so it's not heavy at import time
        from src.core.orchestrator import Orchestrator
        from src.agents.email_agent import EmailAgent
        
        # Initialize Orchestrator
        orc = Orchestrator()
        
        # Register Agents (Bootstrap minimal set or all)
        # In a real app, you'd probably have a bootstrap function
        orc.register_agent("email_agent", EmailAgent("email_agent", orc))
        
        # For demo purposes, we might need more agents if the flow gets complex
        # But let's stick to the requested minimal setup for now, or maybe register all?
        # Let's register all to be safe since we have them.
        from src.agents.sentiment_agent import SentimentAgent
        from src.agents.ticket_agent import TicketAgent
        from src.agents.supervisor_agent import SupervisorAgent
        orc.register_agent("sentiment_agent", SentimentAgent("sentiment_agent", orc))
        orc.register_agent("ticket_agent", TicketAgent("ticket_agent", orc))
        orc.register_agent("supervisor_agent", SupervisorAgent("supervisor_agent", orc))

        # call orchestrator.send_a2a with proper A2A message format
        import uuid
        import datetime
        from src.models.messages import AgentMessage, MessageType
        
        msg = AgentMessage(
            id=payload.get("id", str(uuid.uuid4())),
            session_id=payload.get("session_id", str(uuid.uuid4())),
            sender=payload.get("sender","api_user"),
            receiver="email_agent",
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "text": payload.get("text"),
                "customer_id": payload.get("customer_id"),
                "metadata": payload.get("metadata", {})
            }
        )
        
        res = await orc.route(msg)
        return JSONResponse({"ok": True, "result": res})
    except Exception as e:
        logging.exception("Error running agent")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.post("/api/v1/inbound_email")
async def inbound_email(payload: dict):
    """
    Webhook endpoint for incoming emails (SendGrid / Mailgun inbound parse).
    Accepts the parsed email body and forwards to /api/v1/run.
    """
    text = payload.get("text") or payload.get("body") or ""
    customer = payload.get("from") or payload.get("customer_id", "unknown")
    # trigger background agent run
    # For demo, call run_agent synchronously (simulated request):
    # We construct a mock request object
    class MockRequest:
        async def json(self):
            return {"text": text, "customer_id": customer, "source": "email"}
            
    return await run_agent(MockRequest(), background=BackgroundTasks())

@app.get("/", response_class=HTMLResponse)
def web_ui():
    # tiny UI to submit text to /api/v1/run
    return HTMLResponse("""
    <html>
      <head>
        <title>ARK Agent AGI — Demo</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f0f2f5; }
            .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h2 { color: #1a73e8; }
            textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 10px; font-family: inherit; }
            input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 10px; }
            button { background: #1a73e8; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; }
            button:hover { background: #1557b0; }
            pre { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; }
        </style>
      </head>
      <body>
        <div class="container">
            <h2>ARK Agent AGI — Demo</h2>
            <form id="f">
            <label>Input Text (Email/Query):</label>
            <textarea id="text" rows="6" placeholder="Paste email or issue here..."></textarea>
            <label>Customer ID:</label>
            <input id="cid" placeholder="C001" value="C001" />
            <button type="button" onclick="send()">Run Agent</button>
            </form>
            <h3>Response:</h3>
            <pre id="out">Waiting for input...</pre>
        </div>
        <script>
          async function send(){
            const out = document.getElementById('out');
            out.textContent = "Processing...";
            const text = document.getElementById('text').value;
            const cid = document.getElementById('cid').value || "C_DEMO";
            try {
                const r = await fetch('/api/v1/run', {
                method:'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({text:text, customer_id:cid})
                });
                const j = await r.json();
                out.textContent = JSON.stringify(j, null, 2);
            } catch (e) {
                out.textContent = "Error: " + e;
            }
          }
        </script>
      </body>
    </html>
    """)
