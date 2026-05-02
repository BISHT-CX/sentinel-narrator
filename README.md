# SentinelNarrator

Real-time anomaly explanation engine: classical detection + Gemma 3 1B narration, deployed on GCP Cloud Run.

**Live Demo URL:** [DEPLOYED_URL]

**Model Declaration:** Gemma 3 1B Q4_K_M — llama-cpp-python — CPU-only inference — Tier 1 Absolute Garage

### The Architectural Insight
End-to-end LLMs struggle with precise mathematical anomaly detection, especially small 1B models which hallucinate or lose context. However, classical statistical methods (Z-Score sliding window + Isolation Forest) excel at detection with minimal overhead and high accuracy. 

By combining these two, we unlock the "wow gap". The classical layer accurately pinpoints anomalies, and the 1B model is given one specific job: receive a highly structured JSON context about the anomaly and output a human-readable explanation, ranked root causes, and an incident report. This plays exactly to the model's strengths (constrained text generation) while eliminating its weaknesses, allowing a tiny CPU-bound model to sound like a senior SRE.

### Setup — Local
1. Clone the repository.
2. Run `./scripts/download_model.sh` to download the GGUF model.
3. Run `docker-compose up --build`.
4. Open `http://localhost:8000` in your browser.

### Setup — GCP Cloud Run
1. Bake the model into the container (update Dockerfile to download the model during build, or host it in GCS).
2. Run `gcloud builds submit --config cloudbuild.yaml .` to build and push the image.
3. Deploy via Cloud Run with `gcloud run deploy sentinel-narrator --image gcr.io/$PROJECT_ID/sentinel-narrator --platform managed --region us-central1 --cpu 4 --memory 4Gi --timeout 300 --concurrency 10 --max-instances 3 --allow-unauthenticated`.
4. Ensure no GPU is requested.

### Engineering Techniques
- **Structured Prompts & Few-Shot Learning:** The prompt precisely constrains the LLM to output valid JSON only, guided by robust in-context examples.
- **Pydantic Output Validation:** Ensures the model's structural JSON output perfectly matches the expected schemas.
- **Retry & Prompt Rephrasing:** If the LLM generates malformed JSON, the system dynamically appends strong structural reinforcement rules and retries.
- **Context Injection:** Injecting sliding window data directly into the LLM context allows the 1B model to narrate complex metric drifts.

### Honest Known Failures
1. **Hallucinated Metric Names:** On occasion, the 1B model will inject metric concepts not strictly present in the JSON prompt.
2. **Overconfident Root Causes:** The model confidently attributes anomalies to non-existent complex architectural flaws.
3. **JSON Formatting Errors:** On longer outputs or edge cases, the model may occasionally forget to close JSON braces or escape quotes, requiring prompt retries.
4. **Concurrency Limits:** The model heavily struggles if asked to reason about more than 3 concurrent or cross-metric anomalies.

### Cost Breakdown
- **Inference Time:** ~3–8 seconds per anomaly on a 4 vCPU Cloud Run instance.
- **Estimated Cost:** ~₹0.80 per 1000 anomaly explanations on Cloud Run (based on execution time and compute tiers).

### Threat Model
Model output is treated as untrusted text. It flows only to: JSON parser → Pydantic validator → API response → frontend display. The model cannot trigger actions, access files, call external services, or influence infrastructure.
