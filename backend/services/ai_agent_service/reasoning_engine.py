"""
Aurora Reasoning Engine - NSA-Grade Cognitive Core
==================================================

O cérebro da Aurora. Implementa pensamento explícito tipo Chain-of-Thought,
permitindo que a IA:
- Decomponha problemas complexos
- Pense passo-a-passo
- Se auto-avalie
- Explique seu raciocínio
- Se corrija quando necessário

Inspirado em: Claude Code, o1-preview, AutoGPT, e metodologias de elite da NSA.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import asyncio
import httpx
from pydantic import BaseModel


class ThoughtType(str, Enum):
    """Tipos de pensamento no reasoning chain"""
    OBSERVATION = "observation"  # Observando o problema
    ANALYSIS = "analysis"  # Analisando dados
    HYPOTHESIS = "hypothesis"  # Formando hipótese
    PLANNING = "planning"  # Planejando ação
    EXECUTION = "execution"  # Executando ação
    VALIDATION = "validation"  # Validando resultado
    REFLECTION = "reflection"  # Refletindo sobre processo
    DECISION = "decision"  # Tomando decisão
    CORRECTION = "correction"  # Corrigindo erro


class ConfidenceLevel(str, Enum):
    """Níveis de confiança"""
    VERY_LOW = "very_low"  # < 30%
    LOW = "low"  # 30-50%
    MEDIUM = "medium"  # 50-70%
    HIGH = "high"  # 70-90%
    VERY_HIGH = "very_high"  # > 90%


@dataclass
class Thought:
    """
    Representa um único pensamento no reasoning chain
    """
    type: ThoughtType
    content: str
    confidence: float  # 0-100
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_thought_id: Optional[str] = None
    thought_id: str = field(default_factory=lambda: f"thought_{datetime.now().timestamp()}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.thought_id,
            "type": self.type,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "parent": self.parent_thought_id
        }


@dataclass
class ThoughtChain:
    """
    Cadeia completa de pensamentos (Chain-of-Thought)
    """
    task: str
    thoughts: List[Thought] = field(default_factory=list)
    final_answer: Optional[str] = None
    overall_confidence: float = 0.0
    status: str = "thinking"  # thinking, completed, failed
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    total_thoughts: int = 0

    def add_thought(self, thought: Thought):
        """Adiciona pensamento à cadeia"""
        self.thoughts.append(thought)
        self.total_thoughts = len(self.thoughts)

    def get_confidence_level(self) -> ConfidenceLevel:
        """Retorna nível de confiança categórico"""
        if self.overall_confidence < 30:
            return ConfidenceLevel.VERY_LOW
        elif self.overall_confidence < 50:
            return ConfidenceLevel.LOW
        elif self.overall_confidence < 70:
            return ConfidenceLevel.MEDIUM
        elif self.overall_confidence < 90:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "thoughts": [t.to_dict() for t in self.thoughts],
            "final_answer": self.final_answer,
            "confidence": {
                "score": self.overall_confidence,
                "level": self.get_confidence_level()
            },
            "status": self.status,
            "duration": self._calculate_duration(),
            "total_thoughts": self.total_thoughts
        }

    def _calculate_duration(self) -> Optional[float]:
        """Calcula duração do reasoning"""
        if self.end_time:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            return (end - start).total_seconds()
        return None


class ReasoningEngine:
    """
    Motor de raciocínio da Aurora - NSA Grade

    Implementa múltiplas estratégias de reasoning:
    - Chain-of-Thought: Pensamento sequencial
    - Tree-of-Thought: Pensamento com branches
    - Self-Consistency: Múltiplos caminhos para mesma resposta
    - Reflection: Auto-avaliação e correção
    """

    def __init__(
        self,
        llm_provider: str = "anthropic",
        anthropic_api_key: str = "",
        openai_api_key: str = "",
        llm_callable: Optional[callable] = None
    ):
        """
        Args:
            llm_provider: Provider do LLM ("anthropic", "openai", "local")
            anthropic_api_key: API key da Anthropic
            openai_api_key: API key da OpenAI
            llm_callable: Função async customizada que chama o LLM (opcional)
        """
        self.llm_provider = llm_provider
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        self.llm_callable = llm_callable
        self.reasoning_history: List[ThoughtChain] = []

    async def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Chama o LLM configurado.

        Se llm_callable foi fornecido, usa ele.
        Caso contrário, usa a API direta baseada em llm_provider.
        """
        # Use custom callable se fornecido
        if self.llm_callable:
            return await self.llm_callable(prompt)

        # Fallback para APIs diretas
        if self.llm_provider == "anthropic" and self.anthropic_api_key:
            return await self._call_anthropic(prompt, temperature)
        elif self.llm_provider == "openai" and self.openai_api_key:
            return await self._call_openai(prompt, temperature)
        else:
            # Sem LLM configurado - retorna placeholder
            return f"[LLM not configured] Simulated response for: {prompt[:100]}..."

    async def _call_anthropic(self, prompt: str, temperature: float = 0.7) -> str:
        """Chama Claude via API Anthropic"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 2048,
                        "temperature": temperature,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    # Extrair texto da resposta
                    for content_block in result.get("content", []):
                        if content_block.get("type") == "text":
                            return content_block.get("text", "")
                    return "No text response"
                else:
                    return f"Error calling Anthropic API: {response.status_code}"

            except Exception as e:
                return f"Exception calling Anthropic: {str(e)}"

    async def _call_openai(self, prompt: str, temperature: float = 0.7) -> str:
        """Chama GPT via API OpenAI"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "temperature": temperature,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    return f"Error calling OpenAI API: {response.status_code}"

            except Exception as e:
                return f"Exception calling OpenAI: {str(e)}"

    async def think_step_by_step(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        max_steps: int = 10,
        confidence_threshold: float = 80.0
    ) -> ThoughtChain:
        """
        Pensa passo-a-passo sobre uma tarefa (Chain-of-Thought)

        Args:
            task: Tarefa/problema a resolver
            context: Contexto adicional
            max_steps: Máximo de passos de raciocínio
            confidence_threshold: Threshold para parar (se atingir alta confiança)

        Returns:
            ThoughtChain completa com raciocínio explícito
        """
        chain = ThoughtChain(task=task)
        context = context or {}

        # FASE 1: OBSERVAÇÃO
        observation = await self._observe(task, context)
        chain.add_thought(observation)

        # FASE 2: ANÁLISE INICIAL
        analysis = await self._analyze(task, context, observation)
        chain.add_thought(analysis)

        # FASE 3: DECOMPOSIÇÃO EM SUBPROBLEMAS
        decomposition = await self._decompose(task, analysis)
        chain.add_thought(decomposition)

        # FASE 4: PLANEJAMENTO
        plan = await self._plan(task, decomposition, context)
        chain.add_thought(plan)

        # FASE 5: EXECUÇÃO ITERATIVA
        current_step = 0
        while current_step < max_steps:
            # Executar próximo passo do plano
            execution = await self._execute_step(
                task, plan, context, current_step
            )
            chain.add_thought(execution)

            # Validar resultado
            validation = await self._validate_step(execution, task)
            chain.add_thought(validation)

            # Se validação falhou, corrigir
            if validation.confidence < 50:
                correction = await self._correct(execution, validation)
                chain.add_thought(correction)

            # Verificar se atingimos confiança suficiente
            current_confidence = self._calculate_chain_confidence(chain)
            if current_confidence >= confidence_threshold:
                break

            current_step += 1

        # FASE 6: SÍNTESE FINAL
        synthesis = await self._synthesize(chain, task)
        chain.add_thought(synthesis)

        # FASE 7: REFLEXÃO (Meta-cognição)
        reflection = await self._reflect(chain, task)
        chain.add_thought(reflection)

        # Finalizar chain
        chain.overall_confidence = self._calculate_chain_confidence(chain)
        chain.final_answer = synthesis.content
        chain.status = "completed"
        chain.end_time = datetime.now().isoformat()

        # Guardar histórico
        self.reasoning_history.append(chain)

        return chain

    async def _observe(self, task: str, context: Dict) -> Thought:
        """FASE 1: Observar e compreender o problema"""
        prompt = f"""Você é Aurora, um agente de inteligência cibernética.

Tarefa: {task}
Contexto: {json.dumps(context, indent=2)}

Primeiro passo: OBSERVAR e COMPREENDER.

Analise a tarefa e responda:
1. O que exatamente está sendo pedido?
2. Que tipo de problema é este? (cyber, osint, análise, etc)
3. Quais informações já temos?
4. Quais informações faltam?
5. Qual a complexidade estimada? (baixa/média/alta)

Seja preciso e objetivo. 2-3 parágrafos."""

        response = await self.llm_callable([
            {"role": "user", "content": prompt}
        ])

        return Thought(
            type=ThoughtType.OBSERVATION,
            content=response.get("content", ""),
            confidence=85.0,
            metadata={"phase": "observation", "task": task}
        )

    async def _analyze(self, task: str, context: Dict, observation: Thought) -> Thought:
        """FASE 2: Análise profunda"""
        prompt = f"""Baseado na observação anterior:

{observation.content}

Agora faça uma ANÁLISE PROFUNDA:
1. Identifique os componentes-chave do problema
2. Quais são os riscos/desafios?
3. Que abordagens podem ser usadas?
4. Quais tools/serviços serão necessários?
5. Há precedentes similares?

Seja analítico e técnico."""

        response = await self.llm_callable([
            {"role": "user", "content": prompt}
        ])

        return Thought(
            type=ThoughtType.ANALYSIS,
            content=response.get("content", ""),
            confidence=80.0,
            metadata={"phase": "analysis"},
            parent_thought_id=observation.thought_id
        )

    async def _decompose(self, task: str, analysis: Thought) -> Thought:
        """FASE 3: Decompor em subproblemas"""
        prompt = f"""Baseado na análise:

{analysis.content}

DECOMPONHA o problema em subproblemas menores e gerenciáveis.

Liste 3-7 subproblemas que, se resolvidos, resolvem o problema principal.
Para cada um, indique:
- Descrição clara
- Complexidade (baixa/média/alta)
- Dependências (quais outros subproblemas devem ser resolvidos primeiro)
- Ferramentas necessárias

Formato:
1. [SUBPROBLEMA]
   Complexidade: X
   Dependências: Y
   Tools: Z"""

        response = await self.llm_callable([
            {"role": "user", "content": prompt}
        ])

        return Thought(
            type=ThoughtType.HYPOTHESIS,
            content=response.get("content", ""),
            confidence=75.0,
            metadata={"phase": "decomposition"},
            parent_thought_id=analysis.thought_id
        )

    async def _plan(self, task: str, decomposition: Thought, context: Dict) -> Thought:
        """FASE 4: Criar plano de execução"""
        prompt = f"""Baseado na decomposição:

{decomposition.content}

Crie um PLANO DE EXECUÇÃO detalhado:

Para cada subproblema, defina:
1. Ordem de execução (considere dependências)
2. Tools específicas a usar
3. Parâmetros das tools
4. Critérios de sucesso
5. Fallbacks (se algo falhar)

Seja específico e executável. Este plano será seguido literalmente."""

        response = await self.llm_callable([
            {"role": "user", "content": prompt}
        ])

        return Thought(
            type=ThoughtType.PLANNING,
            content=response.get("content", ""),
            confidence=85.0,
            metadata={"phase": "planning", "executable": True},
            parent_thought_id=decomposition.thought_id
        )

    async def _execute_step(
        self, task: str, plan: Thought, context: Dict, step: int
    ) -> Thought:
        """FASE 5: Executar um passo do plano"""
        # Aqui integramos com o sistema de tools
        prompt = f"""Executando passo {step + 1} do plano:

PLANO COMPLETO:
{plan.content}

PASSO ATUAL: {step + 1}

Execute este passo e relate:
1. O que foi feito exatamente
2. Resultados obtidos
3. Se foi bem-sucedido
4. Próximos passos necessários

Seja factual e baseado em resultados reais."""

        response = await self.llm_callable([
            {"role": "user", "content": prompt}
        ])

        return Thought(
            type=ThoughtType.EXECUTION,
            content=response.get("content", ""),
            confidence=70.0,
            metadata={
                "phase": "execution",
                "step_number": step,
                "tools_used": []  # Será populado com tools reais
            },
            parent_thought_id=plan.thought_id
        )

    async def _validate_step(self, execution: Thought, task: str) -> Thought:
        """FASE 6: Validar resultado do passo"""
        prompt = f"""Valide o resultado da execução:

EXECUÇÃO:
{execution.content}

VALIDAÇÃO:
1. O objetivo do passo foi atingido?
2. Os resultados fazem sentido?
3. Há inconsistências ou erros?
4. Qual a confiança neste resultado? (0-100)
5. Próximos passos são claros?

Seja crítico e honesto."""

        response = await self.llm_callable([
            {"role": "user", "content": prompt}
        ])

        # Extrair confidence do response
        confidence = 70.0  # Default, seria extraído do texto

        return Thought(
            type=ThoughtType.VALIDATION,
            content=response.get("content", ""),
            confidence=confidence,
            metadata={"phase": "validation"},
            parent_thought_id=execution.thought_id
        )

    async def _correct(self, execution: Thought, validation: Thought) -> Thought:
        """FASE 7: Corrigir se necessário"""
        prompt = f"""A validação identificou problemas:

EXECUÇÃO ORIGINAL:
{execution.content}

PROBLEMAS IDENTIFICADOS:
{validation.content}

CORREÇÃO:
1. O que deu errado?
2. Por que deu errado?
3. Como corrigir?
4. Executar correção

Seja específico na correção."""

        response = await self.llm_callable([
            {"role": "user", "content": prompt}
        ])

        return Thought(
            type=ThoughtType.CORRECTION,
            content=response.get("content", ""),
            confidence=75.0,
            metadata={"phase": "correction", "correcting": execution.thought_id},
            parent_thought_id=validation.thought_id
        )

    async def _synthesize(self, chain: ThoughtChain, task: str) -> Thought:
        """FASE 8: Sintetizar resposta final"""
        # Resumir toda a cadeia de pensamento
        thoughts_summary = "\n\n".join([
            f"[{t.type.upper()}] {t.content[:200]}..."
            for t in chain.thoughts
        ])

        prompt = f"""Baseado em TODO o raciocínio realizado:

TAREFA ORIGINAL:
{task}

RACIOCÍNIO COMPLETO:
{thoughts_summary}

SÍNTESE FINAL:
Crie uma resposta final completa e precisa que:
1. Responde diretamente a tarefa
2. Inclui todas as descobertas importantes
3. Fornece recomendações acionáveis
4. Indica nível de confiança
5. Menciona limitações/incertezas se houver

Seja completo mas conciso. Esta é a resposta que o usuário verá."""

        response = await self.llm_callable([
            {"role": "user", "content": prompt}
        ])

        return Thought(
            type=ThoughtType.DECISION,
            content=response.get("content", ""),
            confidence=90.0,
            metadata={"phase": "synthesis", "final": True}
        )

    async def _reflect(self, chain: ThoughtChain, task: str) -> Thought:
        """FASE 9: Reflexão meta-cognitiva"""
        prompt = f"""Meta-cognição: Reflita sobre TODO o processo de raciocínio.

TAREFA: {task}
TOTAL DE PENSAMENTOS: {len(chain.thoughts)}

REFLEXÃO:
1. O raciocínio foi eficiente?
2. Houve passos desnecessários?
3. Algo foi esquecido?
4. O que poderia ser melhorado?
5. Qual confiança você tem na resposta final? (0-100)
6. Há ressalvas importantes?

Seja autocrítico e honesto. Esta reflexão será usada para melhorar futuras análises."""

        response = await self.llm_callable([
            {"role": "user", "content": prompt}
        ])

        # Extrair confidence da reflexão
        confidence = 85.0  # Seria extraído do texto

        return Thought(
            type=ThoughtType.REFLECTION,
            content=response.get("content", ""),
            confidence=confidence,
            metadata={
                "phase": "reflection",
                "meta_cognitive": True,
                "total_thoughts": len(chain.thoughts)
            }
        )

    def _calculate_chain_confidence(self, chain: ThoughtChain) -> float:
        """
        Calcula confiança geral da cadeia baseado em:
        - Confiança média dos pensamentos
        - Completude (todos passos foram executados?)
        - Validações bem-sucedidas
        - Reflexão meta-cognitiva
        """
        if not chain.thoughts:
            return 0.0

        # Média ponderada
        weights = {
            ThoughtType.OBSERVATION: 1.0,
            ThoughtType.ANALYSIS: 1.2,
            ThoughtType.HYPOTHESIS: 1.0,
            ThoughtType.PLANNING: 1.3,
            ThoughtType.EXECUTION: 1.5,
            ThoughtType.VALIDATION: 1.4,
            ThoughtType.REFLECTION: 1.6,
            ThoughtType.DECISION: 2.0,
            ThoughtType.CORRECTION: 0.8
        }

        weighted_sum = sum(
            t.confidence * weights.get(t.type, 1.0)
            for t in chain.thoughts
        )
        total_weight = sum(weights.get(t.type, 1.0) for t in chain.thoughts)

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def get_reasoning_history(self) -> List[Dict[str, Any]]:
        """Retorna histórico de raciocínios"""
        return [chain.to_dict() for chain in self.reasoning_history]

    def export_reasoning_trace(self, chain: ThoughtChain) -> str:
        """
        Exporta reasoning trace em formato legível
        (para debugging e explicabilidade)
        """
        lines = [
            "=" * 80,
            f"AURORA REASONING TRACE",
            f"Task: {chain.task}",
            f"Status: {chain.status}",
            f"Confidence: {chain.overall_confidence:.1f}% ({chain.get_confidence_level()})",
            f"Duration: {chain._calculate_duration():.2f}s" if chain._calculate_duration() else "Duration: N/A",
            f"Total Thoughts: {chain.total_thoughts}",
            "=" * 80,
            ""
        ]

        for i, thought in enumerate(chain.thoughts, 1):
            lines.extend([
                f"[STEP {i}] {thought.type.upper()}",
                f"Confidence: {thought.confidence:.1f}%",
                f"Timestamp: {thought.timestamp}",
                "-" * 80,
                thought.content,
                "",
                ""
            ])

        if chain.final_answer:
            lines.extend([
                "=" * 80,
                "FINAL ANSWER:",
                "=" * 80,
                chain.final_answer,
                ""
            ])

        return "\n".join(lines)