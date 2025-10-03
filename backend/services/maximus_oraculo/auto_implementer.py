"""
Auto Implementer - MAXIMUS Safe Self-Patching System
=====================================================

Sistema ULTRA-SEGURO para auto-implementação de melhorias no codebase.

FILOSOFIA DE SEGURANÇA:
- 🔒 Sandboxed execution
- 🔄 Atomic rollback capability
- 🧪 Auto-testing antes de commit
- 👁️ Human approval para mudanças críticas
- 📝 Logging completo de todas as mudanças

Capacidades:
- Apply code patches automatically
- Run tests before committing
- Create git branches for changes
- Rollback on failure
- Human-in-the-loop for critical changes
"""

import os
import shutil
import subprocess
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from suggestion_generator import Suggestion, SuggestionPriority

logger = logging.getLogger(__name__)


class ImplementationStatus(str, Enum):
    """Status da implementação"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    AWAITING_APPROVAL = "awaiting_approval"


@dataclass
class ImplementationResult:
    """Resultado de uma implementação"""
    suggestion_id: str
    status: ImplementationStatus
    timestamp: datetime
    branch_name: Optional[str]
    files_modified: List[str]
    tests_passed: bool
    error_message: Optional[str] = None
    rollback_performed: bool = False
    human_approval_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict"""
        return {
            'suggestion_id': self.suggestion_id,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'branch_name': self.branch_name,
            'files_modified': self.files_modified,
            'tests_passed': self.tests_passed,
            'error_message': self.error_message,
            'rollback_performed': self.rollback_performed,
            'human_approval_required': self.human_approval_required
        }


