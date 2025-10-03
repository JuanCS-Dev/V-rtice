"""
Suggestion Generator - MAXIMUS Self-Improvement Brain
======================================================

Usa LLM para analisar o próprio código do MAXIMUS e gerar sugestões de melhorias.

Capacidades:
- Análise de código via LLM (Google Gemini)
- Categorização de sugestões (security, performance, features, refactoring)
- Scoring de confiança e impacto
- Geração de planos de implementação
- Priorização inteligente
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from code_scanner import CodeScanner, CodeFile

logger = logging.getLogger(__name__)


class SuggestionCategory(str, Enum):
    """Categorias de sugestões"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    FEATURES = "features"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


class SuggestionPriority(str, Enum):
    """Prioridade da sugestão"""
    CRITICAL = "critical"  # Implementar imediatamente
    HIGH = "high"          # Implementar em dias
    MEDIUM = "medium"      # Implementar em semanas
    LOW = "low"            # Backlog


@dataclass
class Suggestion:
    """Representa uma sugestão de melhoria"""
    suggestion_id: str
    timestamp: datetime
    category: SuggestionCategory
    priority: SuggestionPriority
    title: str
    description: str
    affected_files: List[str]
    confidence_score: float  # 0-1
    impact_score: float      # 0-1
    effort_estimate_hours: int
    implementation_steps: List[str]
    code_example: Optional[str] = None
    references: List[str] = None
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['category'] = self.category.value
        data['priority'] = self.priority.value
        return data


