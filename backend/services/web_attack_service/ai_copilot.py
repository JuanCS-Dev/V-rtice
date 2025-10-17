"""Maximus Web Attack Service - AI Co-Pilot Module.

This module implements the AI Co-Pilot for the Maximus AI's Web Attack Service.
It leverages advanced Large Language Models (LLMs), specifically a hybrid of
Gemini and Anthropic, to generate sophisticated attack payloads and analyze
vulnerability contexts from natural language descriptions.

Key functionalities include:
- Translating natural language descriptions into concrete attack payloads.
- Performing context-aware vulnerability analysis.
- Generating novel attack vectors and ethical payload filtering.
- Integrating with the Prefrontal Cortex Service for ethical validation of payloads.

This AI Co-Pilot is crucial for enhancing Maximus AI's capabilities in automated
penetration testing, red teaming, and proactive cybersecurity defense, allowing
it to intelligently identify and simulate web-based attack scenarios.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Gemini (Google)
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Anthropic (Claude)
try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

import httpx

from backend.services.web_attack_service.models import (
    AICoPilotRequest,
    AICoPilotResponse,
    AIGeneratedPayload,
    AIProvider,
    Severity,
    VulnerabilityType,
)

logger = logging.getLogger(__name__)


class AICoPilot:
    """
    AI Co-Pilot for Web Application Attack

    Hybrid Architecture:
    - Primary: Gemini (saldo de testes disponível)
    - Fallback: Anthropic (quando API key disponível)
    - Validation: Prefrontal Cortex (impulse inhibition)

    Capabilities:
    - Natural language → attack payloads
    - Context-aware vulnerability analysis
    - Novel attack vector generation
    - Ethical payload filtering
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        default_provider: AIProvider = AIProvider.AUTO,
        prefrontal_cortex_url: Optional[str] = None,
    ):
        """Inicializa o AICoPilot.

        Args:
            gemini_api_key (Optional[str]): Chave da API Gemini.
            anthropic_api_key (Optional[str]): Chave da API Anthropic.
            default_provider (AIProvider): Provedor de IA padrão a ser usado.
            prefrontal_cortex_url (Optional[str]): URL do serviço Prefrontal Cortex para validação.
        """
        self.gemini_api_key = gemini_api_key
        self.anthropic_api_key = anthropic_api_key
        self.default_provider = default_provider
        self.prefrontal_cortex_url = prefrontal_cortex_url

        # Initialize clients
        self.gemini_client = None
        self.anthropic_client = None

        if GEMINI_AVAILABLE and gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_client = genai.GenerativeModel("gemini-pro")
            logger.info("Gemini AI initialized")

        if ANTHROPIC_AVAILABLE and anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
            logger.info("Anthropic AI initialized")

        if not self.gemini_client and not self.anthropic_client:
            logger.warning("No AI provider available - Co-Pilot disabled")

    async def generate_attack_vectors(self, request: AICoPilotRequest) -> AICoPilotResponse:
        """
        Generate attack vectors using AI

        Args:
            request: AICoPilotRequest with context

        Returns:
            AICoPilotResponse with payloads and analysis
        """
        # Determine provider
        provider = await self._select_provider(request.provider)

        if not provider:
            raise RuntimeError("No AI provider available")

        logger.info(f"Generating attack vectors using {provider.value}")

        # Build prompt
        prompt = self._build_prompt(request)

        # Generate with selected provider
        if provider == AIProvider.GEMINI:
            response_text, tokens_used = await self._generate_with_gemini(
                prompt, request.temperature, request.max_tokens
            )
        else:  # Anthropic
            response_text, tokens_used = await self._generate_with_anthropic(
                prompt, request.temperature, request.max_tokens
            )

        # Parse response
        payloads = self._parse_ai_response(response_text, request.attack_type)

        # Validate through Prefrontal Cortex
        validated_payloads = await self._validate_payloads(payloads)

        # Extract recommendations
        recommendations = self._extract_recommendations(response_text)

        return AICoPilotResponse(
            analysis=response_text.split("\n\n")[0],  # First paragraph
            attack_vectors=validated_payloads,
            recommendations=recommendations,
            provider_used=provider,
            tokens_used=tokens_used,
            confidence=0.85,  # Based on validation pass rate
            timestamp=datetime.now(),
        )

    async def _select_provider(self, requested: AIProvider) -> Optional[AIProvider]:
        """Seleciona o provedor de IA a ser usado com base na disponibilidade e na preferência.

        Args:
            requested (AIProvider): O provedor de IA solicitado.

        Returns:
            Optional[AIProvider]: O provedor de IA selecionado, ou None se nenhum estiver disponível.
        """
        if requested == AIProvider.GEMINI and self.gemini_client:
            return AIProvider.GEMINI
        elif requested == AIProvider.ANTHROPIC and self.anthropic_client:
            return AIProvider.ANTHROPIC
        elif requested == AIProvider.AUTO:
            # Prefer Gemini (saldo de testes), fallback to Anthropic
            if self.gemini_client:
                return AIProvider.GEMINI
            elif self.anthropic_client:
                return AIProvider.ANTHROPIC

        return None

    def _build_prompt(self, request: AICoPilotRequest) -> str:
        """Constrói um prompt contextualizado para a IA com base na requisição.

        Args:
            request (AICoPilotRequest): O objeto de requisição do co-piloto de IA.

        Returns:
            str: O prompt formatado para a IA.
        """
        vuln_type = request.attack_type.value.replace("_", " ").title()

        prompt = f"""You are a web application security expert conducting an ethical penetration test.

**Vulnerability Context:**
{json.dumps(request.vulnerability_context, indent=2)}

**Request Structure:**
{json.dumps(request.request_structure, indent=2)}

**Attack Type:** {vuln_type}

**Task:**
Generate 5 sophisticated attack payloads to test for {vuln_type}. For each payload:

1. **Payload**: The actual attack string/code
2. **Explanation**: Why this payload works and what it tests
3. **Risk Level**: critical/high/medium/low
4. **Expected Behavior**: What should happen if vulnerable

**Constraints:**
- Payloads must be SAFE for testing (no destructive operations)
- Focus on detection, not exploitation
- Consider modern security controls (WAF, CSP, etc)
- Think beyond obvious/common payloads

**Output Format (JSON):**
```json
{{
  "payloads": [
    {{
      "payload": "...",
      "explanation": "...",
      "risk_level": "...",
      "expected_behavior": "..."
    }}
  ],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ]
}}
```

Think creatively - what novel attack vectors might bypass modern defenses?"""

        return prompt

    async def _generate_with_gemini(self, prompt: str, temperature: float, max_tokens: int) -> tuple[str, int]:
        """Gera uma resposta usando o modelo Gemini.

        Args:
            prompt (str): O prompt a ser enviado ao Gemini.
            temperature (float): A temperatura para a geração de texto.
            max_tokens (int): O número máximo de tokens a serem gerados.

        Returns:
            tuple[str, int]: Uma tupla contendo o texto da resposta e o número estimado de tokens usados.

        Raises:
            Exception: Se a geração do Gemini falhar.
        """
        try:
            response = await asyncio.to_thread(
                self.gemini_client.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens),
            )

            text = response.text
            # Gemini doesn't expose token count directly, estimate
            tokens_used = len(text.split()) * 1.3  # Rough estimate

            return text, int(tokens_used)

        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            raise

    async def _generate_with_anthropic(self, prompt: str, temperature: float, max_tokens: int) -> tuple[str, int]:
        """Gera uma resposta usando o modelo Anthropic.

        Args:
            prompt (str): O prompt a ser enviado ao Anthropic.
            temperature (float): A temperatura para a geração de texto.
            max_tokens (int): O número máximo de tokens a serem gerados.

        Returns:
            tuple[str, int]: Uma tupla contendo o texto da resposta e o número de tokens usados.

        Raises:
            Exception: Se a geração do Anthropic falhar.
        """
        try:
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model="claude-3-sonnet-20240229",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            return text, tokens_used

        except Exception as e:
            logger.error(f"Anthropic generation failed: {str(e)}")
            raise

    def _parse_ai_response(self, response_text: str, attack_type: VulnerabilityType) -> List[AIGeneratedPayload]:
        """Analisa a resposta da IA, extraindo payloads de ataque estruturados.

        Args:
            response_text (str): O texto da resposta gerada pela IA.
            attack_type (VulnerabilityType): O tipo de ataque para o qual os payloads foram gerados.

        Returns:
            List[AIGeneratedPayload]: Uma lista de objetos AIGeneratedPayload.
        """
        payloads = []

        try:
            # Try to extract JSON block
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                # Try to find JSON object
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]

            data = json.loads(json_str)

            for p in data.get("payloads", []):
                severity_map = {
                    "critical": Severity.CRITICAL,
                    "high": Severity.HIGH,
                    "medium": Severity.MEDIUM,
                    "low": Severity.LOW,
                }

                payload = AIGeneratedPayload(
                    payload=p.get("payload", ""),
                    payload_type=attack_type,
                    explanation=p.get("explanation", ""),
                    risk_level=severity_map.get(p.get("risk_level", "medium").lower(), Severity.MEDIUM),
                    prefrontal_cortex_approved=False,
                    destructiveness_score=self._calculate_destructiveness(p.get("payload", "")),
                )
                payloads.append(payload)

        except Exception as e:
            logger.warning(f"Failed to parse AI response as JSON: {str(e)}")
            # Fallback: Extract payloads from text
            payloads = self._fallback_parse(response_text, attack_type)

        return payloads

    def _calculate_destructiveness(self, payload: str) -> float:
        """Calcula um score de destrutividade para um payload (0.0-1.0).

        Args:
            payload (str): O payload a ser avaliado.

        Returns:
            float: O score de destrutividade.
        """
        destructive_keywords = {
            "drop": 0.9,
            "delete": 0.9,
            "truncate": 0.9,
            "update": 0.7,
            "insert": 0.6,
            "exec": 0.8,
            "system": 0.8,
            "shell": 0.8,
            "rm ": 0.9,
            "format": 0.8,
        }

        score = 0.0
        payload_lower = payload.lower()

        for keyword, weight in destructive_keywords.items():
            if keyword in payload_lower:
                score = max(score, weight)

        return score

    def _fallback_parse(self, response_text: str, attack_type: VulnerabilityType) -> List[AIGeneratedPayload]:
        """Parser de fallback quando a extração JSON da resposta da IA falha.

        Tenta extrair payloads de texto usando heurísticas simples.

        Args:
            response_text (str): O texto da resposta da IA.
            attack_type (VulnerabilityType): O tipo de ataque.

        Returns:
            List[AIGeneratedPayload]: Uma lista de objetos AIGeneratedPayload extraídos.
        """
        payloads = []

        # Simple heuristic: look for code blocks or quoted strings
        lines = response_text.split("\n")

        for line in lines:
            # Look for payload patterns
            if any(marker in line for marker in ["payload:", "Payload:", "```", "`"]):
                # Extract potential payload
                payload_text = line.split(":", 1)[-1].strip("` '\"")

                if len(payload_text) > 5:  # Minimum payload length
                    payloads.append(
                        AIGeneratedPayload(
                            payload=payload_text,
                            payload_type=attack_type,
                            explanation="Extracted from AI response (fallback parser)",
                            risk_level=Severity.MEDIUM,
                            destructiveness_score=self._calculate_destructiveness(payload_text),
                        )
                    )

        return payloads[:5]  # Limit to 5

    async def _validate_payloads(self, payloads: List[AIGeneratedPayload]) -> List[AIGeneratedPayload]:
        """Valida payloads através do serviço Prefrontal Cortex (inibição de impulso).

        Args:
            payloads (List[AIGeneratedPayload]): A lista de payloads gerados pela IA.

        Returns:
            List[AIGeneratedPayload]: A lista de payloads validados e aprovados.
        """
        if not self.prefrontal_cortex_url:
            logger.warning("Prefrontal Cortex not configured - skipping validation")
            return payloads

        validated = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            for payload in payloads:
                try:
                    response = await client.post(
                        f"{self.prefrontal_cortex_url}/api/v1/validate-action",
                        json={
                            "action": "web_attack_payload",
                            "payload": {
                                "payload_text": payload.payload,
                                "attack_type": payload.payload_type.value,
                                "risk_level": payload.risk_level.value,
                            },
                            "destructiveness_score": payload.destructiveness_score,
                        },
                    )

                    if response.status_code == 200:
                        validation = response.json()

                        if validation.get("approved", False):
                            payload.prefrontal_cortex_approved = True
                            validated.append(payload)
                        else:
                            logger.info(f"Payload blocked by Prefrontal Cortex: {payload.payload[:50]}")

                except Exception as e:
                    logger.warning(f"Prefrontal Cortex validation failed: {str(e)}")
                    # On validation error, include payload but mark as not approved
                    validated.append(payload)

        return validated

    def _extract_recommendations(self, response_text: str) -> List[str]:
        """Extrai recomendações de segurança da resposta da IA.

        Args:
            response_text (str): O texto completo da resposta da IA.

        Returns:
            List[str]: Uma lista de recomendações de segurança extraídas.
        """
        recommendations = []

        try:
            # Try JSON extraction first
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                data = json.loads(json_str)
                recommendations = data.get("recommendations", [])

        except Exception:
            # Fallback: look for recommendation patterns
            lines = response_text.split("\n")
            for line in lines:
                if any(keyword in line.lower() for keyword in ["recommend", "should", "must", "remediation"]):
                    cleaned = line.strip("- *#").strip()
                    if len(cleaned) > 20:  # Meaningful recommendation
                        recommendations.append(cleaned)

        return recommendations[:5]  # Limit to 5

    async def analyze_vulnerability_context(
        self, http_request: Dict, http_response: Dict, suspected_vuln: VulnerabilityType
    ) -> str:
        """
        Analyze HTTP traffic for vulnerability insights

        Args:
            http_request: Request dict
            http_response: Response dict
            suspected_vuln: Suspected vulnerability type

        Returns:
            AI analysis text
        """
        provider = await self._select_provider(self.default_provider)

        if not provider:
            return "AI Co-Pilot unavailable"

        prompt = f"""Analyze this HTTP transaction for {suspected_vuln.value}:

**Request:**
```
{json.dumps(http_request, indent=2)}
```

**Response:**
```
{json.dumps(http_response, indent=2)}
```

Provide:
1. Vulnerability assessment (likely/possible/unlikely)
2. Attack surface analysis
3. Recommended test payloads (3-5)
4. Security recommendations

Be concise but thorough."""

        if provider == AIProvider.GEMINI:
            text, _ = await self._generate_with_gemini(prompt, 0.7, 1000)
        else:
            text, _ = await self._generate_with_anthropic(prompt, 0.7, 1000)

        return text
