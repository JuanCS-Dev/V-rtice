import threading
import google.generativeai as genai
from google.generativeai.generative_models import GenerativeModel
from typing import Dict

from config import settings

class LLMClientFactory:
    _instance = None
    _lock = threading.Lock()
    _clients: Dict[str, GenerativeModel] = {}

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LLMClientFactory, cls).__new__(cls)
                genai.configure(api_key=settings.GEMINI_API_KEY)
        return cls._instance

    def get_client(self, model_name: str) -> GenerativeModel:
        with self._lock:
            if model_name not in self._clients:
                self._clients[model_name] = genai.GenerativeModel(model_name)
            return self._clients[model_name]
