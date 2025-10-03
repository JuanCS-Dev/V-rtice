"""
Maximus Chain-of-Thought System - Explicit Reasoning
====================================================

Implementa raciocínio explícito tipo Chain-of-Thought (CoT) para:

1. Decompor problemas complexos em passos
2. Tornar o raciocínio da IA transparente
3. Permitir self-correction
4. Aumentar precisão em tarefas de reasoning

Resolve problema do Manifesto:
- "Raciocínio Fraco" causado por arquitetura auto-regressiva
- Melhora trustworthiness através de explicabilidade

Inspiração: o1-preview, Chain-of-Thought Prompting, Tree of Thoughts
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import asyncio


class ReasoningType(str, Enum):
    """Tipos de raciocínio"""
    LINEAR = "linear"  # Sequencial simples (A → B → C)
    BRANCHING = "branching"  # Tree of Thoughts (múltiplos caminhos)
    ITERATIVE = "iterative"  # Refinar resposta iterativamente
    SELF_CRITIQUE = "self_critique"  # Se auto-avaliar e corrigir


class StepType(str, Enum):
    """Tipos de passo no reasoning chain"""
    UNDERSTAND = "understand"  # Entender o problema
    DECOMPOSE = "decompose"  # Quebrar em sub-problemas
    ANALYZE = "analyze"  # Analisar informação
    HYPOTHESIZE = "hypothesize"  # Formar hipóteses
    VALIDATE = "validate"  # Validar hipótese
    SYNTHESIZE = "synthesize"  # Sintetizar conclusão
    REFLECT = "reflect"  # Refletir sobre resultado
    CORRECT = "correct"  # Corrigir erros


class StepStatus(str, Enum):
    """Status de um passo"""
    PENDING = "pending"
    THINKING = "thinking"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ReasoningStep:
    """
    Um único passo no chain of thought.
    """
    step_id: str
    step_type: StepType
    question: str  # O que estamos tentando resolver neste passo
    thought: str  # O raciocínio explícito
    answer: Optional[str] = None  # Resposta deste passo
    confidence: float = 0.0  # 0-1
    status: StepStatus = StepStatus.PENDING
    parent_step_id: Optional[str] = None  # Para tree of thoughts
    alternatives: List[str] = field(default_factory=list)  # Caminhos alternativos considerados
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.step_id,
            "type": self.step_type,
            "question": self.question,
            "thought": self.thought,
            "answer": self.answer,
            "confidence": self.confidence,
            "status": self.status,
            "parent": self.parent_step_id,
            "alternatives": self.alternatives,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class ReasoningChain:
    """
    Cadeia completa de raciocínio (Chain-of-Thought).
    """
    chain_id: str
    problem: str  # Problema original
    reasoning_type: ReasoningType
    steps: List[ReasoningStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    overall_confidence: float = 0.0
    status: str = "reasoning"  # reasoning, completed, failed
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    total_steps: int = 0
    errors: List[str] = field(default_factory=list)

    def add_step(self, step: ReasoningStep):
        """Adiciona passo à cadeia"""
        self.steps.append(step)
        self.total_steps = len(self.steps)

    def get_step(self, step_id: str) -> Optional[ReasoningStep]:
        """Busca passo por ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_path(self) -> List[ReasoningStep]:
        """Retorna caminho principal de raciocínio"""
        # Para linear: todos os steps
        # Para branching: apenas o caminho que levou à resposta final
        return self.steps  # Simplificado

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.chain_id,
            "problem": self.problem,
            "type": self.reasoning_type,
            "steps": [s.to_dict() for s in self.steps],
            "final_answer": self.final_answer,
            "confidence": self.overall_confidence,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_steps": self.total_steps,
            "errors": self.errors
        }


