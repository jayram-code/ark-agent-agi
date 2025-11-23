import datetime
import time
import uuid

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from storage.ticket_db import create_ticket, derive_category
from utils.observability.logging_utils import log_event
from utils.observability.metrics import increment, record_latency


class TicketAgent(BaseAgent):
    async def receive(self, message: AgentMessage):
        # defensive: support multiple message shapes from different agents
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        log_event(
            "TicketAgent", {"event": "received_payload", "payload_keys": list(payload.keys())}
        )
        start = time.time()

        # Try multiple places for intent/text/sentiment (planner, supervisor, knowledge wrapping)
        intent = payload.get("intent")
        if intent is None:
            # check nested original payloads used by some agents
            original = payload.get("original") or payload.get("original", {})
            if isinstance(original, dict):
                intent = original.get("intent")
        if intent is None:
            # sometimes planner supplies original inside payload -> original.original...
            try:
                intent = payload.get("original", {}).get("original", {}).get("intent")
            except Exception:
                intent = None

        text = payload.get("text")
        if text is None:
            # planner provides 'original' or 'summary' or 'plan' with details
            text = (
                payload.get("original", {}).get("text")
                or payload.get("summary")
                or str(payload.get("plan", ""))
            )

        sentiment = payload.get("sentiment_score")
        if sentiment is None:
            # attempt to find sentiment nested in original
            sentiment = payload.get("original", {}).get("sentiment_score", 0.0)

        # Extract additional workflow automation fields
        key_phrases = payload.get("key_phrases") or payload.get("original", {}).get(
            "key_phrases", []
        )
        customer_id = payload.get("customer_id") or payload.get("original", {}).get("customer_id")
        priority_score = payload.get("priority_score") or payload.get("original", {}).get(
            "priority_score"
        )

        # Auto-derive category from intent if not provided
        category = derive_category(intent)

        # Convert tags from key_phrases for better organization
        tags = key_phrases if isinstance(key_phrases, list) else []

        # final safe defaults
        if intent is None:
            intent = "unknown"
        if text is None:
            text = ""

        log_event(
            "TicketAgent",
            {
                "event": "creating_ticket",
                "intent": intent,
                "category": category,
                "text_preview": text[:120],
                "sentiment": sentiment,
                "key_phrases": key_phrases,
                "customer_id": customer_id,
                "priority_score": priority_score,
            },
        )

        ticket_id = create_ticket(
            intent=intent,
            text=text,
            sentiment=sentiment or 0.0,
            category=category,
            tags=tags,
            key_phrases=key_phrases,
            customer_id=customer_id,
            priority_score=priority_score or 0.0,
            status="open",
        )

        log_event(
            "TicketAgent",
            {"event": "ticket_created", "ticket_id": ticket_id, "category": category, "tags": tags},
        )
        record_latency(
            "ticket_generation_time_ms", (time.time() - start) * 1000.0, tags={"category": category}
        )
        increment("tickets_created", 1, tags={"category": category})

        # Return result directly (end of chain usually)
        return {
            "status": "ticket_created",
            "ticket_id": ticket_id,
            "category": category,
            "tags": tags,
        }
