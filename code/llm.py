from __future__ import annotations
import logging
from typing import Optional

try:
    from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
    import torch
except Exception:  # pragma: no cover
    AutoModelForCausalLM = None
    AutoModelForSeq2SeqLM = None
    AutoTokenizer = None
    pipeline = None
    torch = None


class LocalLLM:
    def __init__(self, model_name_or_path: str, device: str = "cpu") -> None:
        if AutoTokenizer is None or pipeline is None:
            raise ImportError("transformers is required for local LLM support")
        self.model_name_or_path = model_name_or_path
        self.device = device
        self._generator = None

    def _init_generator(self):
        if self._generator is not None:
            return
        try:
            self._generator = pipeline(
                "text-generation",
                model=self.model_name_or_path,
                tokenizer=self.model_name_or_path,
                device=0 if self.device == "cuda" else -1,
            )
        except Exception as exc:
            logging.warning("Failed to initialize local LLM pipeline: %s", exc)
            self._generator = None

    def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        self._init_generator()
        if self._generator is None:
            raise RuntimeError("Local LLM pipeline is unavailable")
        outputs = self._generator(prompt, max_new_tokens=max_new_tokens, do_sample=False)
        if outputs and isinstance(outputs, list):
            return str(outputs[0].get("generated_text", "")).strip()
        return ""

    def available(self) -> bool:
        if AutoTokenizer is None or pipeline is None:
            return False
        try:
            self._init_generator()
            return self._generator is not None
        except Exception:
            return False
