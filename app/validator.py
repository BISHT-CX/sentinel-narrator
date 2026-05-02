import json
import logging
import re
from .schemas import LLMOutput, RootCause, AnomalyEvent

logger = logging.getLogger(__name__)

def _parse_flat(raw: str) -> LLMOutput:
    # Strip markdown fences
    text = re.sub(r"```json\n?", "", raw)
    text = re.sub(r"```\n?", "", text)
    text = text.strip()
    
    # Find JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found")
    
    text = text[start:end]
    data = json.loads(text)
    
    # Build LLMOutput from flat structure
    root_causes = [
        RootCause(cause=data.get("cause1", "Unknown cause"), likelihood="high"),
        RootCause(cause=data.get("cause2", "Unknown cause"), likelihood="medium"),
        RootCause(cause=data.get("cause3", "Unknown cause"), likelihood="low"),
    ]
    
    return LLMOutput(
        explanation=data.get("explanation", "Anomaly detected."),
        root_causes=root_causes,
        incident_summary=data.get("summary", "Anomaly detected. Investigation required."),
        confidence=float(data.get("confidence", 0.5))
    )

def validate_llm_output(raw: str, event: AnomalyEvent, model, max_retries: int):
    retry_count = 0
    current_raw = raw
    
    for attempt in range(max_retries + 1):
        try:
            result = _parse_flat(current_raw)
            return result, retry_count, False
        except Exception as e:
            logger.warning(f"Validation failed attempt {attempt}: {e}")
            if attempt < max_retries:
                retry_count += 1
                retry_prompt = f"""Reply with ONLY a JSON object. No markdown. Start with {{.

{{"explanation":"one sentence about the anomaly","cause1":"top cause","cause2":"second cause","cause3":"third cause","summary":"slack alert paragraph","confidence":0.7}}

Anomaly: metric={event.metric_name} value={event.value:.2f} severity={event.severity.value}

JSON:"""
                try:
                    current_raw, _ = model.infer(retry_prompt)
                except Exception:
                    continue
    
    # Hardcoded fallback
    fallback = LLMOutput(
        explanation=f"{event.metric_name} deviated {abs(event.z_score):.1f} standard deviations from baseline.",
        root_causes=[
            RootCause(cause="Unexpected load spike", likelihood="high"),
            RootCause(cause="Dependency failure", likelihood="medium"),
            RootCause(cause="Configuration change", likelihood="low"),
        ],
        incident_summary=f"ALERT [{event.severity.value.upper()}]: {event.metric_name} = {event.value:.2f} (expected {event.expected_min:.2f}-{event.expected_max:.2f}). Z-score: {event.z_score:.2f}. Immediate investigation recommended.",
        confidence=0.0
    )
    return fallback, retry_count, True