class CoTPromptBuilder:
    """
    Constrói prompts estruturados para Chain-of-Thought.
    """

    @staticmethod
    def build_linear_prompt(problem: str, context: Optional[str] = None) -> str:
        """
        Prompt para raciocínio linear (sequencial).

        Format:
        Problem → Understand → Plan → Execute → Verify → Conclude
        """
        prompt = f"""You are Maximus, an elite AI analyst. Use explicit step-by-step reasoning.

PROBLEM:
{problem}
"""

        if context:
            prompt += f"""
CONTEXT:
{context}
"""

        prompt += """
INSTRUCTIONS:
Think step-by-step and show your work. For each step:
1. State what you're trying to figure out
2. Show your reasoning
3. State your conclusion for that step
4. Rate your confidence (0-100%)

Use this format:

STEP 1 - UNDERSTAND THE PROBLEM:
- What I need to figure out: [question]
- My reasoning: [thought process]
- Conclusion: [answer]
- Confidence: [X%]

STEP 2 - ANALYZE AVAILABLE INFORMATION:
- What I need to figure out: [question]
- My reasoning: [thought process]
- Conclusion: [answer]
- Confidence: [X%]

[Continue with more steps as needed]

FINAL ANSWER:
[Clear, concise answer to the original problem]

OVERALL CONFIDENCE: [X%]

Begin your step-by-step reasoning:"""

        return prompt

    @staticmethod
    def build_self_critique_prompt(
        problem: str,
        initial_answer: str,
        context: Optional[str] = None
    ) -> str:
        """
        Prompt para self-critique (se auto-avaliar).

        The AI critiques its own answer and improves it.
        """
        prompt = f"""You are Maximus, an elite AI analyst. You just generated an answer, but now you need to critique it and improve it.

ORIGINAL PROBLEM:
{problem}

YOUR INITIAL ANSWER:
{initial_answer}
"""

        if context:
            prompt += f"""
ADDITIONAL CONTEXT:
{context}
"""

        prompt += """
SELF-CRITIQUE INSTRUCTIONS:
1. Identify potential errors or weaknesses in your answer
2. Check for logical flaws, unsupported claims, or missing information
3. Consider alternative perspectives
4. Generate an improved answer

Use this format:

CRITIQUE:
- Weakness 1: [what's wrong]
- Weakness 2: [what's wrong]
- Missing: [what's missing]
- Confidence in initial answer: [X%]

ALTERNATIVE PERSPECTIVES:
- Alternative 1: [different angle]
- Alternative 2: [different angle]

IMPROVED ANSWER:
[Better version addressing the critiques]

CONFIDENCE IN IMPROVED ANSWER: [X%]

Begin your self-critique:"""

        return prompt

    @staticmethod
    def build_decomposition_prompt(problem: str) -> str:
        """
        Prompt para decompor problema complexo em sub-problemas.
        """
        prompt = f"""You are Maximus, an elite AI analyst. You need to break down a complex problem into smaller, manageable sub-problems.

COMPLEX PROBLEM:
{problem}

DECOMPOSITION INSTRUCTIONS:
1. Identify the core question
2. Break it into 3-5 sub-questions
3. For each sub-question, explain why it's important
4. Suggest the order to tackle them

Use this format:

CORE QUESTION:
[Restate the essence of the problem]

SUB-PROBLEMS:
1. [Sub-question 1]
   - Why important: [explanation]
   - Prerequisites: [what's needed to answer this]

2. [Sub-question 2]
   - Why important: [explanation]
   - Prerequisites: [what's needed to answer this]

[Continue...]

RECOMMENDED ORDER:
1. Start with: [sub-question X] because [reason]
2. Then: [sub-question Y] because [reason]
3. Finally: [sub-question Z] because [reason]

Begin decomposition:"""

        return prompt


