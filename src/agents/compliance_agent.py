from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.models.messages import AgentMessage, MessageType
import uuid, datetime
import asyncio
import re

class ComplianceAgent(BaseAgent):
    """
    Agent responsible for ensuring data privacy and compliance.
    Inspects payloads for PII and redacts them.
    """
    def __init__(self, agent_id, orchestrator):
        super().__init__(agent_id, orchestrator)
        self.pii_patterns = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b"
        }

    async def receive(self, message: AgentMessage):
        log_event("ComplianceAgent", f"Received request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        
        action = payload.get("action")
        
        response_payload = {}
        
        if action == "inspect":
            content = payload.get("content", "")
            redacted_content, flags = self._redact_pii(content)
            response_payload = {
                "status": "inspected",
                "is_compliant": len(flags) == 0,
                "redacted_content": redacted_content,
                "flags": flags
            }
        else:
            response_payload = {"status": "error", "message": f"Unknown action: {action}"}
            
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="compliance_agent",
            receiver=message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload=response_payload
        )
        
        return await self.orchestrator.send_a2a(response)

    def _redact_pii(self, text):
        flags = []
        redacted_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, redacted_text)
            if matches:
                flags.append(pii_type)
                redacted_text = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", redacted_text)
                
        if flags:
            log_event("ComplianceAgent", f"Redacted PII: {flags}")
            
        return redacted_text, flags