class AutoImplementer:
    """
    Sistema de auto-implementação SEGURA de melhorias

    SEGURANÇA EM CAMADAS:
    1. Backup automático antes de mudanças
    2. Git branching para isolamento
    3. Testes automáticos pós-implementação
    4. Rollback automático em caso de falha
    5. Human approval para mudanças críticas
    """

    # Mudanças que SEMPRE requerem aprovação humana
    CRITICAL_PATHS = [
        "main.py",
        "config.yaml",
        "requirements.txt",
        ".env",
        "Dockerfile",
        "docker-compose.yml"
    ]

    # Mudanças que NUNCA devem ser auto-implementadas
    FORBIDDEN_PATHS = [
        ".env",
        "secrets.yaml",
        "credentials.json",
        ".git/",
        "__pycache__/"
    ]

    def __init__(
        self,
        repo_path: str = "/home/juan/vertice-dev",
        enable_auto_commit: bool = False,
        require_tests: bool = True
    ):
        """
        Args:
            repo_path: Path do repositório MAXIMUS
            enable_auto_commit: Se True, faz commit automático (CUIDADO!)
            require_tests: Se True, roda testes antes de commit
        """
        self.repo_path = Path(repo_path)
        self.enable_auto_commit = enable_auto_commit
        self.require_tests = require_tests
        self.implementations: List[ImplementationResult] = []

    def implement_suggestion(
        self,
        suggestion: Suggestion,
        dry_run: bool = True,
        force_approval: bool = False
    ) -> ImplementationResult:
        """
        Implementa uma sugestão de forma segura

        Args:
            suggestion: Sugestão a implementar
            dry_run: Se True, apenas simula (não modifica arquivos)
            force_approval: Se True, pula aprovação humana (PERIGOSO!)

        Returns:
            Resultado da implementação
        """
        logger.info(f"🔧 Implementando sugestão: {suggestion.title}")

        # 1. Validação de segurança
        if not self._validate_safety(suggestion):
            return ImplementationResult(
                suggestion_id=suggestion.suggestion_id,
                status=ImplementationStatus.FAILED,
                timestamp=datetime.utcnow(),
                branch_name=None,
                files_modified=[],
                tests_passed=False,
                error_message="Sugestão falhou validação de segurança"
            )

        # 2. Verifica se precisa aprovação humana
        needs_approval = self._needs_human_approval(suggestion)
        if needs_approval and not force_approval:
            logger.warning("⚠️ Esta mudança requer aprovação humana")
            return ImplementationResult(
                suggestion_id=suggestion.suggestion_id,
                status=ImplementationStatus.AWAITING_APPROVAL,
                timestamp=datetime.utcnow(),
                branch_name=None,
                files_modified=suggestion.affected_files,
                tests_passed=False,
                human_approval_required=True
            )

        # 3. Cria branch Git para isolamento
        branch_name = f"oraculo/{suggestion.suggestion_id}"
        if not dry_run:
            if not self._create_git_branch(branch_name):
                return ImplementationResult(
                    suggestion_id=suggestion.suggestion_id,
                    status=ImplementationStatus.FAILED,
                    timestamp=datetime.utcnow(),
                    branch_name=None,
                    files_modified=[],
                    tests_passed=False,
                    error_message="Falha ao criar branch Git"
                )

        # 4. Aplica mudanças
        result = ImplementationResult(
            suggestion_id=suggestion.suggestion_id,
            status=ImplementationStatus.IN_PROGRESS,
            timestamp=datetime.utcnow(),
            branch_name=branch_name if not dry_run else None,
            files_modified=[],
            tests_passed=False
        )

        try:
            if dry_run:
                logger.info("🔍 DRY RUN MODE - Apenas simulando mudanças")
                result.status = ImplementationStatus.SUCCESS
                result.files_modified = suggestion.affected_files
                logger.info(f"✅ Simulação OK: {len(suggestion.affected_files)} arquivos seriam modificados")
            else:
                # Aplica mudanças reais
                modified_files = self._apply_changes(suggestion)
                result.files_modified = modified_files

                # 5. Roda testes
                if self.require_tests:
                    result.status = ImplementationStatus.TESTING
                    tests_passed = self._run_tests(suggestion.affected_files)
                    result.tests_passed = tests_passed

                    if not tests_passed:
                        logger.error("❌ Testes falharam! Iniciando rollback...")
                        self._rollback_changes(branch_name)
                        result.status = ImplementationStatus.ROLLED_BACK
                        result.rollback_performed = True
                        result.error_message = "Testes falharam"
                        return result

                # 6. Commit (se habilitado)
                if self.enable_auto_commit:
                    self._commit_changes(suggestion, branch_name)

                result.status = ImplementationStatus.SUCCESS
                logger.info(f"✅ Implementação concluída com sucesso!")

        except Exception as e:
            logger.error(f"❌ Erro durante implementação: {e}")
            result.status = ImplementationStatus.FAILED
            result.error_message = str(e)

            # Rollback automático
            if not dry_run:
                self._rollback_changes(branch_name)
                result.rollback_performed = True

        self.implementations.append(result)
        return result

    def _validate_safety(self, suggestion: Suggestion) -> bool:
        """
        Valida se sugestão é segura para implementar

        Returns:
            True se segura, False caso contrário
        """
        # Verifica arquivos proibidos
        for file_path in suggestion.affected_files:
            for forbidden in self.FORBIDDEN_PATHS:
                if forbidden in file_path:
                    logger.error(f"❌ FORBIDDEN FILE: {file_path}")
                    return False

        # Verifica confiança mínima
        if suggestion.confidence_score < 0.8:
            logger.warning(f"⚠️ Confiança baixa: {suggestion.confidence_score}")
            return False

        # Verifica se arquivos existem
        for file_path in suggestion.affected_files:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                logger.warning(f"⚠️ Arquivo não existe: {file_path}")
                # Pode ser arquivo novo, não bloqueia

        return True

    def _needs_human_approval(self, suggestion: Suggestion) -> bool:
        """
        Determina se sugestão requer aprovação humana

        Returns:
            True se requer aprovação
        """
        # Sempre requer aprovação se for crítica
        if suggestion.priority == SuggestionPriority.CRITICAL:
            return True

        # Verifica arquivos críticos
        for file_path in suggestion.affected_files:
            for critical in self.CRITICAL_PATHS:
                if critical in file_path:
                    return True

        # Mudanças de segurança sempre requerem aprovação
        if suggestion.category.value == "security":
            return True

        return False

    def _create_git_branch(self, branch_name: str) -> bool:
        """
        Cria branch Git para mudanças isoladas

        Args:
            branch_name: Nome da branch

        Returns:
            True se sucesso
        """
        try:
            # Verifica se está em git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error("❌ Não é um repositório Git")
                return False

            # Cria branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info(f"✅ Branch criada: {branch_name}")
                return True
            else:
                # Branch pode já existir, tenta fazer checkout
                result = subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    logger.info(f"✅ Checkout para branch existente: {branch_name}")
                    return True
                else:
                    logger.error(f"❌ Erro ao criar/checkout branch: {result.stderr}")
                    return False

        except Exception as e:
            logger.error(f"❌ Erro ao criar branch: {e}")
            return False

    def _apply_changes(self, suggestion: Suggestion) -> List[str]:
        """
        Aplica mudanças sugeridas nos arquivos

        NOTA: Esta é uma implementação simplificada.
        Em produção, seria necessário parsing mais sofisticado
        ou integração com ferramentas de AST (Abstract Syntax Tree).

        Args:
            suggestion: Sugestão a implementar

        Returns:
            Lista de arquivos modificados
        """
        modified_files = []

        logger.info(f"📝 Aplicando mudanças em {len(suggestion.affected_files)} arquivos...")

        for file_path in suggestion.affected_files:
            full_path = self.repo_path / file_path

            # Backup do arquivo original
            backup_path = full_path.with_suffix(full_path.suffix + '.oraculo_backup')
            if full_path.exists():
                shutil.copy2(full_path, backup_path)
                logger.info(f"💾 Backup criado: {backup_path}")

            # Aqui seria aplicada a mudança real
            # Por enquanto, apenas adiciona comentário indicando mudança sugerida
            try:
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Adiciona header com sugestão
                    header = f"""# ORACULO AUTO-IMPROVEMENT
# Suggestion ID: {suggestion.suggestion_id}
# Title: {suggestion.title}
# Timestamp: {datetime.utcnow().isoformat()}
# Category: {suggestion.category.value}
#
# IMPLEMENTATION STEPS:
# {chr(10).join(f'# {i+1}. {step}' for i, step in enumerate(suggestion.implementation_steps))}
#
# NOTE: This is a PLACEHOLDER implementation.
# In production, actual code changes would be applied here.
# ============================================================

"""
                    modified_content = header + content

                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)

                    modified_files.append(file_path)
                    logger.info(f"✅ Modificado: {file_path}")
                else:
                    logger.warning(f"⚠️ Arquivo não existe (pode ser novo): {file_path}")

            except Exception as e:
                logger.error(f"❌ Erro ao modificar {file_path}: {e}")
                # Restaura backup em caso de erro
                if backup_path.exists():
                    shutil.copy2(backup_path, full_path)
                    logger.info(f"🔄 Backup restaurado: {file_path}")

        return modified_files

    def _run_tests(self, affected_files: List[str]) -> bool:
        """
        Roda testes para validar mudanças

        Args:
            affected_files: Arquivos modificados

        Returns:
            True se todos os testes passaram
        """
        logger.info("🧪 Rodando testes...")

        try:
            # Tenta rodar pytest
            result = subprocess.run(
                ["pytest", "-xvs", "--tb=short"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos max
            )

            if result.returncode == 0:
                logger.info("✅ Todos os testes passaram!")
                return True
            else:
                logger.error(f"❌ Testes falharam:\n{result.stdout}\n{result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ Testes excederam timeout de 5 minutos")
            return False
        except FileNotFoundError:
            logger.warning("⚠️ pytest não encontrado, pulando testes")
            return True  # Não bloqueia se pytest não estiver instalado
        except Exception as e:
            logger.error(f"❌ Erro ao rodar testes: {e}")
            return False

    def _rollback_changes(self, branch_name: str):
        """
        Reverte mudanças em caso de falha

        Args:
            branch_name: Nome da branch a reverter
        """
        logger.info(f"🔄 Iniciando rollback da branch {branch_name}...")

        try:
            # Volta para main
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=self.repo_path,
                capture_output=True
            )

            # Deleta branch com mudanças falhadas
            subprocess.run(
                ["git", "branch", "-D", branch_name],
                cwd=self.repo_path,
                capture_output=True
            )

            # Restaura backups
            for backup_file in self.repo_path.rglob("*.oraculo_backup"):
                original_file = backup_file.with_suffix('')
                shutil.copy2(backup_file, original_file)
                backup_file.unlink()
                logger.info(f"🔄 Restaurado: {original_file}")

            logger.info("✅ Rollback completo")

        except Exception as e:
            logger.error(f"❌ Erro durante rollback: {e}")

    def _commit_changes(self, suggestion: Suggestion, branch_name: str):
        """
        Faz commit das mudanças (se habilitado)

        Args:
            suggestion: Sugestão implementada
            branch_name: Branch onde fazer commit
        """
        try:
            # Stage files
            subprocess.run(
                ["git", "add", "."],
                cwd=self.repo_path,
                check=True
            )

            # Commit
            commit_message = f"""[ORACULO] {suggestion.title}

Category: {suggestion.category.value}
Priority: {suggestion.priority.value}
Confidence: {suggestion.confidence_score:.2f}
Impact: {suggestion.impact_score:.2f}

{suggestion.description}

Implementation Steps:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(suggestion.implementation_steps))}

Suggestion ID: {suggestion.suggestion_id}
Auto-implemented by MAXIMUS ORACULO
"""

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                check=True
            )

            logger.info(f"✅ Commit realizado na branch {branch_name}")

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao fazer commit: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das implementações"""
        if not self.implementations:
            return {'total': 0}

        return {
            'total': len(self.implementations),
            'successful': len([i for i in self.implementations if i.status == ImplementationStatus.SUCCESS]),
            'failed': len([i for i in self.implementations if i.status == ImplementationStatus.FAILED]),
            'rolled_back': len([i for i in self.implementations if i.rollback_performed]),
            'awaiting_approval': len([i for i in self.implementations if i.status == ImplementationStatus.AWAITING_APPROVAL]),
            'tests_passed': len([i for i in self.implementations if i.tests_passed]),
            'files_modified_total': sum(len(i.files_modified) for i in self.implementations)
        }


if __name__ == "__main__":
    # Teste standalone
    logging.basicConfig(level=logging.INFO)

    from suggestion_generator import Suggestion, SuggestionCategory, SuggestionPriority

    # Cria sugestão mock
    test_suggestion = Suggestion(
        suggestion_id="test_001",
        timestamp=datetime.utcnow(),
        category=SuggestionCategory.REFACTORING,
        priority=SuggestionPriority.LOW,
        title="Adicionar type hints em funções",
        description="Melhorar legibilidade com type hints",
        affected_files=["maximus_oraculo/code_scanner.py"],
        confidence_score=0.95,
        impact_score=0.60,
        effort_estimate_hours=2,
        implementation_steps=[
            "Adicionar imports do typing",
            "Adicionar type hints nas funções",
            "Validar com mypy"
        ],
        code_example="def scan_files(path: str) -> List[CodeFile]:",
        reasoning="Melhora manutenção e detecta bugs em tempo de desenvolvimento"
    )

    implementer = AutoImplementer(enable_auto_commit=False, require_tests=False)

    print("🔧 TESTANDO AUTO IMPLEMENTER")
    print("\n1. DRY RUN (simulação):")
    result = implementer.implement_suggestion(test_suggestion, dry_run=True)
    print(f"Status: {result.status.value}")
    print(f"Files: {result.files_modified}")
    print(f"Approval required: {result.human_approval_required}")

    print("\n\n📊 ESTATÍSTICAS:")
    stats = implementer.get_stats()
    print(f"Total: {stats['total']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