class ChainOfThoughtEngine:
    """
    Engine principal para execução de Chain-of-Thought reasoning.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client  # Cliente LLM (OpenAI, Anthropic, etc)
        self.prompt_builder = CoTPromptBuilder()
        self.chains: Dict[str, ReasoningChain] = {}
        self.step_counter = 0

    async def reason(
        self,
        problem: str,
        reasoning_type: ReasoningType = ReasoningType.LINEAR,
        context: Optional[str] = None,
        max_steps: int = 10
    ) -> ReasoningChain:
        """
        Executa raciocínio Chain-of-Thought.

        Args:
            problem: Problema a resolver
            reasoning_type: Tipo de raciocínio
            context: Contexto adicional
            max_steps: Máximo de passos

        Returns:
            ReasoningChain com raciocínio completo
        """
        chain = ReasoningChain(
            chain_id=f"chain_{datetime.now().timestamp()}",
            problem=problem,
            reasoning_type=reasoning_type
        )

        if reasoning_type == ReasoningType.LINEAR:
            await self._reason_linear(chain, problem, context, max_steps)
        elif reasoning_type == ReasoningType.SELF_CRITIQUE:
            await self._reason_self_critique(chain, problem, context)
        elif reasoning_type == ReasoningType.ITERATIVE:
            await self._reason_iterative(chain, problem, context, max_steps)
        else:
            chain.status = "failed"
            chain.errors.append(f"Unsupported reasoning type: {reasoning_type}")

        self.chains[chain.chain_id] = chain
        return chain

    async def _reason_linear(
        self,
        chain: ReasoningChain,
        problem: str,
        context: Optional[str],
        max_steps: int
    ):
        """Raciocínio linear (sequencial)"""

        # 1. Gera prompt CoT
        prompt = self.prompt_builder.build_linear_prompt(problem, context)

        # 2. Chama LLM com prompt estruturado
        # TODO: Integrar com LLM real
        response = await self._call_llm(prompt)

        # 3. Parse resposta em steps
        steps = self._parse_linear_response(response)

        for step in steps:
            chain.add_step(step)

        # 4. Extrai resposta final
        chain.final_answer = self._extract_final_answer(response)
        chain.overall_confidence = self._calculate_overall_confidence(steps)
        chain.status = "completed"
        chain.end_time = datetime.now().isoformat()

    async def _reason_self_critique(
        self,
        chain: ReasoningChain,
        problem: str,
        context: Optional[str]
    ):
        """Raciocínio com self-critique"""

        # 1. Gera resposta inicial
        initial_prompt = f"Answer this question concisely: {problem}"
        if context:
            initial_prompt += f"\n\nContext: {context}"

        initial_answer = await self._call_llm(initial_prompt)

        # Step 1: Initial answer
        step1 = ReasoningStep(
            step_id=self._next_step_id(),
            step_type=StepType.HYPOTHESIZE,
            question="What's my initial answer?",
            thought="Generating initial response without deep analysis",
            answer=initial_answer,
            confidence=0.6,
            status=StepStatus.COMPLETED
        )
        chain.add_step(step1)

        # 2. Self-critique
        critique_prompt = self.prompt_builder.build_self_critique_prompt(
            problem, initial_answer, context
        )
        critique_response = await self._call_llm(critique_prompt)

        # Step 2: Critique
        step2 = ReasoningStep(
            step_id=self._next_step_id(),
            step_type=StepType.REFLECT,
            question="What's wrong with my initial answer?",
            thought=self._extract_critique(critique_response),
            answer=None,
            confidence=0.8,
            status=StepStatus.COMPLETED,
            parent_step_id=step1.step_id
        )
        chain.add_step(step2)

        # Step 3: Improved answer
        improved_answer = self._extract_improved_answer(critique_response)
        step3 = ReasoningStep(
            step_id=self._next_step_id(),
            step_type=StepType.SYNTHESIZE,
            question="What's my improved answer?",
            thought="Incorporating critiques and improvements",
            answer=improved_answer,
            confidence=0.85,
            status=StepStatus.COMPLETED,
            parent_step_id=step2.step_id
        )
        chain.add_step(step3)

        chain.final_answer = improved_answer
        chain.overall_confidence = 0.85
        chain.status = "completed"
        chain.end_time = datetime.now().isoformat()

    async def _reason_iterative(
        self,
        chain: ReasoningChain,
        problem: str,
        context: Optional[str],
        max_iterations: int
    ):
        """Raciocínio iterativo (refinar resposta múltiplas vezes)"""

        current_answer = None
        current_confidence = 0.0

        for iteration in range(max_iterations):
            # Monta prompt iterativo
            if iteration == 0:
                prompt = f"Answer: {problem}"
                if context:
                    prompt += f"\n\nContext: {context}"
            else:
                prompt = f"""Previous answer (confidence {current_confidence:.0%}):
{current_answer}