class SuggestionGenerator:
    """
    Gera sugestões de melhoria usando LLM

    Features:
    - Análise contextual de código
    - Múltiplas categorias de sugestão
    - Scoring automático
    - Planos de implementação detalhados
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Args:
            gemini_api_key: Google Gemini API key (se None, usa env var)
        """
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.suggestions_generated: List[Suggestion] = []
        self.scanner = CodeScanner()

    def generate_suggestions(
        self,
        focus_category: Optional[SuggestionCategory] = None,
        max_suggestions: int = 10,
        min_confidence: float = 0.7
    ) -> List[Suggestion]:
        """
        Gera sugestões de melhoria para o codebase MAXIMUS

        Args:
            focus_category: Categoria específica (None = todas)
            max_suggestions: Máximo de sugestões a gerar
            min_confidence: Confiança mínima (0-1)

        Returns:
            Lista de sugestões priorizadas
        """
        logger.info("🧠 Iniciando geração de sugestões...")

        # 1. Escaneia codebase
        code_files = self.scanner.scan_maximus_codebase()
        logger.info(f"📂 {len(code_files)} arquivos escaneados")

        # 2. Constrói contexto para LLM
        context = self.scanner.build_context_for_llm(
            max_files=15,
            max_total_chars=80000,
            prioritize_core=True
        )

        # 3. Gera sugestões via LLM
        suggestions = self._analyze_with_llm(
            context=context,
            focus_category=focus_category,
            max_suggestions=max_suggestions
        )

        # 4. Filtra por confiança
        filtered_suggestions = [
            s for s in suggestions
            if s.confidence_score >= min_confidence
        ]

        # 5. Prioriza sugestões
        prioritized = self._prioritize_suggestions(filtered_suggestions)

        self.suggestions_generated.extend(prioritized)

        logger.info(
            f"✅ {len(prioritized)} sugestões geradas | "
            f"Avg confidence: {sum(s.confidence_score for s in prioritized) / len(prioritized):.2f}"
        )

        return prioritized

    def _analyze_with_llm(
        self,
        context: str,
        focus_category: Optional[SuggestionCategory],
        max_suggestions: int
    ) -> List[Suggestion]:
        """
        Analisa código usando Google Gemini

        Args:
            context: Contexto do código
            focus_category: Categoria específica
            max_suggestions: Máximo de sugestões

        Returns:
            Lista de sugestões não filtradas
        """
        if not self.gemini_api_key:
            logger.warning("⚠️ GEMINI_API_KEY não configurada, usando sugestões mock")
            return self._generate_mock_suggestions()

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            # Constrói prompt
            prompt = self._build_analysis_prompt(
                context=context,
                focus_category=focus_category,
                max_suggestions=max_suggestions
            )

            # Chama LLM
            logger.info("🤖 Consultando Gemini...")
            response = model.generate_content(prompt)

            # Parse resposta
            suggestions = self._parse_llm_response(response.text)

            logger.info(f"✅ LLM retornou {len(suggestions)} sugestões")
            return suggestions

        except ImportError:
            logger.error("❌ google-generativeai não instalado. Instale: pip install google-generativeai")
            return self._generate_mock_suggestions()
        except Exception as e:
            logger.error(f"❌ Erro ao chamar Gemini: {e}")
            return self._generate_mock_suggestions()

    def _build_analysis_prompt(
        self,
        context: str,
        focus_category: Optional[SuggestionCategory],
        max_suggestions: int
    ) -> str:
        """Constrói prompt para análise LLM"""
        category_focus = f"\nFOCUS CATEGORY: {focus_category.value}" if focus_category else ""

        prompt = f"""
You are MAXIMUS ORÁCULO, an AI system analyzing your own codebase for self-improvement.

**YOUR MISSION**: Analyze the MAXIMUS codebase below and suggest {max_suggestions} HIGH-IMPACT improvements.
{category_focus}

**CODEBASE CONTEXT**:
{context}

**ANALYSIS CATEGORIES**:
1. **SECURITY**: Vulnerabilities, injection risks, authentication flaws
2. **PERFORMANCE**: Bottlenecks, inefficient algorithms, resource leaks
3. **FEATURES**: Missing capabilities, UX improvements, new integrations
4. **REFACTORING**: Code smells, duplication, architectural improvements
5. **DOCUMENTATION**: Missing docs, unclear comments, outdated READMEs
6. **TESTING**: Missing tests, low coverage, flaky tests

**OUTPUT FORMAT** (JSON array of suggestions):
```json
[
  {{
    "category": "security|performance|features|refactoring|documentation|testing",
    "priority": "critical|high|medium|low",
    "title": "Clear, actionable title (max 100 chars)",
    "description": "Detailed explanation of the issue and why it matters (200-500 chars)",
    "affected_files": ["path/to/file1.py", "path/to/file2.py"],
    "confidence_score": 0.95,
    "impact_score": 0.85,
    "effort_estimate_hours": 8,
    "implementation_steps": [
      "Step 1: ...",
      "Step 2: ...",
      "Step 3: ..."
    ],
    "code_example": "# Optional: Show how to implement\\ndef improved_function():\\n    pass",
    "references": ["https://owasp.org/...", "https://docs.python.org/..."],
    "reasoning": "Why this suggestion matters and how it improves MAXIMUS (100-300 chars)"
  }}
]
```

**SCORING GUIDELINES**:
- **confidence_score**: How certain you are this is a real issue (0.7-1.0)
- **impact_score**: How much this improves MAXIMUS (0.5-1.0)
- **priority**: critical (fix now), high (fix soon), medium (backlog), low (nice-to-have)

**IMPORTANT**:
- Focus on HIGH-IMPACT, ACTIONABLE suggestions
- Provide SPECIFIC file paths from the context
- Include CONCRETE implementation steps
- Avoid generic advice
- Prioritize SECURITY and PERFORMANCE

Return ONLY valid JSON, no markdown formatting.
"""
        return prompt

    def _parse_llm_response(self, response_text: str) -> List[Suggestion]:
        """
        Parse resposta do LLM em objetos Suggestion

        Args:
            response_text: Resposta raw do LLM

        Returns:
            Lista de objetos Suggestion
        """
        import json
        import re
        from uuid import uuid4

        try:
            # Remove markdown code blocks se presentes
            cleaned = re.sub(r'```json\s*|\s*```', '', response_text.strip())

            # Parse JSON
            suggestions_data = json.loads(cleaned)

            if not isinstance(suggestions_data, list):
                logger.error("❌ LLM não retornou array JSON")
                return []

            # Converte para objetos Suggestion
            suggestions = []
            for data in suggestions_data:
                try:
                    suggestion = Suggestion(
                        suggestion_id=f"sug_{uuid4().hex[:8]}",
                        timestamp=datetime.utcnow(),
                        category=SuggestionCategory(data['category']),
                        priority=SuggestionPriority(data['priority']),
                        title=data['title'],
                        description=data['description'],
                        affected_files=data.get('affected_files', []),
                        confidence_score=float(data['confidence_score']),
                        impact_score=float(data['impact_score']),
                        effort_estimate_hours=int(data['effort_estimate_hours']),
                        implementation_steps=data.get('implementation_steps', []),
                        code_example=data.get('code_example'),
                        references=data.get('references', []),
                        reasoning=data.get('reasoning', '')
                    )
                    suggestions.append(suggestion)
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"⚠️ Sugestão inválida ignorada: {e}")
                    continue

            return suggestions

        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao parsear JSON do LLM: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            return []

    def _prioritize_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """
        Prioriza sugestões por impacto, confiança e prioridade

        Args:
            suggestions: Lista de sugestões

        Returns:
            Lista ordenada por prioridade
        """
        # Score composto: impact * confidence * priority_weight
        priority_weights = {
            SuggestionPriority.CRITICAL: 10,
            SuggestionPriority.HIGH: 5,
            SuggestionPriority.MEDIUM: 2,
            SuggestionPriority.LOW: 1
        }

        def score(s: Suggestion) -> float:
            return (
                s.impact_score *
                s.confidence_score *
                priority_weights[s.priority]
            )

        return sorted(suggestions, key=score, reverse=True)

    def _generate_mock_suggestions(self) -> List[Suggestion]:
        """Gera sugestões mock para testes sem API key"""
        from uuid import uuid4

        return [
            Suggestion(
                suggestion_id=f"sug_{uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                category=SuggestionCategory.SECURITY,
                priority=SuggestionPriority.HIGH,
                title="Adicionar validação de input em endpoints críticos",
                description="Endpoints de análise não validam tamanho/tipo de inputs, permitindo DoS via payloads gigantes",
                affected_files=["maximus_core_service/main.py"],
                confidence_score=0.85,
                impact_score=0.90,
                effort_estimate_hours=4,
                implementation_steps=[
                    "Adicionar Pydantic validators para file_size, string_length",
                    "Implementar rate limiting por IP",
                    "Adicionar timeout em operações de I/O"
                ],
                code_example="# Exemplo\nclass FileAnalysisRequest(BaseModel):\n    file_path: str = Field(..., max_length=512)\n    @validator('file_path')\n    def validate_size(cls, v):\n        if os.path.getsize(v) > 100_000_000:\n            raise ValueError('File too large')\n        return v",
                references=["https://owasp.org/www-community/vulnerabilities/Denial_of_Service"],
                reasoning="Protege contra ataques de DoS e garante estabilidade em produção"
            ),
            Suggestion(
                suggestion_id=f"sug_{uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                category=SuggestionCategory.PERFORMANCE,
                priority=SuggestionPriority.MEDIUM,
                title="Implementar cache Redis para resultados de IP intelligence",
                description="Queries repetidas ao IP Intel Service causam latência. Cache reduziria 70% das chamadas.",
                affected_files=["adr_core_service/connectors/ip_intelligence_connector.py"],
                confidence_score=0.92,
                impact_score=0.75,
                effort_estimate_hours=6,
                implementation_steps=[
                    "Instalar redis-py",
                    "Criar RedisCache wrapper class",
                    "Adicionar cache lookup antes de HTTP request",
                    "Configurar TTL de 1 hora para IP reputation"
                ],
                code_example="# Exemplo\nimport redis\n\nclass IPIntelConnector:\n    def __init__(self):\n        self.cache = redis.Redis(host='localhost', port=6379, db=0)\n    \n    async def get_ip_info(self, ip: str):\n        cached = self.cache.get(f'ip:{ip}')\n        if cached:\n            return json.loads(cached)\n        # ... fetch from API",
                references=["https://redis.io/docs/manual/patterns/caching/"],
                reasoning="Reduz latência de análise em 40-60% e custos de infraestrutura"
            )
        ]

    def get_suggestions_by_category(self, category: SuggestionCategory) -> List[Suggestion]:
        """Filtra sugestões por categoria"""
        return [s for s in self.suggestions_generated if s.category == category]

    def get_critical_suggestions(self) -> List[Suggestion]:
        """Retorna apenas sugestões críticas"""
        return [s for s in self.suggestions_generated if s.priority == SuggestionPriority.CRITICAL]

    def export_suggestions(self, filepath: str):
        """Exporta sugestões para JSON"""
        import json

        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_suggestions': len(self.suggestions_generated),
            'suggestions': [s.to_dict() for s in self.suggestions_generated]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Sugestões exportadas para: {filepath}")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das sugestões geradas"""
        if not self.suggestions_generated:
            return {'total': 0}

        return {
            'total': len(self.suggestions_generated),
            'by_category': {
                cat.value: len(self.get_suggestions_by_category(cat))
                for cat in SuggestionCategory
            },
            'by_priority': {
                'critical': len([s for s in self.suggestions_generated if s.priority == SuggestionPriority.CRITICAL]),
                'high': len([s for s in self.suggestions_generated if s.priority == SuggestionPriority.HIGH]),
                'medium': len([s for s in self.suggestions_generated if s.priority == SuggestionPriority.MEDIUM]),
                'low': len([s for s in self.suggestions_generated if s.priority == SuggestionPriority.LOW])
            },
            'avg_confidence': sum(s.confidence_score for s in self.suggestions_generated) / len(self.suggestions_generated),
            'avg_impact': sum(s.impact_score for s in self.suggestions_generated) / len(self.suggestions_generated),
            'total_effort_hours': sum(s.effort_estimate_hours for s in self.suggestions_generated)
        }


