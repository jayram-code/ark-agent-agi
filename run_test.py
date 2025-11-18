from src.orchestrator import Orchestrator
from src.agents.email_agent import EmailAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.ticket_agent import TicketAgent
from src.agents.supervisor_agent import SupervisorAgent
from src.agents.memory_agent import MemoryAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.meeting_agent import MeetingAgent
from src.utils.pretty import pretty

# create orchestrator
orc = Orchestrator()

# create agents and register
agents = {
    "email_agent": EmailAgent("email_agent", orc),
    "sentiment_agent": SentimentAgent("sentiment_agent", orc),
    "ticket_agent": TicketAgent("ticket_agent", orc),
    "supervisor_agent": SupervisorAgent("supervisor_agent", orc),
    "memory_agent": MemoryAgent("memory_agent", orc),
    "knowledge_agent": KnowledgeAgent("knowledge_agent", orc),
    "meeting_agent": MeetingAgent("meeting_agent", orc),
}

for name, inst in agents.items():
    orc.register_agent(name, inst)

# 1) Build a sample message (complaint)
message = orc.new_message(
    sender="user",
    receiver="supervisor_agent",
    payload={
        "text": "My order didn't arrive and the tracking is blank. I want a refund.",
        "intent": "complaint",
        "customer_id": "C001"
    }
)

print("=== OUTGOING A2A MESSAGE ===")
pretty(message)
print("=== RUNNING PIPELINE ===")
res = orc.send_a2a(message)
print("=== FINAL RESPONSE ===")
pretty(res)

# 2) Demo: meeting transcript flow
meeting_msg = orc.new_message(
    sender="user",
    receiver="meeting_agent",
    payload={
        "transcript": "Attendees: Support lead and Customer. Action: Investigate order #123. Action item: Follow up in 2 days."
    }
)
print("\n=== RUNNING MEETING FLOW ===")
pretty(orc.send_a2a(meeting_msg))
