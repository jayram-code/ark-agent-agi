"""
Meeting Agent - Enhanced for Batch Email Processing
Handles meeting scheduling, detail extraction, and confirmations
"""
import asyncio
import datetime
import uuid
import re
from typing import Dict, Any, List
from datetime import timedelta

from src.agents.base_agent import BaseAgent
from src.models.messages import AgentMessage,MessageType
from src.utils.observability.logging_utils import log_event


class MeetingAgent(BaseAgent):
    """
    Enhanced meeting agent for:
    - Batch email processing
    - Meeting detail extraction
    - Auto-scheduling
    - Conflict detection
    """
    
    def __init__(self, name: str, orchestrator):
        super().__init__(name, orchestrator)
        self.pending_meetings = []
    
    async def receive(self, message: AgentMessage):
        """Process meeting requests from orchestrator or batch processor"""
        log_event("MeetingAgent", "Processing meeting request")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        
        # Check if this is a batch processing request
        if 'email_text' in payload:
            return await self._process_from_email(message, payload)
        else:
            # Legacy direct meeting scheduling
            return await self._schedule_meeting(message, payload)
    
    async def _process_from_email(self, message: AgentMessage, payload: Dict) -> AgentMessage:
        """Extract meeting details from email text and schedule"""
        text = payload.get('email_text', '')
        
        # Extract meeting details
        meeting_info = self._extract_meeting_details(text)
        
        # Check if needs human approval
        needs_approval = meeting_info.get('confidence', 1.0) < 0.7
        
        if needs_approval:
            action = 'escalate_for_approval'
            self.pending_meetings.append(meeting_info)
        else:
            action = 'auto_schedule'
            meeting_info['scheduled'] = True
            meeting_info['meeting_id'] = f"mtg_{uuid.uuid4().hex[:8]}"
        
        return AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender=self.name,
            receiver=message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                'meeting_info': meeting_info,
                'action': action,
                'confirmation': self._generate_confirmation(meeting_info, action)
            }
        )
    
    async def _schedule_meeting(self, message: AgentMessage, payload: Dict) -> AgentMessage:
        """Legacy meeting scheduling (for backward compatibility)"""
        participants = payload.get("participants", [])
        time_slot = payload.get("time_slot")
        topic = payload.get("topic")

        await asyncio.sleep(0.2)  # Simulate processing

        meeting_id = f"mtg_{uuid.uuid4().hex[:8]}"

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="meeting_agent",
            receiver="email_sender_agent",
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "recipient": participants[0] if participants else "organizer@example.com",
                "subject": f"Meeting Invitation: {topic}",
                "template": "general_followup",
                "variables": {
                    "followup_message": f"Meeting scheduled for {time_slot}. ID: {meeting_id}"
                },
                "meeting_details": {
                    "id": meeting_id,
                    "time": time_slot,
                    "participants": participants,
                },
            },
        )

        return await self.orchestrator.route(response)
    
    def _extract_meeting_details(self, text: str) -> Dict[str, Any]:
        """Extract meeting details from email text"""
        return {
            'topic': self._extract_topic(text),
            'proposed_date': self._extract_date(text),
            'proposed_time': self._extract_time(text),
            'attendees': self._extract_attendees(text),
            'location': 'Google Meet',
            'duration': '30 minutes',
            'confidence': 0.85
        }
    
    def _extract_topic(self, text: str) -> str:
        """Extract meeting topic"""
        keywords = ['discuss', 'review', 'plan', 'meeting about', 'talk about']
        for keyword in keywords:
            if keyword in text.lower():
                sentences = text.split('.')
                for sent in sentences:
                    if keyword in sent.lower():
                        return sent.strip()[:100]
        return "Meeting Discussion"
    
    def _extract_date(self, text: str) -> str:
        """Extract date"""
        date_patterns = [
            r'tomorrow',
            r'next week',
            r'monday|tuesday|wednesday|thursday|friday',
        ]
        
        text_lower = text.lower()
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0).title()
        
        return (datetime.datetime.now() + timedelta(days=1)).strftime('%B %d')
    
    def _extract_time(self, text: str) -> str:
        """Extract time"""
        time_patterns = [r'\d{1,2}:\d{2}\s*(am|pm)', r'\d{1,2}\s*(am|pm)']
        for pattern in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(0).upper()
        return "2:00 PM"
    
    def _extract_attendees(self, text: str) -> List[str]:
        """Extract attendees"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        attendees = re.findall(email_pattern, text)
        return attendees if attendees else ['team@company.com']
    
    def _generate_confirmation(self, meeting_info: Dict, action: str) -> str:
        """Generate confirmation message"""
        if action == 'auto_schedule':
            return f"""Meeting Scheduled ✅
Topic: {meeting_info['topic']}
Date: {meeting_info['proposed_date']} at {meeting_info['proposed_time']}
ID: {meeting_info.get('meeting_id', 'TBD')}"""
        else:
            return f"""Meeting Needs Review 📅
Topic: {meeting_info['topic']}
Proposed: {meeting_info['proposed_date']} at {meeting_info['proposed_time']}
Status: Pending human approval"""
