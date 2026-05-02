import asyncio
import random
import math
import logging
from datetime import datetime
import httpx
from .config import config

logger = logging.getLogger(__name__)

# Metric bases
METRICS = {
    "api_latency_ms": {"base": 120.0, "type": "sine", "period": 300, "amp": 15},
    "error_rate_pct": {"base": 0.5, "type": "flat", "noise": 0.1},
    "cpu_utilization_pct": {"base": 45.0, "type": "drift", "rate": 0.05},
    "memory_used_gb": {"base": 6.2, "type": "sawtooth", "max": 8.0, "rate": 0.01},
    "requests_per_second": {"base": 850.0, "type": "sine", "period": 120, "amp": 100},
}

async def generate_metrics():
    tick = 0
    while True:
        tick += 1
        points = []
        now = datetime.utcnow()
        
        for name, params in METRICS.items():
            val = params["base"]
            if params["type"] == "sine":
                val += math.sin(tick * 2 * math.pi / params["period"]) * params["amp"]
            elif params["type"] == "drift":
                val += tick * params.get("rate", 0)
            elif params["type"] == "sawtooth":
                val += (tick * params.get("rate", 0)) % (params.get("max", 10.0) - params["base"])
            elif params["type"] == "flat":
                val += random.uniform(-params.get("noise", 0), params.get("noise", 0))
                
            # Add base noise
            val += random.uniform(-val * 0.02, val * 0.02)
            
            # Anomaly injection every 30-60 ticks
            if random.randint(1, int(45 / config.METRICS_INTERVAL_SECONDS)) == 1:
                anomaly_type = random.choice(["spike", "drop", "sustained_drift", "noise_burst"])
                logger.info(f"Injecting {anomaly_type} into {name}")
                if anomaly_type == "spike":
                    val *= random.uniform(3.5, 5.0)
                elif anomaly_type == "drop":
                    val *= random.uniform(0.1, 0.2)
                elif anomaly_type == "sustained_drift":
                    METRICS[name]["base"] += val * 0.5  # Permanent drift shift
                elif anomaly_type == "noise_burst":
                    val += val * random.uniform(0.5, 1.0) # Simulate 1 point, let loop continue normal noise
            
            points.append({
                "metric_name": name,
                "value": max(0.0, val),
                "timestamp": now.isoformat()
            })
            
        async with httpx.AsyncClient() as client:
            for point in points:
                try:
                    await client.post("http://127.0.0.1:8000/ingest", json=point)
                except httpx.RequestError as e:
                    pass

        await asyncio.sleep(config.METRICS_INTERVAL_SECONDS)