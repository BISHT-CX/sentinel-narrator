from .schemas import AnomalyEvent

def build_prompt(event: AnomalyEvent) -> str:
    # Minimal schema - only what a 1B model can reliably produce
    prompt = f"""You are an SRE. A metric anomaly was detected. Reply with ONLY a JSON object, nothing else. No markdown. No explanation. Start with {{ and end with }}.

JSON format:
{{"explanation":"one sentence","cause1":"most likely cause","cause2":"second cause","cause3":"third cause","summary":"one paragraph for slack alert","confidence":0.8}}

Example input:
metric=api_latency_ms value=487.3 expected=110-150 z_score=8.2 severity=critical

Example output:
{{"explanation":"API latency spiked to 487ms which is 4x above normal range.","cause1":"Database connection pool exhausted","cause2":"Upstream service timeout cascade","cause3":"Traffic spike without autoscaling","summary":"CRITICAL: api_latency_ms hit 487.3ms vs normal 110-150ms. Investigate DB connections immediately.","confidence":0.85}}

Now respond for this anomaly:
metric={event.metric_name} value={event.value:.2f} expected={event.expected_min:.2f}-{event.expected_max:.2f} z_score={event.z_score:.2f} severity={event.severity.value} recent_values={",".join([f"{v:.1f}" for v in event.context_window[-5:]])}

JSON:"""
    return prompt
