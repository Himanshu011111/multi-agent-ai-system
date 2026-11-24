import time
import google.generativeai as genai
from app.config import settings
from app.utils.logger import logger


class LLMService:
    # Class-level cache so list_models() runs only ONCE across all agents
    _cached_models: list[str] = []
    _configured: bool = False

    def __init__(self):
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY is not set in environment variables.")
            self.available_models = ["gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-2.5-flash"]
            self.model_name = self.available_models[0]
            return

        if not LLMService._configured:
            genai.configure(api_key=settings.gemini_api_key)
            LLMService._configured = True

        if not LLMService._cached_models:
            LLMService._cached_models = self._detect_available_models()

        self.available_models = LLMService._cached_models
        self.model_name = self.available_models[0]

    def _detect_available_models(self) -> list[str]:
        preferred_fast_order = [
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.5-flash",
        ]
        excluded_keywords = (
            "embedding", "image", "imagen", "veo", "tts",
            "audio", "thinking", "aqa", "bison", "gecko", "vision",
        )
        try:
            raw_models = [
                m.name.replace("models/", "")
                for m in genai.list_models()
                if "generateContent" in getattr(m, "supported_generation_methods", [])
                and not any(bad in m.name.lower() for bad in excluded_keywords)
            ]

            ordered: list[str] = []
            # 1. Exact fastest stable models first
            for exact in preferred_fast_order:
                if exact in raw_models and exact not in ordered:
                    ordered.append(exact)

            # 2. Other stable flash-lite / flash models (skip preview/exp unless needed)
            for kw in ("flash-lite", "flash"):
                for m in raw_models:
                    if kw in m and "exp" not in m and "preview" not in m and m not in ordered:
                        ordered.append(m)

            # 3. Remaining fallback models
            for m in raw_models:
                if m not in ordered:
                    ordered.append(m)

            logger.info(f"Ultra-Fast Gemini chain ready: {ordered[:5]}")
            return ordered if ordered else preferred_fast_order
        except Exception as e:
            logger.error(f"Could not list Gemini models: {str(e)}")
            return preferred_fast_order

    def _demote_model(self, model_name: str):
        """Move a rate-limited model to the back so subsequent agents don't hit 429 again."""
        if model_name in LLMService._cached_models:
            LLMService._cached_models.remove(model_name)
            LLMService._cached_models.append(model_name)
            self.available_models = LLMService._cached_models

    def generate_text(
        self,
        prompt: str,
        system_instruction: str = None,
        temperature: float = 0.3,
        max_output_tokens: int = 1024,
    ) -> str:
        if not self.available_models:
            LLMService._cached_models = self._detect_available_models()
            self.available_models = LLMService._cached_models

        last_error = None
        candidates = list(self.available_models[:5])

        for candidate_model in candidates:
            try:
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                )
                model = genai.GenerativeModel(
                    model_name=candidate_model,
                    system_instruction=system_instruction,
                    generation_config=generation_config,
                )
                response = model.generate_content(
                    prompt,
                    request_options={"timeout": 30},
                )
                self.model_name = candidate_model
                return (response.text or "").strip()
            except Exception as e:
                last_error = e
                err_str = str(e)
                if (
                    "429" in err_str
                    or "quota" in err_str.lower()
                    or "rate" in err_str.lower()
                    or "404" in err_str
                ):
                    logger.warning(f"Skipping {candidate_model} (quota/unavailable), switching instantly...")
                    self._demote_model(candidate_model)
                    time.sleep(0.2)
                    continue
                logger.error(f"Error generating text with {candidate_model}: {err_str}")
                raise e

        raise last_error


llm_service = LLMService()