Improve this answer for: {problem}
Be more precise, accurate, and comprehensive."""

            # Gera resposta
            response = await self._call_llm(prompt)

            # Cria step
            step = ReasoningStep(
                step_id=self._next_step_id(),
                step_type=StepType.SYNTHESIZE if iteration > 0 else StepType.HYPOTHESIZE,
                question=f"Iteration {iteration + 1}: What's my answer?",
                thought=f"Refining answer (iteration {iteration + 1}/{max_iterations})",
                answer=response,
                confidence=min(0.5 + (iteration * 0.1), 0.95),
                status=StepStatus.COMPLETED
            )
            chain.add_step(step)

            current_answer = response
            current_confidence = step.confidence

            # Para se confiança já é alta
            if current_confidence >= 0.9:
                break

        chain.final_answer = current_answer
        chain.overall_confidence = current_confidence
        chain.status = "completed"
        chain.end_time = datetime.now().isoformat()

    async def decompose_problem(self, problem: str) -> Dict[str, Any]:
        """
        Decompõe problema complexo em sub-problemas.

        Returns:
            {
                "core_question": str,
                "sub_problems": List[Dict],
                "recommended_order": List[str]
            }
        """
        prompt = self.prompt_builder.build_decomposition_prompt(problem)
        response = await self._call_llm(prompt)

        # Parse resposta
        # TODO: Parsing mais sofisticado
        return {
            "core_question": problem,
            "sub_problems": [],
            "recommended_order": [],
            "raw_response": response
        }

    async def _call_llm(self, prompt: str) -> str:
        """Chama LLM (placeholder)"""
        # TODO: Integrar com LLM real (OpenAI, Anthropic, etc)
        # Por enquanto, resposta fake
        await asyncio.sleep(0.1)  # Simula latência

        if "STEP 1" in prompt:
            return """STEP 1 - UNDERSTAND THE PROBLEM:
- What I need to figure out: What is being asked?
- My reasoning: Analyzing the question to identify key components
- Conclusion: This is a multi-step problem requiring structured analysis
- Confidence: 85%

STEP 2 - ANALYZE AVAILABLE INFORMATION:
- What I need to figure out: What data do I have?
- My reasoning: Reviewing provided context and constraints
- Conclusion: Sufficient information available
- Confidence: 80%

FINAL ANSWER:
Based on structured analysis, the answer is clear.

