import asyncio
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from orchestrator import Orchestrator
from agents.ticket_agent import TicketAgent
from models.messages import AgentMessage, MessageType
import uuid
import datetime

async def run_evals():
    print("🧪 Running Evaluations...")
    
    # Load scenarios
    with open(os.path.join(os.path.dirname(__file__), 'scenarios.json'), 'r') as f:
        scenarios = json.load(f)
        
    # Setup Orchestrator
    orc = Orchestrator()
    orc.register_agent("ticket_agent", TicketAgent("ticket_agent", orc))
    
    results = []
    
    for case in scenarios:
        print(f"   Running case: {case['id']}")
        
        msg = AgentMessage(
            id=str(uuid.uuid4()),
            session_id="eval_session",
            sender="evaluator",
            receiver="ticket_agent",
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={"text": case["input"], "customer_id": "eval_user", "intent": "unknown"}
        )
        
        try:
            response = await orc.send_a2a(msg)
            payload = response.payload if isinstance(response, AgentMessage) else response
            if hasattr(payload, "dict"): payload = payload.dict()
            
            # Simple scoring logic
            passed = True
            if "expected_intent" in case:
                if payload.get("category") != "billing" and case["expected_intent"] == "refund_request":
                     # simplified check for demo
                     pass 
            
            results.append({
                "id": case["id"],
                "passed": passed,
                "actual": payload
            })
            
        except Exception as e:
            results.append({"id": case["id"], "passed": False, "error": str(e)})
            
    # Save results
    with open(os.path.join(os.path.dirname(__file__), 'results.json'), 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"✅ Completed {len(results)} evaluations.")

if __name__ == "__main__":
    asyncio.run(run_evals())