# Helper function
def generate_suggestions(focus_category: Optional[str] = None, max_suggestions: int = 10) -> List[Suggestion]:
    """Helper para geração rápida de sugestões"""
    generator = SuggestionGenerator()
    category = SuggestionCategory(focus_category) if focus_category else None
    return generator.generate_suggestions(
        focus_category=category,
        max_suggestions=max_suggestions
    )


if __name__ == "__main__":
    # Teste standalone
    logging.basicConfig(level=logging.INFO)

    generator = SuggestionGenerator()
    suggestions = generator.generate_suggestions(max_suggestions=5)

    print("\n🧠 SUGESTÕES DE MELHORIA GERADAS:")
    print(f"Total: {len(suggestions)}\n")

    for i, sugg in enumerate(suggestions, 1):
        print(f"\n{'='*80}")
        print(f"#{i} [{sugg.category.value.upper()}] {sugg.title}")
        print(f"Priority: {sugg.priority.value} | Confidence: {sugg.confidence_score:.2f} | Impact: {sugg.impact_score:.2f}")
        print(f"Effort: {sugg.effort_estimate_hours}h")
        print(f"\n{sugg.description}")
        print(f"\nAffected files:")
        for f in sugg.affected_files:
            print(f"  - {f}")
        print(f"\nImplementation:")
        for step in sugg.implementation_steps:
            print(f"  • {step}")

    print("\n\n📊 ESTATÍSTICAS:")
    stats = generator.get_stats()
    print(f"Total de sugestões: {stats['total']}")
    print(f"Confiança média: {stats['avg_confidence']:.2f}")
    print(f"Impacto médio: {stats['avg_impact']:.2f}")
    print(f"Esforço total: {stats['total_effort_hours']}h")

    print("\n\nPor categoria:")
    for cat, count in stats['by_category'].items():
        print(f"  {cat}: {count}")

    print("\n\nPor prioridade:")
    for pri, count in stats['by_priority'].items():
        print(f"  {pri}: {count}")
