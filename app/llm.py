import httpx
import time
import logging
import re

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://172.17.0.1:11434/api/generate"
MODEL_NAME = "gemma3:1b"

class GemmaModel:
    def __init__(self):
        self._loaded = True

    @property
    def is_loaded(self):
        return self._loaded

    def load(self):
        pass

    def infer(self, prompt: str, timeout: int = 30):
        start = time.time()
        try:
            response = httpx.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 400}
                },
                timeout=timeout
            )
            response.raise_for_status()
            text = response.json()["response"]
            text = re.sub(r"```json\n?", "", text)
            text = re.sub(r"```\n?", "", text)
            elapsed_ms = int((time.time() - start) * 1000)
            logger.info(f"Inference took {elapsed_ms}ms")
            return text.strip(), elapsed_ms
        except Exception as e:
            raise RuntimeError(f"Ollama inference failed: {e}")

gemma_model = GemmaModel()

llm = gemma_model
