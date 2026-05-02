import asyncio
import time
from collections import deque
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .config import config
from .schemas import MetricPoint, AnomalyExplanation
from .generator import generate_metrics
from .detector import detector
from .llm import llm
from .prompt_builder import build_prompt
from .validator import validate_llm_output

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="SentinelNarrator")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

anomalies_store = deque(maxlen=config.MAX_STORED_ANOMALIES)
store_lock = asyncio.Lock()
subscribers = []
generator_task = None

stats = {
    "total_anomalies": 0,
    "total_inference_ms": 0,
    "total_retries": 0,
    "fallback_count": 0,
    "start_time": time.time()
}

@app.on_event("startup")
async def startup_event():
    start_load = time.time()
    llm.load()
    print(f"Model loaded in {time.time() - start_load:.2f}s")
    global generator_task
    generator_task = asyncio.create_task(generate_metrics())

@app.on_event("shutdown")
async def shutdown_event():
    if generator_task:
        generator_task.cancel()

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": llm.is_loaded,
        "anomalies_detected": stats["total_anomalies"],
        "uptime_seconds": time.time() - stats["start_time"]
    }

@app.post("/ingest")
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def ingest(point: MetricPoint, request: Request):
    event = detector.process(point)
    if event:
        prompt = build_prompt(event)
        raw_output = ""
        inference_ms = 0
        
        if llm.is_loaded:
            try:
                raw_output, inference_ms = llm.infer(prompt)
            except Exception as e:
                print(f"Inference error: {e}")
                
        llm_output, retry_count, fallback_used = validate_llm_output(
            raw_output, event, llm, config.MAX_RETRIES
        )
        
        explanation = AnomalyExplanation(
            event=event,
            llm_output=llm_output,
            inference_time_ms=inference_ms,
            retry_count=retry_count,
            fallback_used=fallback_used
        )
        
        async with store_lock:
            anomalies_store.appendleft(explanation)
            stats["total_anomalies"] += 1
            stats["total_inference_ms"] += inference_ms
            stats["total_retries"] += retry_count
            if fallback_used:
                stats["fallback_count"] += 1
                
        for q in subscribers:
            await q.put(explanation.model_dump_json())
            
        return {"status": "anomaly_detected"}
        
    return {"status": "ok"}

@app.get("/anomalies")
async def get_anomalies(limit: int = 50):
    async with store_lock:
        data = list(anomalies_store)[:limit]
    return data

@app.get("/anomalies/{id}")
async def get_anomaly(id: str):
    async with store_lock:
        for a in anomalies_store:
            if a.event.id == id:
                return a
    raise HTTPException(status_code=404, detail="Anomaly not found")

@app.get("/stats")
def get_stats():
    total = max(1, stats["total_anomalies"])
    return {
        "total_anomalies": stats["total_anomalies"],
        "avg_inference_ms": stats["total_inference_ms"] / total,
        "avg_retry_count": stats["total_retries"] / total,
        "fallback_rate_pct": (stats["fallback_count"] / total) * 100,
        "model_path": config.MODEL_PATH,
        "tier": "Tier 1 — Absolute Garage"
    }

@app.get("/stream")
async def stream():
    q = asyncio.Queue()
    subscribers.append(q)
    
    async def event_generator():
        try:
            while True:
                data = await q.get()
                yield {"data": data}
        except asyncio.CancelledError:
            subscribers.remove(q)
            
    return EventSourceResponse(event_generator())

from fastapi.responses import FileResponse

@app.get("/")
async def serve_frontend():
    return FileResponse("/app/frontend/index.html")

