import time

class InMemorySessionService:
    def __init__(self):
        self.sessions = {}
        self.by_customer = {}

    def _get_s(self, session_id):
        return self.sessions.setdefault(session_id, {
            "messages": [],
            "tickets": [],
            "sentiments": [],
            "emotions": [],
            "priorities": [],
            "kv": {}
        })

    def _get_c(self, customer_id):
        return self.by_customer.setdefault(customer_id, {
            "messages": [],
            "tickets": [],
            "sentiments": [],
            "emotions": [],
            "priorities": [],
            "kv": {}
        })

    def update_from_message(self, message, output=None, latency_ms=None):
        session_id = message.get("session_id")
        payload = message.get("payload", {}) or {}
        customer_id = payload.get("customer_id")

        s = self._get_s(session_id)
        c = self._get_c(customer_id) if customer_id else None

        text = payload.get("text") or payload.get("summary")
        if text:
            s["messages"].append(text)
            if c:
                c["messages"].append(text)

        if payload.get("priority_score") is not None:
            s["priorities"].append(payload.get("priority_score"))
            if c:
                c["priorities"].append(payload.get("priority_score"))

        if payload.get("sentiment_score") is not None:
            s["sentiments"].append(payload.get("sentiment_score"))
            if c:
                c["sentiments"].append(payload.get("sentiment_score"))

        if payload.get("emotion"):
            s["emotions"].append(payload.get("emotion"))
            if c:
                c["emotions"].append(payload.get("emotion"))

        if output and isinstance(output, dict) and output.get("ticket_id"):
            t_id = output.get("ticket_id")
            s["tickets"].append(t_id)
            if c:
                c["tickets"].append(t_id)

        # store simple kv memory
        if c is not None:
            if payload.get("intent"):
                c["kv"]["last_intent"] = payload.get("intent")
            if payload.get("urgency"):
                c["kv"]["last_urgency"] = payload.get("urgency")
            c["kv"]["last_update_ts"] = time.time()

        # context compaction rules
        self.compact(session_id)
        if customer_id:
            self.compact_customer(customer_id)

    def compact(self, session_id, max_messages=20):
        s = self._get_s(session_id)
        # merge repeated messages
        s["messages"] = list(dict.fromkeys(s["messages"]))
        # summarize older interactions
        if len(s["messages"]) > max_messages:
            keep = s["messages"][-max_messages:]
            old = s["messages"][:-max_messages]
            summary = ", ".join(m.split(".")[0][:80] for m in old[:10])
            s["kv"]["history_summary"] = summary
            s["messages"] = keep

    def compact_customer(self, customer_id, max_messages=50):
        c = self._get_c(customer_id)
        c["messages"] = list(dict.fromkeys(c["messages"]))
        if len(c["messages"]) > max_messages:
            keep = c["messages"][-max_messages:]
            old = c["messages"][:-max_messages]
            summary = ", ".join(m.split(".")[0][:80] for m in old[:20])
            c["kv"]["history_summary"] = summary
            c["messages"] = keep

    def get_session(self, session_id):
        return self._get_s(session_id)

    def get_customer(self, customer_id):
        return self._get_c(customer_id)

# singleton
SESSION = InMemorySessionService()
