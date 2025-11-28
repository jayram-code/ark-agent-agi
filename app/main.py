# app/main.py
import time, asyncio, os
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel
from uuid import uuid4
from typing import List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ARK Job Server")

# Allow requests from extension / testing clients
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# In-memory jobs dict (job_id -> dict). Replace with Redis for prod.
jobs: Dict[str, Dict[str, Any]] = {}

# Dummy orchestrator analyze function - replace with your orchestrator call
def analyze_single_email_text(text: str) -> Dict[str, Any]:
    # Normally call orchestrator.analyze(text) or orchestrator.send_a2a(message)
    # For demo, return a fake analysis with random-ish data
    import random
    intents = ["complaint","meeting","invoice","general_query","support_request"]
    intent = random.choice(intents)
    return {
        "intent": intent,
        "confidence": round(random.uniform(0.6, 0.98), 2),
        "summary": text[:200],
        "entities": { "order": None }
    }

class BatchRequest(BaseModel):
    emails: List[str] = None
    take: int = None  # if provided, instruct backend to fetch N emails from mail connector

@app.get("/api/v1/ping")
async def ping():
    return {"msg":"pong"}

@app.post("/api/v1/batch")
async def start_batch(req: BatchRequest, background_tasks: BackgroundTasks):
    # if req.emails provided, use them otherwise use take to fetch from mailbox
    job_id = str(uuid4())
    emails = req.emails or []
    if not emails and (req.take is None or req.take <= 0):
        # quick default - return error, or fetch from your mailbox connector
        raise HTTPException(status_code=400, detail="Provide emails or take>0")
    # If take provided, we would fetch that many via Gmail/IMAP — here stub simple generation for demo
    if not emails and req.take:
        # TODO: integrate Gmail API / IMAP fetcher. For demo, create N fake sample emails.
        emails = [f"Subject: Demo email {i}\nBody: This is a test email number {i}" for i in range(1, req.take+1)]

    jobs[job_id] = {"status":"running", "progress":0, "total": len(emails), "processed":0, "results":[], "created_at": time.time()}
    background_tasks.add_task(process_batch_job, job_id, emails)
    return {"job_id": job_id}

@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job

@app.post("/api/v1/daily_brief")
async def daily_brief():
    # For demo: summarize last N processed entries from jobs store
    all_results = []
    for j in jobs.values():
        if j.get("results"):
            all_results.extend(j["results"])
    # Compose a simple summary
    total = len(all_results)
    counts = {}
    for r in all_results:
        counts[r["intent"]] = counts.get(r["intent"], 0) + 1
    summary = {
        "total_processed": total,
        "by_intent": counts,
        "generated_at": time.time()
    }
    return {"summary": summary}

async def process_batch_job(job_id: str, emails: List[str]):
    try:
        j = jobs[job_id]
        total = len(emails)
        for idx, e in enumerate(emails, start=1):
            # simulate a call to your orchestrator/analyzer (which might be async).
            # Replace with await orchestrator.analyze(e) as needed.
            res = analyze_single_email_text(e)
            j["results"].append(res)
            j["processed"] = idx
            j["progress"] = int((idx/total)*100)
            # small sleep to simulate processing & avoid rate limit storms
            await asyncio.sleep(0.2)
        j["status"] = "completed"
        j["completed_at"] = time.time()
        # compute a lightweight summary
        by_intent = {}
        for r in j["results"]:
            by_intent[r["intent"]] = by_intent.get(r["intent"], 0) + 1
        j["summary"] = {"total": total, "by_intent": by_intent}
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

# ticket endpoint example (used by popup for create ticket)
class TicketIn(BaseModel):
    title: str
    body: str
    tags: List[str] = []
@app.post("/api/v1/tickets")
async def create_ticket(t: TicketIn):
    ticket_id = str(uuid4())[:8]
    # persist to DB - here we add to a jobs store for demo
    return {"ticket_id": ticket_id, "status":"created", "title": t.title}

# run by uvicorn when deployed
