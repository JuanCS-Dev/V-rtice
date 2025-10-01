import json
from typing import Dict

from google.generativeai.generative_models import GenerativeModel, GenerationConfig
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from models import SinespAnalysisReport
from prompt_templates import SINESP_ANALYSIS_PROMPT_TEMPLATE

class IntelligenceAgent:
    """
    The agent responsible for synthesizing factual data into an intelligence report.
    """
    def __init__(self, llm_client: GenerativeModel):
        self._llm_client = llm_client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=(retry_if_exception_type(ValidationError) | retry_if_exception_type(json.JSONDecodeError))
    )
    async def analyze(self, facts: Dict) -> SinespAnalysisReport:
        """
        Analyzes the given facts and returns a structured intelligence report.

        This method is resilient, automatically retrying on parsing or validation errors.
        """
        prompt = SINESP_ANALYSIS_PROMPT_TEMPLATE.format(facts=json.dumps(facts, indent=2))

        response = await self._llm_client.generate_content_async(
            prompt,
            generation_config=GenerationConfig(response_mime_type="application/json")
        )

        # Validate the response using the Pydantic model
        report = SinespAnalysisReport.model_validate_json(response.text)

        return report
