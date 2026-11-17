import time
import google.generativeai as genai
from app.config import settings
from app.utils.logger import logger

class LLMService:
    def __init__(self):
        self.available_models = []
        self.model_name = None
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY is not set in environment variables.")
        else:
            genai.configure(api_key=settings.gemini_api_key)
            self.available_models = self._detect_available_models()
            self.model_name = self.available_models[0] if self.available_models else "gemini-2.5-pro"

    def _detect_available_models(self) -> list[str]:
        try:
            raw_models = [
                m.name.replace("models/", "")
                for m in genai.list_models()
                if "generateContent" in getattr(m, "supported_generation_methods", [])
                and "embedding" not in m.name.lower()
                and "image" not in m.name.lower()
            ]
            priority_keywords = ["flash-lite", "flash", "pro"]
            ordered = []
            for kw in priority_keywords:
                for m in raw_models:
                    if kw in m and m not in ordered:
                        ordered.append(m)
            for m in raw_models:
                if m not in ordered:
                    ordered.append(m)
            logger.info(f"Detected active Gemini fallback chain: {ordered[:5]}")
            return ordered if ordered else ["gemini-2.5-pro"]
        except Exception as e:
            logger.error(f"Could not list Gemini models: {str(e)}")
            return ["gemini-2.5-pro"]

    def generate_text(self, prompt: str, system_instruction: str = None, temperature: float = 0.3) -> str:
        if not self.available_models:
            self.available_models = self._detect_available_models()

        last_error = None
        # Try across available models if one hits daily free-tier quota (429)
        for candidate_model in self.available_models[:5]:
            try:
                generation_config = genai.types.GenerationConfig(temperature=temperature)
                model = genai.GenerativeModel(
                    model_name=candidate_model,
                    system_instruction=system_instruction,
                    generation_config=generation_config,
                )
                response = model.generate_content(prompt)
                self.model_name = candidate_model
                return response.text
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                    logger.warning(f"Quota/rate limit on {candidate_model}, switching to next Gemini model...")
                    time.sleep(2)
                    continue
                logger.error(f"Error generating text with {candidate_model}: {err_str}")
                raise e

        raise last_error

llm_service = LLMService()