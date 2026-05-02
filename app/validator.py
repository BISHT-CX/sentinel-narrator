import json
import logging
from .schemas import AnomalyEvent, LLMOutput
from .llm import GemmaModel
from .prompt_builder import build_prompt

logger = logging.getLogger(__name__)

def validate_llm_output(raw: str, event: AnomalyEvent, model: GemmaModel, max_retries: int) -> tuple[LLMOutput | None, int, bool]:
    prompt = build_prompt(event)
    current_raw = raw
    retry_count = 0

    for attempt in range(max_retries + 1):
        cleaned = current_raw.strip('` \n')
        if cleaned.startswith('json\n'):
            cleaned = cleaned[5:]
            
        try:
            parsed = json.loads(cleaned)
            obj = LLMOutput.model_validate(parsed)
            
            # Additional logic
            if len(obj.root_causes) != 3:
                raise ValueError("root_causes must have exactly 3 items")
            if not (0.0 <= obj.confidence <= 1.0):
                raise ValueError("confidence must be between 0.0 and 1.0")
            if not obj.explanation or not obj.incident_summary:
                raise ValueError("explanation and incident_summary must be non-empty")
                
            return obj, retry_count, False
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Validation failed (attempt {attempt}): {e}")
            if attempt < max_retries:
                retry_count += 1
                prompt += "\n\nIMPORTANT: Your previous response was invalid. Return ONLY a raw JSON object. No markdown. No backticks. No extra text. Start your response with { and end with }."
                try:
                    current_raw, _ = model.infer(prompt)
                except Exception as model_err:
                    logger.error(f"Inference failed during retry: {model_err}")
                    break
            else:
                return None, retry_count, True

    return None, retry_count, True