OVERALL CONFIDENCE: 82%"""
        else:
            return "This is a simulated LLM response. Integrate with real LLM for production."

    def _parse_linear_response(self, response: str) -> List[ReasoningStep]:
        """Parse resposta linear em steps"""
        steps = []

        # TODO: Parsing mais robusto com regex
        # Por enquanto, cria steps genéricos
        import re
        step_pattern = r'STEP (\d+) - ([A-Z\s]+):(.*?)(?=STEP \d+|FINAL ANSWER|$)'
        matches = re.finditer(step_pattern, response, re.DOTALL)

        for match in matches:
            step_num = match.group(1)
            step_title = match.group(2).strip()
            step_content = match.group(3).strip()

            # Extrai confidence
            conf_match = re.search(r'Confidence:\s*(\d+)%', step_content)
            confidence = float(conf_match.group(1)) / 100 if conf_match else 0.7

            step = ReasoningStep(
                step_id=self._next_step_id(),
                step_type=StepType.ANALYZE,
                question=step_title,
                thought=step_content,
                answer=None,
                confidence=confidence,
                status=StepStatus.COMPLETED
            )
            steps.append(step)

        return steps if steps else self._create_fallback_steps()

    def _create_fallback_steps(self) -> List[ReasoningStep]:
        """Cria steps genéricos se parsing falhar"""
        return [
            ReasoningStep(
                step_id=self._next_step_id(),
                step_type=StepType.UNDERSTAND,
                question="Understanding the problem",
                thought="Analyzing the question",
                confidence=0.7,
                status=StepStatus.COMPLETED
            )
        ]

    def _extract_final_answer(self, response: str) -> str:
        """Extrai resposta final"""
        import re
        match = re.search(r'FINAL ANSWER:\s*(.+?)(?=OVERALL CONFIDENCE|$)', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response[:200]  # Fallback: primeiros 200 chars

    def _extract_critique(self, response: str) -> str:
        """Extrai crítica"""
        import re
        match = re.search(r'CRITIQUE:\s*(.+?)(?=ALTERNATIVE|IMPROVED|$)', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return "Self-critique performed"

    def _extract_improved_answer(self, response: str) -> str:
        """Extrai resposta melhorada"""
        import re
        match = re.search(r'IMPROVED ANSWER:\s*(.+?)(?=CONFIDENCE|$)', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response

    def _calculate_overall_confidence(self, steps: List[ReasoningStep]) -> float:
        """Calcula confiança geral"""
        if not steps:
            return 0.0
        return sum(s.confidence for s in steps) / len(steps)

    def _next_step_id(self) -> str:
        """Gera próximo step ID"""
        self.step_counter += 1
        return f"step_{self.step_counter}"

    def get_chain(self, chain_id: str) -> Optional[ReasoningChain]:
        """Recupera chain por ID"""
        return self.chains.get(chain_id)

    def export_chain(self, chain: ReasoningChain, format: str = "markdown") -> str:
        """
        Exporta chain em formato legível.

        Args:
            chain: Chain a exportar
            format: markdown, json, text

        Returns:
            String formatada
        """
        if format == "json":
            return json.dumps(chain.to_dict(), indent=2)

        elif format == "markdown":
            lines = []
            lines.append(f"# Chain of Thought: {chain.problem}\n")
            lines.append(f"**Type:** {chain.reasoning_type}")
            lines.append(f"**Status:** {chain.status}")
            lines.append(f"**Confidence:** {chain.overall_confidence:.2%}\n")

            lines.append("## Reasoning Steps\n")
            for i, step in enumerate(chain.steps, 1):
                lines.append(f"### Step {i}: {step.step_type}")
                lines.append(f"**Question:** {step.question}")
                lines.append(f"**Thought:** {step.thought}")
                if step.answer:
                    lines.append(f"**Answer:** {step.answer}")
                lines.append(f"**Confidence:** {step.confidence:.2%}\n")

            lines.append("## Final Answer\n")
            lines.append(chain.final_answer or "No answer generated")

            return "\n".join(lines)

        else:  # text
            lines = []
            lines.append(f"PROBLEM: {chain.problem}")
            lines.append(f"CONFIDENCE: {chain.overall_confidence:.2%}")
            lines.append("\nSTEPS:")
            for i, step in enumerate(chain.steps, 1):
                lines.append(f"{i}. [{step.step_type}] {step.thought[:100]}...")
            lines.append(f"\nFINAL: {chain.final_answer}")
            return "\n".join(lines)


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_usage():
    """Demonstra uso do sistema Chain-of-Thought"""

    cot = ChainOfThoughtEngine()

    # 1. Raciocínio Linear
    print("=== LINEAR REASONING ===")
    chain1 = await cot.reason(
        problem="What are the top 3 cyber threats in 2024?",
        reasoning_type=ReasoningType.LINEAR,
        context="Focus on enterprise environments"
    )
    print(cot.export_chain(chain1, format="text"))

    # 2. Self-Critique
    print("\n=== SELF-CRITIQUE ===")
    chain2 = await cot.reason(
        problem="Is ransomware the biggest threat?",
        reasoning_type=ReasoningType.SELF_CRITIQUE
    )
    print(cot.export_chain(chain2, format="text"))

    # 3. Iterative
    print("\n=== ITERATIVE REASONING ===")
    chain3 = await cot.reason(
        problem="Explain SQL injection in simple terms",
        reasoning_type=ReasoningType.ITERATIVE,
        max_steps=3
    )
    print(cot.export_chain(chain3, format="text"))


if __name__ == "__main__":
    asyncio.run(example_usage())
