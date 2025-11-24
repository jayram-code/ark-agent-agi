"""
Simple Demo API - Bypasses complex imports for quick demo
"""
import os
import sys
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import only what we need
from src.utils.gemini_utils import classify_intent, analyze_sentiment

app = FastAPI(title="ARK Agent AGI - Demo")

# Enable CORS for browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    text: str
    customer_id: Optional[str] = "C001"

@app.get("/")
async def root():
    return {"status": "healthy", "service": "ark-agent-agi-demo"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/v1/run")
async def run_agent(request: MessageRequest):
    """Simplified demo endpoint - shows intent + sentiment analysis"""
    try:
        # Classify intent
        intent_result = classify_intent(request.text)
        
        # Analyze sentiment
        sentiment_result = analyze_sentiment(request.text)
        
        # Calculate simple priority
        urgency_score = {"low": 3, "medium": 6, "high": 8, "critical": 10}
        priority = urgency_score.get(intent_result.get("urgency", "medium"), 5)
        
        # Determine routing based on intent
        routing_map = {
            "shipping_inquiry": "shipping_agent",
            "refund_request": "refund_agent",
            "technical_support": "tech_support_agent",
            "complaint": "supervisor_agent",
            "cancellation": "ticket_agent",
            "product_question": "knowledge_agent",
            "general_query": "ticket_agent"
        }
        routing = routing_map.get(intent_result.get("intent", "general_query"), "ticket_agent")
        
        return {
            "ok": True,
            "customer_id": request.customer_id,
            "intent": intent_result.get("intent"),
            "confidence": intent_result.get("confidence"),
            "urgency": intent_result.get("urgency"),
            "sentiment": {
                "emotion": sentiment_result.get("emotion"),
                "score": sentiment_result.get("sentiment_score"),
                "intensity": sentiment_result.get("intensity")
            },
            "priority_score": priority,
            "routing": routing,
            "ticket_id": f"TKT-{hash(request.text) % 100000:05d}",
            "status": "processed"
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "fallback": True
        }

# Batch processing state
batch_state = {
    'in_progress': False,
    'results': None,
    'progress': 0,
    'total': 0
}

@app.post("/api/v1/batch/scan")
async def scan_inbox():
    """Start batch email scan from Gmail"""
    global batch_state
    
    if batch_state['in_progress']:
        return {"ok": False, "error": "Scan already in progress"}
    
    try:
        # Start batch processing in background
        batch_state['in_progress'] = True
        batch_state['progress'] = 0
        
        # Import enterprise batch processor
        from src.integrations.gmail_api import get_gmail_api
        from src.services.batch_processor import enterprise_processor
        import asyncio
        
        gmail = get_gmail_api()
        
        # Fetch emails
        batch_state['total'] = 200
        emails = gmail.fetch_emails(max_results=200)
        
        # Process batch with enterprise processor
        results = await enterprise_processor.process_batch(emails)
        
        batch_state['results'] = results
        batch_state['in_progress'] = False
        batch_state['progress'] = batch_state['total']
        
        return {
            "ok": True,
            "message": f"Scanned {len(emails)} emails",
            "results": results
        }
        
    except FileNotFoundError as e:
        batch_state['in_progress'] = False
        return {
            "ok": False,
            "error": "Gmail credentials not found. Please setup credentials.json first.",
            "setup_guide": "See GMAIL_SETUP.md"
        }
    except Exception as e:
        batch_state['in_progress'] = False
        return {
            "ok": False,
            "error": str(e)
        }

@app.get("/api/v1/batch/status")
async def get_batch_status():
    """Get current batch processing status"""
    return {
        "ok": True,
        "in_progress": batch_state['in_progress'],
        "progress": batch_state['progress'],
        "total": batch_state['total'],
        "percentage": (batch_state['progress'] / batch_state['total'] * 100) if batch_state['total'] > 0 else 0
    }

@app.get("/api/v1/batch/results")
async def get_batch_results():
    """Get batch processing results"""
    if batch_state['results'] is None:
        return {"ok": False, "error": "No results available. Run scan first."}
    
    return {
        "ok": True,
        "results": batch_state['results']
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
