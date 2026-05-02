from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MODEL_PATH: str = "./models/gemma-3-1b-it-q4_k_m.gguf"
    N_CTX: int = 1024
    MAX_TOKENS: int = 400
    TEMPERATURE: float = 0.1
    INFERENCE_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    ANOMALY_THRESHOLD_ZSCORE: float = 3.0
    WINDOW_SIZE: int = 100
    METRICS_INTERVAL_SECONDS: float = 1.0
    MAX_STORED_ANOMALIES: int = 200
    RATE_LIMIT_PER_MINUTE: int = 120

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

config = Settings()