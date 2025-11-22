from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import uuid
import datetime


class MessageType(str, Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    QUERY = "query"  # New type for request-reply pattern
    ERROR = "error"
    INFO = "info"


class MessagePayload(BaseModel):
    """Base payload model, can be extended or used as generic dict wrapper"""

    text: Optional[str] = None
    intent: Optional[str] = None
    sentiment_score: Optional[float] = None
    customer_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Allow extra fields for flexibility
    class Config:
        extra = "allow"


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: Optional[str] = None
    sender: str
    receiver: str
    type: MessageType = MessageType.TASK_REQUEST
    timestamp: str = Field(default_factory=lambda: str(datetime.datetime.utcnow()))
    payload: Union[MessagePayload, Dict[str, Any]]

    @validator("timestamp", pre=True, always=True)
    def set_timestamp(cls, v):
        return v or str(datetime.datetime.utcnow())
