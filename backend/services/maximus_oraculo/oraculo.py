"""
MAXIMUS ORÁCULO - Self-Improvement Orchestrator
================================================

"Pela Arte. Pela Sociedade."

O Oráculo é o sistema de auto-melhoramento do MAXIMUS.
Ele permite que a IA analise, sugira e implemente melhorias
no seu próprio código de forma AUTÔNOMA e SEGURA.

ARQUITETURA:
┌─────────────────────────────────────────┐
│         MAXIMUS ORÁCULO                 │
├─────────────────────────────────────────┤
│                                         │
│  1. CODE SCANNER                        │
│     └─> Escaneia codebase MAXIMUS      │
│                                         │
│  2. SUGGESTION GENERATOR                │
│     └─> Analisa via LLM                 │
│     └─> Gera sugestões categorizadas    │
│                                         │
│  3. AUTO IMPLEMENTER                    │
│     └─> Aplica mudanças seguras         │
│     └─> Roda testes                     │
│     └─> Rollback automático             │
│                                         │
│  4. DAILY JOB                           │
│     └─> Cron 3h AM                      │
│     └─> Self-improvement automático     │
│                                         │
└─────────────────────────────────────────┘

FILOSOFIA:
- 🔒 SEGURANÇA PRIMEIRO (human-in-the-loop para mudanças críticas)
- 🧪 TESTES OBRIGATÓRIOS (rollback automático em falhas)
- 📝 TRANSPARÊNCIA TOTAL (logging completo)
- 🎯 IMPACTO REAL (foco em security, performance, features)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from code_scanner import CodeScanner, CodeFile
from suggestion_generator import (
    SuggestionGenerator,
    Suggestion,
    SuggestionCategory,
    SuggestionPriority
)
from auto_implementer import (
    AutoImplementer,
    ImplementationResult,
    ImplementationStatus
)

logger = logging.getLogger(__name__)


@dataclass
class OraculoSession:
    """Representa uma sessão de auto-melhoramento"""
    session_id: str
    timestamp: datetime
    files_scanned: int
    suggestions_generated: int
    suggestions_implemented: int
    suggestions_failed: int
    suggestions_awaiting_approval: int
    total_files_modified: int
    tests_passed: bool
    duration_seconds: float
    focus_category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class Oraculo:
    """
    Orquestrador de Auto-Melhoramento do MAXIMUS

    Este é o coração do sistema de meta-cognição.
    Coordena scanning, análise LLM, e implementação segura.

    Features:
    - 🔍 Auto-análise de código
    - 🧠 Sugestões inteligentes via LLM
    - 🔧 Auto-implementação segura
    - 📊 Métricas e estatísticas
    - 🔒 Multi-layer safety checks
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        enable_auto_implement: bool = False,
        enable_auto_commit: bool = False,
        require_tests: bool = True
    ):
        """
        Args:
            gemini_api_key: API key do Google Gemini
            enable_auto_implement: Se True, implementa sugestões automaticamente
            enable_auto_commit: Se True, faz commit automático (PERIGOSO!)
            require_tests: Se True, roda testes antes de commit
        """
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.enable_auto_implement = enable_auto_implement
        self.enable_auto_commit = enable_auto_commit
        self.require_tests = require_tests

        # Componentes
        self.scanner = CodeScanner()
        self.generator = SuggestionGenerator(gemini_api_key=self.gemini_api_key)
        self.implementer = AutoImplementer(
            enable_auto_commit=enable_auto_commit,
            require_tests=require_tests
        )

        # Histórico de sessões
        self.sessions: List[OraculoSession] = []

    def run_self_improvement_cycle(
        self,
        focus_category: Optional[SuggestionCategory] = None,
        max_suggestions: int = 5,
        min_confidence: float = 0.8,
        dry_run: bool = True
    ) -> OraculoSession:
        """
        Executa um ciclo completo de auto-melhoramento

        PIPELINE:
        1. Scan do codebase MAXIMUS
        2. Geração de sugestões via LLM
        3. Priorização e filtragem
        4. Implementação segura (com aprovação/testes)
        5. Relatório de resultados

        Args:
            focus_category: Categoria específica (security, performance, etc.)
            max_suggestions: Máximo de sugestões a gerar
            min_confidence: Confiança mínima (0-1)
            dry_run: Se True, apenas simula (não modifica arquivos)

        Returns:
            Objeto OraculoSession com resultados
        """
        from uuid import uuid4

        session_start = datetime.utcnow()
        session_id = f"oraculo_{uuid4().hex[:8]}"

        logger.info("="*80)
        logger.info("🔮 MAXIMUS ORÁCULO - Self-Improvement Cycle INICIADO")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Timestamp: {session_start.isoformat()}")
        logger.info(f"Focus: {focus_category.value if focus_category else 'ALL CATEGORIES'}")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
        logger.info("="*80)

        # 1. SCAN CODEBASE
        logger.info("\n📂 FASE 1: Scanning codebase...")
        code_files = self.scanner.scan_maximus_codebase()
        scan_stats = self.scanner.get_stats()
        logger.info(
            f"✅ Scan completo: {scan_stats['total_files']} arquivos | "
            f"{scan_stats['total_loc']:,} LOC | "
            f"{scan_stats['core_files']} core files"
        )

        # 2. GERA SUGESTÕES
        logger.info("\n🧠 FASE 2: Gerando sugestões via LLM...")
        suggestions = self.generator.generate_suggestions(
            focus_category=focus_category,
            max_suggestions=max_suggestions,
            min_confidence=min_confidence
        )
        suggestion_stats = self.generator.get_stats()
        logger.info(
            f"✅ {len(suggestions)} sugestões geradas | "
            f"Avg confidence: {suggestion_stats['avg_confidence']:.2f} | "
            f"Avg impact: {suggestion_stats['avg_impact']:.2f}"
        )

        # Mostra sugestões
        self._display_suggestions(suggestions)

        # 3. IMPLEMENTAÇÃO
        implementations: List[ImplementationResult] = []
        if self.enable_auto_implement and len(suggestions) > 0:
            logger.info("\n🔧 FASE 3: Implementando sugestões...")

            for i, suggestion in enumerate(suggestions, 1):
                logger.info(f"\n--- Sugestão {i}/{len(suggestions)} ---")
                logger.info(f"Title: {suggestion.title}")
                logger.info(f"Category: {suggestion.category.value}")
                logger.info(f"Priority: {suggestion.priority.value}")

                result = self.implementer.implement_suggestion(
                    suggestion=suggestion,
                    dry_run=dry_run,
                    force_approval=False  # NUNCA force approval
                )

                implementations.append(result)

                status_emoji = {
                    ImplementationStatus.SUCCESS: "✅",
                    ImplementationStatus.FAILED: "❌",
                    ImplementationStatus.AWAITING_APPROVAL: "⏳",
                    ImplementationStatus.ROLLED_BACK: "🔄"
                }
                emoji = status_emoji.get(result.status, "❓")
                logger.info(f"{emoji} Status: {result.status.value}")

        else:
            logger.info("\n⏸️ FASE 3: Auto-implementação DESABILITADA")
            logger.info("Para habilitar: Oraculo(enable_auto_implement=True)")

        # 4. RESULTADOS
        session_end = datetime.utcnow()
        duration = (session_end - session_start).total_seconds()

        impl_stats = self.implementer.get_stats() if implementations else {
            'successful': 0, 'failed': 0, 'awaiting_approval': 0
        }

        session = OraculoSession(
            session_id=session_id,
            timestamp=session_start,
            files_scanned=scan_stats['total_files'],
            suggestions_generated=len(suggestions),
            suggestions_implemented=impl_stats['successful'],
            suggestions_failed=impl_stats['failed'],
            suggestions_awaiting_approval=impl_stats['awaiting_approval'],
            total_files_modified=impl_stats.get('files_modified_total', 0),
            tests_passed=impl_stats.get('tests_passed', 0) > 0,
            duration_seconds=duration,
            focus_category=focus_category.value if focus_category else None
        )

        self.sessions.append(session)

        # RELATÓRIO FINAL
        self._display_session_report(session, suggestions, implementations)

        return session

    def _display_suggestions(self, suggestions: List[Suggestion]):
        """Exibe sugestões no console"""
        logger.info("\n" + "="*80)
        logger.info("💡 SUGESTÕES GERADAS")
        logger.info("="*80)

        for i, sugg in enumerate(suggestions, 1):
            priority_emoji = {
                SuggestionPriority.CRITICAL: "🔴",
                SuggestionPriority.HIGH: "🟠",
                SuggestionPriority.MEDIUM: "🟡",
                SuggestionPriority.LOW: "🟢"
            }
            emoji = priority_emoji.get(sugg.priority, "⚪")

            logger.info(f"\n{emoji} #{i} [{sugg.category.value.upper()}] {sugg.title}")
            logger.info(f"   Priority: {sugg.priority.value} | Confidence: {sugg.confidence_score:.2f} | Impact: {sugg.impact_score:.2f} | Effort: {sugg.effort_estimate_hours}h")
            logger.info(f"   {sugg.description}")
            logger.info(f"   Files: {', '.join(sugg.affected_files[:3])}")
            if len(sugg.affected_files) > 3:
                logger.info(f"   ... +{len(sugg.affected_files) - 3} more files")

    def _display_session_report(
        self,
        session: OraculoSession,
        suggestions: List[Suggestion],
        implementations: List[ImplementationResult]
    ):
        """Exibe relatório final da sessão"""
        logger.info("\n" + "="*80)
        logger.info("📊 RELATÓRIO FINAL - ORÁCULO SESSION")
        logger.info("="*80)
        logger.info(f"Session ID: {session.session_id}")
        logger.info(f"Duration: {session.duration_seconds:.2f}s")
        logger.info(f"\n📂 SCANNING:")
        logger.info(f"   Files scanned: {session.files_scanned}")
        logger.info(f"\n🧠 SUGGESTIONS:")
        logger.info(f"   Generated: {session.suggestions_generated}")
        logger.info(f"   Implemented: {session.suggestions_implemented}")
        logger.info(f"   Failed: {session.suggestions_failed}")
        logger.info(f"   Awaiting approval: {session.suggestions_awaiting_approval}")
        logger.info(f"\n🔧 IMPLEMENTATION:")
        logger.info(f"   Files modified: {session.total_files_modified}")
        logger.info(f"   Tests passed: {'✅ YES' if session.tests_passed else '❌ NO'}")

        if implementations:
            logger.info(f"\n📋 IMPLEMENTATION DETAILS:")
            for impl in implementations:
                status_emoji = {
                    ImplementationStatus.SUCCESS: "✅",
                    ImplementationStatus.FAILED: "❌",
                    ImplementationStatus.AWAITING_APPROVAL: "⏳",
                    ImplementationStatus.ROLLED_BACK: "🔄"
                }
                emoji = status_emoji.get(impl.status, "❓")
                logger.info(f"   {emoji} {impl.suggestion_id}: {impl.status.value}")
                if impl.error_message:
                    logger.info(f"      Error: {impl.error_message}")

        logger.info("\n" + "="*80)
        logger.info("🔮 ORÁCULO Session COMPLETO")
        logger.info("="*80)

    def get_pending_approvals(self) -> List[ImplementationResult]:
        """Retorna implementações aguardando aprovação"""
        return [
            impl for impl in self.implementer.implementations
            if impl.status == ImplementationStatus.AWAITING_APPROVAL
        ]

    def approve_implementation(self, suggestion_id: str) -> ImplementationResult:
        """
        Aprova uma implementação pendente

        Args:
            suggestion_id: ID da sugestão a aprovar

        Returns:
            Resultado da implementação
        """
        # Encontra sugestão pendente
        pending = [
            (impl, sugg) for impl in self.implementer.implementations
            for sugg in self.generator.suggestions_generated
            if impl.suggestion_id == suggestion_id and impl.status == ImplementationStatus.AWAITING_APPROVAL
        ]

        if not pending:
            logger.error(f"❌ Nenhuma implementação pendente com ID: {suggestion_id}")
            raise ValueError(f"No pending implementation with ID: {suggestion_id}")

        impl, suggestion = pending[0]

        logger.info(f"✅ Aprovação humana recebida para: {suggestion.title}")

        # Reimplementa com force_approval=True
        return self.implementer.implement_suggestion(
            suggestion=suggestion,
            dry_run=False,
            force_approval=True
        )

    def export_session_report(self, session_id: str, filepath: str):
        """
        Exporta relatório de sessão para JSON

        Args:
            session_id: ID da sessão
            filepath: Path do arquivo de saída
        """
        import json

        session = next((s for s in self.sessions if s.session_id == session_id), None)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        report = {
            'session': session.to_dict(),
            'suggestions': [
                s.to_dict() for s in self.generator.suggestions_generated
            ],
            'implementations': [
                impl.to_dict() for impl in self.implementer.implementations
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Relatório exportado: {filepath}")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais do Oráculo"""
        if not self.sessions:
            return {'total_sessions': 0}

        return {
            'total_sessions': len(self.sessions),
            'total_suggestions': sum(s.suggestions_generated for s in self.sessions),
            'total_implemented': sum(s.suggestions_implemented for s in self.sessions),
            'total_failed': sum(s.suggestions_failed for s in self.sessions),
            'total_files_modified': sum(s.total_files_modified for s in self.sessions),
            'avg_duration_seconds': sum(s.duration_seconds for s in self.sessions) / len(self.sessions),
            'latest_session': self.sessions[-1].to_dict() if self.sessions else None
        }


# Helper functions
def run_oraculo(
    focus_category: Optional[str] = None,
    dry_run: bool = True
) -> OraculoSession:
    """Helper para execução rápida do Oráculo"""
    oraculo = Oraculo(enable_auto_implement=True, enable_auto_commit=False)
    category = SuggestionCategory(focus_category) if focus_category else None
    return oraculo.run_self_improvement_cycle(
        focus_category=category,
        dry_run=dry_run
    )


if __name__ == "__main__":
    # Teste standalone
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*80)
    print("🔮 MAXIMUS ORÁCULO - Self-Improvement Engine")
    print("\"Pela Arte. Pela Sociedade.\"")
    print("="*80)

    # Cria instância do Oráculo
    oraculo = Oraculo(
        enable_auto_implement=True,
        enable_auto_commit=False,
        require_tests=False  # Desabilita testes para demo
    )

    # Roda ciclo de auto-melhoramento (DRY RUN)
    session = oraculo.run_self_improvement_cycle(
        focus_category=None,  # Todas as categorias
        max_suggestions=3,
        min_confidence=0.7,
        dry_run=True  # SIMULAÇÃO APENAS
    )

    # Exibe estatísticas finais
    print("\n\n📊 ESTATÍSTICAS DO ORÁCULO:")
    stats = oraculo.get_stats()
    print(f"Total de sessões: {stats['total_sessions']}")
    print(f"Total de sugestões: {stats['total_suggestions']}")
    print(f"Total implementadas: {stats['total_implemented']}")
    print(f"Duração média: {stats['avg_duration_seconds']:.2f}s")

    print("\n✅ Demo completo!")
    print("\nPara execução REAL (modifica arquivos):")
    print("  oraculo.run_self_improvement_cycle(dry_run=False)")
    print("\nPara habilitar commits automáticos:")
    print("  Oraculo(enable_auto_commit=True)")
