from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.storage.ticket_db import create_ticket

class TicketAgent(BaseAgent):
    def receive(self, message):
        log_event("TicketAgent", "Creating ticket")

        intent = message["payload"]["intent"]
        text = message["payload"]["text"]
        sentiment = message["payload"]["sentiment_score"]

        ticket_id = create_ticket(intent, text, sentiment)

        return {"status": "ticket_created", "ticket_id": ticket_id}
