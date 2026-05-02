from .schemas import AnomalyEvent

def build_prompt(event: AnomalyEvent) -> str:
    prompt = f"""You are a senior site reliability engineer. Respond ONLY with a valid JSON object. No markdown, no explanation outside the JSON, no code fences.

Output schema:
{{
  "explanation": "1-2 sentence plain English explanation of what happened",
  "root_causes": [
    {{"cause": "string", "likelihood": "high"}},
    {{"cause": "string", "likelihood": "medium"}},
    {{"cause": "string", "likelihood": "low"}}
  ],
  "incident_summary": "1 paragraph suitable for a Slack alert",
  "confidence": 0.85
}}

Example 1:
Anomaly: metric=api_latency_ms, value=487.3, expected=110-150, z_score=8.2, severity=critical
Response:
{{"explanation": "API latency spiked to 487ms, nearly 4x the normal range, indicating a severe downstream bottleneck.", "root_causes": [{{"cause": "Database connection pool exhaustion", "likelihood": "high"}}, {{"cause": "Upstream dependency timeout cascade", "likelihood": "medium"}}, {{"cause": "Increased traffic load without scaling", "likelihood": "low"}}], "incident_summary": "CRITICAL: api_latency_ms spiked to 487.3ms at {event.timestamp.strftime('%H:%M:%S')}. Normal range is 110-150ms. Immediate investigation of database connections recommended.", "confidence": 0.88}}

Example 2:
Anomaly: metric=error_rate_pct, value=12.4, expected=0.2-0.8, z_score=6.1, severity=high
Response:
{{"explanation": "Error rate jumped to 12.4%, roughly 20x above baseline, suggesting a deployment issue or dependency failure.", "root_causes": [{{"cause": "Recent bad deployment introducing regressions", "likelihood": "high"}}, {{"cause": "Third-party API returning 5xx errors", "likelihood": "medium"}}, {{"cause": "Memory leak causing request handler crashes", "likelihood": "low"}}], "incident_summary": "HIGH: error_rate_pct is at 12.4%, far above normal 0.2-0.8%. Review recent deployments and check third-party integrations immediately.", "confidence": 0.82}}

Now respond with the JSON object for this anomaly:
metric={event.metric_name}
timestamp={event.timestamp.isoformat()}
value={event.value:.4f}
expected_range=[{event.expected_min:.4f}, {event.expected_max:.4f}]
z_score={event.z_score:.4f}
severity={event.severity.value}
context_window={", ".join([f"{v:.2f}" for v in event.context_window])}
detection_method={event.detection_method}"""

    return prompt
