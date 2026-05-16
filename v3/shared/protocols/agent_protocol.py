"""Inter-agent communication protocol schemas using Pydantic v2."""

from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List


class MessageType(str, Enum):
    TASK_ASSIGNMENT = "TASK_ASSIGNMENT"
    TASK_COMPLETE = "TASK_COMPLETE"
    TASK_BLOCKED = "TASK_BLOCKED"
    ARTIFACT_DELIVERED = "ARTIFACT_DELIVERED"
    REVIEW_REQUEST = "REVIEW_REQUEST"
    REVIEW_FEEDBACK = "REVIEW_FEEDBACK"
    DEPENDENCY_REQUEST = "DEPENDENCY_REQUEST"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentMessage(BaseModel):
    """Standard inter-agent message format."""
    message_id: UUID = Field(default_factory=uuid4)
    correlation_id: Optional[UUID] = Field(default=None)
    sender: str
    recipient: str = "broadcast"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_type: MessageType
    priority: Priority = Priority.MEDIUM
    payload: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)


class TaskAssignment(BaseModel):
    """Task assignment from Orchestrator to an Agent."""
    task_id: UUID = Field(default_factory=uuid4)
    agent: str
    action: str
    phase: str
    project_path: str
    input_spec: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None


class TaskResult(BaseModel):
    """Result returned by an Agent after task completion."""
    task_id: UUID
    agent: str
    status: str  # "completed", "failed", "partial"
    generated_files: List[str] = Field(default_factory=list)
    validation: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    duration_ms: float = 0.0
