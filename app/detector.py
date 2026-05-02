from collections import deque
import numpy as np
from sklearn.ensemble import IsolationForest
import time
from .config import config
from .schemas import MetricPoint, AnomalyEvent, Severity

class SlidingWindowDetector:
    def __init__(self):
        self.windows = {}
        self.models = {}
        self.last_anomaly_time = {}

    def process(self, point: MetricPoint) -> AnomalyEvent | None:
        name = point.metric_name
        if name not in self.windows:
            self.windows[name] = deque(maxlen=config.WINDOW_SIZE)
            self.models[name] = IsolationForest(contamination=0.05, random_state=42)
            
        window = self.windows[name]
        window.append(point.value)
        
        if len(window) < 20:
            return None
            
        # Z-score detection
        data = np.array(window)
        mean = np.mean(data[:-1]) if len(data) > 1 else data[0]
        std = np.std(data[:-1]) if len(data) > 1 else 1e-5
        if std == 0:
            std = 1e-5
            
        z_score = (point.value - mean) / std
        
        # Periodically retrain Isolation Forest
        if len(window) == config.WINDOW_SIZE and int(time.time()) % 10 == 0:
            self.models[name].fit(data.reshape(-1, 1))
            
        is_anomaly = abs(z_score) > config.ANOMALY_THRESHOLD_ZSCORE
        
        if is_anomaly:
            now = time.time()
            if name in self.last_anomaly_time and (now - self.last_anomaly_time[name]) < 30:
                return None  # Deduplicate
                
            self.last_anomaly_time[name] = now
            
            abs_z = abs(z_score)
            if abs_z > 7:
                severity = Severity.CRITICAL
            elif abs_z > 5:
                severity = Severity.HIGH
            elif abs_z > 4:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW
                
            return AnomalyEvent(
                metric_name=name,
                timestamp=point.timestamp,
                value=point.value,
                expected_min=mean - (std * config.ANOMALY_THRESHOLD_ZSCORE),
                expected_max=mean + (std * config.ANOMALY_THRESHOLD_ZSCORE),
                z_score=z_score,
                severity=severity,
                context_window=list(window)[-10:],
                detection_method="z-score"
            )
            
        return None

detector = SlidingWindowDetector()