from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Literal, Dict, List, Optional
import uuid

class MetricPoint(BaseModel):
    metric_name: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = Field(default_factory=dict)

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnomalyEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str
    timestamp: datetime
    value: float
    expected_min: float
    expected_max: float
    z_score: float
    severity: Severity
    context_window: List[float]
    detection_method: str

class RootCause(BaseModel):
    cause: str
    likelihood: Literal["high", "medium", "low"]

class LLMOutput(BaseModel):
    explanation: str
    root_causes: List[RootCause]
    incident_summary: str
    confidence: float

class AnomalyExplanation(BaseModel):
    event: AnomalyEvent
    llm_output: Optional[LLMOutput] = None
    inference_time_ms: int
    retry_count: int
    fallback_used: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)