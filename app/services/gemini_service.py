import json
from typing import Any

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings


ALLOWED_CATEGORIES = {
    "Food",
    "Shopping",
    "Travel",
    "Transport",
    "Utilities",
    "Cash Withdrawal",
    "Entertainment",
    "Other",
}
ALLOWED_RISK_LEVELS = {"low", "medium", "high"}


class GeminiUnavailableError(RuntimeError):
    pass


class GeminiService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = None
        if self.settings.gemini_api_key:
            genai.configure(api_key=self.settings.gemini_api_key)
            self.model = genai.GenerativeModel(self.settings.gemini_model)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def classify_categories(
        self,
        transactions: list[dict[str, str | None]],
    ) -> tuple[dict[str, str], str]:
        if not transactions:
            return {}, "{}"

        payload = {
            "allowed_categories": sorted(ALLOWED_CATEGORIES),
            "transactions": transactions,
            "response_schema": {
                "categories": [{"id": "transaction id", "category": "Food"}]
            },
        }
        response_text = self._generate_json(
            "Classify each transaction into exactly one allowed category. "
            "Return only valid JSON.",
            payload,
        )
        parsed = self._parse_json(response_text)

        categories: dict[str, str] = {}
        for item in parsed.get("categories", []):
            transaction_id = str(item.get("id", ""))
            category = item.get("category")
            categories[transaction_id] = (
                category if category in ALLOWED_CATEGORIES else "Other"
            )

        return categories, response_text

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def generate_summary_narrative(
        self,
        aggregates: dict[str, Any],
    ) -> tuple[str | None, str | None]:
        response_text = self._generate_json(
            "Generate a concise spending narrative and risk level. "
            "Return only JSON with narrative and risk_level.",
            {
                "aggregates": aggregates,
                "allowed_risk_levels": sorted(ALLOWED_RISK_LEVELS),
                "response_schema": {"narrative": "...", "risk_level": "low"},
            },
        )
        parsed = self._parse_json(response_text)
        risk_level = parsed.get("risk_level")
        if risk_level not in ALLOWED_RISK_LEVELS:
            risk_level = "medium"
        return parsed.get("narrative"), risk_level

    def _generate_json(self, instruction: str, payload: dict[str, Any]) -> str:
        if self.model is None:
            raise GeminiUnavailableError("GEMINI_API_KEY is not configured.")

        response = self.model.generate_content(
            [
                instruction,
                json.dumps(payload, default=str),
            ],
            generation_config={"response_mime_type": "application/json"},
        )
        return response.text

    def _parse_json(self, response_text: str) -> dict[str, Any]:
        return json.loads(response_text)
