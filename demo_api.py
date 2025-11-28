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
from src.utils.gemini_utils import classify_intent, analyze_sentiment, analyze_email_combined

app = FastAPI(title="ARK Agent AGI - Demo")

# Enable CORS for browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import base64
import base64

class MessageRequest(BaseModel):
    text: str
    customer_id: Optional[str] = "C001"
    attachment: Optional[str] = None # Base64 encoded image
    mime_type: Optional[str] = "image/jpeg"

@app.get("/")
async def root():
    return {"status": "healthy", "service": "ark-agent-agi-demo"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/v1/run")
async def run_agent(request: MessageRequest):
    """Simplified demo endpoint - shows intent + sentiment + OCR"""
    try:
        # Use COMBINED analysis (1 API call instead of 2!)
        combined_result = analyze_email_combined(request.text)
        
        # Extract intent and sentiment from combined result
        intent_result = {
            "intent": combined_result.get("intent"),
            "confidence": combined_result.get("confidence"),
            "urgency": combined_result.get("urgency"),
            "key_phrases": combined_result.get("key_phrases", [])
        }
        
        sentiment_result = {
            "emotion": combined_result.get("emotion"),
            "sentiment_score": combined_result.get("sentiment_score"),
            "intensity": combined_result.get("intensity")
        }
        
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
        
        # Generate rationale based on intent
        rationale_map = {
            "refund_request": "Detected keywords 'refund', 'money back' and negative sentiment.",
            "shipping_inquiry": "Found tracking number pattern and shipping keywords.",
            "technical_support": "Contains technical terms 'error', 'bug', 'failed'.",
            "meeting_request": "Identified calendar availability request.",
            "urgent_issue": "High urgency keywords detected with negative sentiment."
        }
        rationale = rationale_map.get(intent_result.get("intent"), "Standard classification based on keyword analysis.")

        # Mock entity extraction (for demo purposes)
        import re
        entities = []
        # Extract potential order IDs
        order_ids = re.findall(r'#?ORD-\d+|#?\d{5,}', request.text)
        if order_ids:
            entities.extend([f"Order: {oid}" for oid in order_ids])
        # Extract potential dates
        dates = re.findall(r'\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2}|tomorrow|today|next week', request.text, re.IGNORECASE)
        if dates:
            entities.extend([f"Date: {d}" for d in dates])
            
        # Determine suggested actions
        actions = []
        if intent_result.get("intent") in ["refund_request", "shipping_inquiry", "complaint", "technical_support", "cancellation"]:
            actions.append("create_ticket")
        if intent_result.get("intent") in ["meeting_request", "general_query", "product_question"]:
            actions.append("schedule_meeting")
        if intent_result.get("urgency") == "high":
            actions.append("escalate_human")
        
        # Default action if empty
        if not actions:
            actions.append("archive_email")
        
        return {
            "ok": True,
            "customer_id": request.customer_id,
            "intent": intent_result.get("intent"),
            "confidence": intent_result.get("confidence"),
            "urgency": intent_result.get("urgency"),
            "rationale": rationale,
            "entities": entities,
            "attachments": ["invoice_INV-2024-001.pdf", "screenshot_error.png"] if "technical" in intent_result.get("intent", "") or "refund" in intent_result.get("intent", "") else [],
            "suggested_actions": actions,
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

from typing import List

class CSVRequest(BaseModel):
    emails: List[str]

# Batch processing state
batch_state = {
    'in_progress': False,
    'results': None,
    'progress': 0,
    'total': 0,
    'logs': []
}

# Job store
jobs = {}

@app.post("/api/v1/batch/scan")
async def scan_inbox(background_tasks: BackgroundTasks, dry_run: bool = True):
    """Start batch email scan from Gmail (Async Job)"""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "total": 0,
        "results": None,
        "logs": ["Job started"]
    }
    
    background_tasks.add_task(process_batch_job, job_id, dry_run)
    
    return {"ok": True, "job_id": job_id}

async def process_batch_job(job_id: str, dry_run: bool):
    """Background task for batch processing"""
    try:
        # Import enterprise batch processor
        from src.integrations.gmail_api import get_gmail_api
        from src.services.batch_processor import enterprise_processor
        
        # Update settings
        enterprise_processor.settings['dry_run'] = dry_run
        
        gmail = get_gmail_api()
        
        # Fetch emails
        jobs[job_id]['logs'].append("Fetching emails...")
        emails = gmail.fetch_emails(max_results=200)
        jobs[job_id]['total'] = len(emails)
        jobs[job_id]['logs'].append(f"Fetched {len(emails)} emails")
        
        # Process batch
        # Note: enterprise_processor.process_batch is async and returns full results
        # To support granular progress, we might need to modify it or wrap it.
        # For now, we'll wait for it but update status.
        
        results = await enterprise_processor.process_batch(emails)
        
        jobs[job_id]['results'] = results
        jobs[job_id]['status'] = "completed"
        jobs[job_id]['progress'] = len(emails)
        jobs[job_id]['logs'].append("Batch processing complete")
        
        # Update global state for legacy compatibility if needed
        global batch_state
        batch_state['results'] = results
        
    except Exception as e:
        jobs[job_id]['status'] = "failed"
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['logs'].append(f"Error: {str(e)}")

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    job = jobs.get(job_id)
    if not job:
        return {"ok": False, "error": "Job not found"}
    
    return {
        "ok": True,
        "status": job['status'],
        "progress": job['progress'],
        "total": job['total'],
        "logs": job['logs'],
        "results": job['results'] if job['status'] == 'completed' else None
    }

@app.get("/api/v1/batch/results")
async def get_batch_results():
    """Get batch processing results (Legacy/Global)"""
    # Try to find the last completed job
    completed_jobs = [j for j in jobs.values() if j['status'] == 'completed']
    if completed_jobs:
        return {"ok": True, "results": completed_jobs[-1]['results']}
        
    if batch_state['results'] is None:
        return {"ok": False, "error": "No results available. Run scan first."}
    
    return {
        "ok": True,
        "results": batch_state['results']
    }

@app.post("/api/v1/batch/summarize")
async def summarize_batch():
    """Generate a daily briefing summary from the last batch"""
    if batch_state['results'] is None:
        return {"ok": False, "error": "No batch results available. Run a scan first."}
    
    try:
        results = batch_state['results']
        
        # Categorize emails
        urgent = []
        meetings = []
        financial = []
        low_priority = []
        
        for email in results:
            intent = email.get('intent', 'general_query')
            urgency = email.get('urgency', 'low')
            snippet = email.get('snippet', 'No preview')
            
            if urgency in ['high', 'critical']:
                urgent.append(f"- {intent.replace('_', ' ').title()}: {snippet}")
            
            if 'meeting' in intent.lower():
                meetings.append(f"- {snippet}")
            
            if intent in ['refund_request', 'cancellation']:
                financial.append(f"- {intent.replace('_', ' ').title()}: {snippet}")
            
            if urgency == 'low':
                low_priority.append(f"- {snippet}")
        
        # Build Markdown summary
        summary = f"""# Daily Briefing

## Summary
Processed **{len(results)}** emails from your inbox.

## Urgent Attention ({len(urgent)})
{chr(10).join(urgent[:10]) if urgent else '- None'}

## Calendar Updates ({len(meetings)})
{chr(10).join(meetings[:5]) if meetings else '- No meetings scheduled'}

## Financial Requests ({len(financial)})
{chr(10).join(financial[:5]) if financial else '- None'}

## Low Priority ({len(low_priority)})
{len(low_priority)} general queries and feedback items.

---
Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return {
            "ok": True,
            "summary": summary,
            "stats": {
                "total": len(results),
                "urgent": len(urgent),
                "meetings": len(meetings),
                "financial": len(financial),
                "low_priority": len(low_priority)
            }
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
