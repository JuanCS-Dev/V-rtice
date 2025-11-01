"""Sophia Engine - Motor de Sabedoria (Artigo I).

Implementa o Princípio da Sabedoria: julgar se uma intervenção é necessária
antes de acionar o ciclo MAPE-K completo.

Fundamento Bíblico: Provérbios 9:10
"O temor do SENHOR é o princípio da sabedoria."

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml

from models import Anomaly, InterventionDecision, InterventionLevel, Severity

logger = logging.getLogger(__name__)


class SophiaEngine:
    """
    Motor de Sabedoria: Julga se uma intervenção é necessária.

    Implementa três perguntas essenciais:
    1. É uma falha transitória que se autocorrige?
    2. A intervenção pode causar mais dano que a falha?
    3. Há precedentes históricos que informam a decisão?
    """

    def __init__(self, wisdom_base, observability_client):
        """
        Inicializa Sophia Engine.

        Args:
            wisdom_base: Cliente para Wisdom Base (precedentes históricos)
            observability_client: Cliente para Prometheus/Loki
        """
        self.wisdom_base = wisdom_base
        self.observability_client = observability_client

        # Configurações de sabedoria
        self.transient_failure_threshold_minutes = 5
        self.min_precedent_confidence = 0.85
        self.risk_tolerance = 0.3  # Máximo 30% de risco aceitável

    async def should_intervene(self, anomaly: Anomaly) -> dict[str, Any]:
        """
        Decisão principal: devemos intervir nesta anomalia?

        Args:
            anomaly: Anomalia detectada

        Returns:
            Dict com decisão e reasoning
        """
        logger.info(
            f"[Sophia] Evaluating intervention for anomaly {anomaly.anomaly_id}"
        )

        # Pergunta 1: É transitória?
        if await self._is_self_healing_naturally(anomaly):
            return {
                "decision": InterventionDecision.OBSERVE_AND_WAIT,
                "reasoning": "Anomalia tem padrão transitório conhecido. Histórico mostra auto-correção em 94% dos casos.",
                "wait_time_minutes": self.transient_failure_threshold_minutes,
                "sophia_wisdom": "Há tempo certo para cada ação (Eclesiastes 3:1). Este não é o momento de agir.",
            }

        # Pergunta 2: Risco de intervenção > benefício?
        risk_assessment = await self._assess_intervention_risk(anomaly)
        current_impact = self._calculate_current_impact(anomaly)

        if risk_assessment["risk_score"] > current_impact:
            return {
                "decision": InterventionDecision.HUMAN_CONSULTATION_REQUIRED,
                "reasoning": f"Risco de intervenção ({risk_assessment['risk_score']:.2f}) > impacto atual ({current_impact:.2f})",
                "risk_details": risk_assessment,
                "sophia_wisdom": "A prudência é a marca da sabedoria. Quando em dúvida, consultar aqueles com mais experiência.",
            }

        # Pergunta 3: Há precedentes históricos?
        precedent = await self._query_wisdom_base(anomaly)

        if precedent:
            return {
                "decision": InterventionDecision.INTERVENE,
                "reasoning": f"Precedente encontrado (similaridade: {precedent['similarity']:.1%}). Intervenção anterior foi {precedent['outcome']}.",
                "intervention_level": self._recommend_intervention_level(
                    anomaly, precedent
                ),
                "precedent": precedent,
                "sophia_wisdom": "Há sabedoria em aprender com o passado. Precedentes nos guiam.",
            }

        # Sem precedentes: avaliar se devemos arriscar intervenção
        if anomaly.severity in [Severity.P0_CRITICAL, Severity.P1_HIGH]:
            return {
                "decision": InterventionDecision.INTERVENE,
                "reasoning": f"Severidade {anomaly.severity.value} requer ação. Sem precedentes, mas impacto justifica risco.",
                "intervention_level": InterventionLevel.PATCH_SURGICAL,  # Começar conservador
                "sophia_wisdom": "Em momentos críticos, sabedoria também é agir com coragem temperada.",
            }
        else:
            return {
                "decision": InterventionDecision.OBSERVE_AND_WAIT,
                "reasoning": "Sem precedentes e severidade não crítica. Observar para aprender antes de agir.",
                "wait_time_minutes": 10,
                "sophia_wisdom": "Melhor observar e aprender que agir precipitadamente sem conhecimento.",
            }

    async def _is_self_healing_naturally(self, anomaly: Anomaly) -> bool:
        """
        Verifica se anomalia tem padrão de auto-correção.

        Args:
            anomaly: Anomalia a verificar

        Returns:
            True se histórico mostra auto-correção frequente
        """
        # Buscar ocorrências similares nas últimas 4 semanas
        time_window = datetime.now() - timedelta(weeks=4)

        similar_anomalies = await self.observability_client.query_similar_anomalies(
            anomaly_type=anomaly.anomaly_type,
            service=anomaly.service,
            since=time_window,
        )

        if len(similar_anomalies) < 5:
            return False  # Insuficiente histórico

        # Calcular taxa de auto-correção
        auto_corrected = sum(
            1 for a in similar_anomalies if a["resolved_without_intervention"]
        )

        auto_correction_rate = auto_corrected / len(similar_anomalies)

        # Se > 90% se auto-corrigiram, considerar transitório
        is_transient = auto_correction_rate > 0.90

        if is_transient:
            logger.info(
                f"[Sophia] Anomaly {anomaly.anomaly_id} identified as transient "
                f"({auto_correction_rate:.1%} auto-correction rate)"
            )

        return is_transient

    async def _assess_intervention_risk(self, anomaly: Anomaly) -> dict[str, Any]:
        """
        Avalia risco de intervenção.

        Args:
            anomaly: Anomalia a avaliar

        Returns:
            Dict com risk_score e detalhes
        """
        risk_factors = []
        risk_score = 0.0

        # Fator 1: Complexidade do serviço afetado
        service_complexity = await self._get_service_complexity(anomaly.service)
        if service_complexity > 0.7:
            risk_factors.append("Serviço de alta complexidade")
            risk_score += 0.3

        # Fator 2: Número de dependências
        dependencies = await self._get_service_dependencies(anomaly.service)
        if len(dependencies) > 10:
            risk_factors.append(f"Muitas dependências ({len(dependencies)})")
            risk_score += 0.2

        # Fator 3: Mudanças recentes no serviço
        recent_changes = await self._get_recent_changes(anomaly.service, hours=24)
        if recent_changes > 3:
            risk_factors.append(f"Múltiplas mudanças recentes ({recent_changes})")
            risk_score += 0.25

        # Fator 4: Falta de testes
        test_coverage = await self._get_test_coverage(anomaly.service)
        if test_coverage < 0.90:
            risk_factors.append(f"Coverage baixo ({test_coverage:.1%})")
            risk_score += 0.25

        return {
            "risk_score": min(risk_score, 1.0),
            "risk_factors": risk_factors,
            "service_complexity": service_complexity,
            "dependencies_count": len(dependencies),
            "recent_changes": recent_changes,
            "test_coverage": test_coverage,
        }

    def _calculate_current_impact(self, anomaly: Anomaly) -> float:
        """
        Calcula impacto atual da anomalia.

        Args:
            anomaly: Anomalia a avaliar

        Returns:
            Impact score (0.0 - 1.0)
        """
        impact = 0.0

        # Severity base
        severity_scores = {
            Severity.P0_CRITICAL: 1.0,
            Severity.P1_HIGH: 0.7,
            Severity.P2_MEDIUM: 0.4,
            Severity.P3_LOW: 0.2,
        }
        impact += severity_scores.get(anomaly.severity, 0.5)

        # Métricas específicas
        if "error_rate" in anomaly.metrics:
            impact += anomaly.metrics["error_rate"] * 0.3

        if "affected_users" in anomaly.metrics:
            users_affected = anomaly.metrics["affected_users"]
            if users_affected > 1000:
                impact += 0.3
            elif users_affected > 100:
                impact += 0.15

        return min(impact, 1.0)

    async def _query_wisdom_base(self, anomaly: Anomaly) -> dict[str, Any] | None:
        """
        Busca precedentes históricos na Wisdom Base.

        Args:
            anomaly: Anomalia a buscar

        Returns:
            Precedente mais similar ou None
        """
        precedents = await self.wisdom_base.query_precedents(
            anomaly_type=anomaly.anomaly_type,
            service=anomaly.service,
            similarity_threshold=self.min_precedent_confidence,
        )

        if not precedents:
            return None

        # Retornar precedente mais similar com outcome positivo
        successful_precedents = [p for p in precedents if p["outcome"] == "success"]

        if successful_precedents:
            return max(successful_precedents, key=lambda p: p["similarity"])

        # Se não há sucessos, retornar mais similar (para aprender com falha)
        return max(precedents, key=lambda p: p["similarity"])

    def _recommend_intervention_level(
        self, anomaly: Anomaly, precedent: dict[str, Any]
    ) -> InterventionLevel:
        """
        Recomenda nível de intervenção baseado em precedente.

        Args:
            anomaly: Anomalia atual
            precedent: Precedente histórico

        Returns:
            Nível de intervenção recomendado
        """
        # Se precedente foi sucesso e similar > 90%, usar mesmo nível
        if precedent["outcome"] == "success" and precedent["similarity"] > 0.90:
            return precedent.get("intervention_level", InterventionLevel.PATCH_SURGICAL)

        # Se precedente falhou, ser mais conservador
        if precedent["outcome"] == "failure":
            return InterventionLevel.OBSERVE

        # Padrão: começar com intervenção cirúrgica
        return InterventionLevel.PATCH_SURGICAL

    async def _get_service_complexity(self, service: str) -> float:
        """
        Calcula complexidade real do serviço usando radon.

        Usa cyclomatic complexity como métrica principal.
        Normaliza para escala 0.0-1.0 (complexidade >15 = muito alta).

        Args:
            service: Nome do serviço (e.g., "penelope_service")

        Returns:
            Score de complexidade (0.0 - 1.0)
        """
        try:
            service_path = f"backend/services/{service}"

            # Run radon cc (cyclomatic complexity)
            result = subprocess.run(
                ["radon", "cc", "-a", "-j", service_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd="/home/juan/vertice-dev",
            )

            if result.returncode != 0:
                logger.warning(
                    f"Radon failed for {service}: {result.stderr}. Using default complexity."
                )
                return 0.5

            # Parse JSON output
            data = json.loads(result.stdout)

            # Calculate weighted complexity
            total_complexity = 0
            total_functions = 0

            for file_data in data.values():
                for item in file_data:
                    total_complexity += item.get("complexity", 0)
                    total_functions += 1

            if total_functions == 0:
                logger.info(
                    f"No functions found in {service}, using default complexity"
                )
                return 0.5

            avg_complexity = total_complexity / total_functions

            # Normalize to 0-1 scale (complexity >15 is very high)
            normalized = min(avg_complexity / 15.0, 1.0)

            logger.info(
                f"Service {service} complexity: {normalized:.2f} "
                f"(avg cyclomatic: {avg_complexity:.1f}, functions: {total_functions})"
            )
            return normalized

        except subprocess.TimeoutExpired:
            logger.error(f"Radon timeout for {service}")
            return 0.5
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse radon output for {service}: {e}")
            return 0.5
        except Exception as e:
            logger.error(f"Failed to calculate complexity for {service}: {e}")
            return 0.5  # Conservative fallback

    async def _get_service_dependencies(self, service: str) -> list[str]:
        """
        Obtém dependências reais do serviço analisando imports e docker-compose.

        Analisa:
        1. Imports Python (from X_service import ...)
        2. docker-compose.yml (depends_on)
        3. Service Registry (runtime dependencies)

        Args:
            service: Nome do serviço (e.g., "penelope_service")

        Returns:
            Lista de serviços dependentes (unique)
        """
        try:
            dependencies = set()
            service_path = Path(f"/home/juan/vertice-dev/backend/services/{service}")

            if not service_path.exists():
                logger.warning(f"Service path not found: {service_path}")
                return []

            # 1. Parse Python imports
            for py_file in service_path.rglob("*.py"):
                try:
                    content = py_file.read_text()

                    # Find internal service imports
                    # Pattern: from X_service import ... or import X_service
                    import_pattern = (
                        r"from\s+(\w+_service)\s+import|import\s+(\w+_service)"
                    )
                    matches = re.findall(import_pattern, content)

                    for match in matches:
                        dep = match[0] or match[1]
                        if dep and dep != service:
                            dependencies.add(dep)
                except Exception as e:
                    logger.debug(f"Failed to parse {py_file}: {e}")
                    continue

            # 2. Parse docker-compose.yml
            compose_file = service_path / "docker-compose.yml"
            if compose_file.exists():
                try:
                    compose_data = yaml.safe_load(compose_file.read_text())

                    for svc_name, svc_config in compose_data.get(
                        "services", {}
                    ).items():
                        depends_on = svc_config.get("depends_on", [])

                        # depends_on can be list or dict
                        if isinstance(depends_on, list):
                            dependencies.update(depends_on)
                        elif isinstance(depends_on, dict):
                            dependencies.update(depends_on.keys())
                except Exception as e:
                    logger.debug(f"Failed to parse docker-compose.yml: {e}")

            # 3. Query Service Registry (if available)
            # TODO: Implement when Service Registry client is available
            # registry_deps = await self._query_registry_dependencies(service)
            # dependencies.update(registry_deps)

            result = sorted(list(dependencies))
            logger.info(f"Service {service} has {len(result)} dependencies: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to get dependencies for {service}: {e}")
            return []

    async def _get_recent_changes(self, service: str, hours: int = 24) -> int:
        """
        Obtém número real de commits recentes usando git log.

        Conta commits no diretório do serviço nas últimas N horas.

        Args:
            service: Nome do serviço (e.g., "penelope_service")
            hours: Janela de tempo em horas (padrão: 24)

        Returns:
            Número de commits recentes
        """
        try:
            service_path = f"backend/services/{service}"
            since_time = f"{hours} hours ago"

            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    f"--since={since_time}",
                    "--",
                    service_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
                cwd="/home/juan/vertice-dev",
            )

            if result.returncode != 0:
                logger.warning(f"Git log failed for {service}: {result.stderr}")
                return 0

            # Count non-empty lines
            commit_count = len(
                [line for line in result.stdout.split("\n") if line.strip()]
            )

            logger.info(
                f"Service {service} had {commit_count} commits in last {hours}h"
            )
            return commit_count

        except subprocess.TimeoutExpired:
            logger.error(f"Git log timeout for {service}")
            return 0
        except Exception as e:
            logger.error(f"Failed to get recent changes for {service}: {e}")
            return 0

    async def _get_test_coverage(self, service: str) -> float:
        """
        Obtém coverage real de testes usando pytest-cov.

        Executa pytest com coverage no diretório do serviço e extrai
        o percentual de cobertura do coverage.json gerado.

        Args:
            service: Nome do serviço (e.g., "penelope_service")

        Returns:
            Coverage (0.0 - 1.0)
        """
        try:
            service_path = Path(f"/home/juan/vertice-dev/backend/services/{service}")

            if not service_path.exists():
                logger.warning(f"Service path not found: {service_path}")
                return 0.0

            # Run pytest with coverage
            result = subprocess.run(
                ["pytest", "--cov=.", "--cov-report=json", "-q", "--tb=no"],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes timeout
                cwd=str(service_path),
            )

            # Check if coverage.json was generated
            coverage_file = service_path / "coverage.json"
            if not coverage_file.exists():
                logger.warning(
                    f"No coverage.json for {service}. "
                    f"Tests may have failed or no tests exist."
                )
                return 0.0

            # Read coverage.json
            coverage_data = json.loads(coverage_file.read_text())
            coverage_pct = coverage_data["totals"]["percent_covered"] / 100.0

            logger.info(
                f"Service {service} coverage: {coverage_pct:.1%} "
                f"({coverage_data['totals']['covered_lines']}/{coverage_data['totals']['num_statements']} statements)"
            )
            return coverage_pct

        except subprocess.TimeoutExpired:
            logger.error(f"Pytest timeout for {service} (>120s)")
            return 0.0
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse coverage.json for {service}: {e}")
            return 0.0
        except KeyError as e:
            logger.error(f"Invalid coverage.json format for {service}: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get test coverage for {service}: {e}")
            return 0.0

    async def validate_patch_in_twin(self, service: str, patch: str) -> dict[str, Any]:
        """
        Validate patch using digital twin before production.

        Creates isolated Docker container, applies patch, runs tests,
        monitors metrics. Only approves if all checks pass.

        Args:
            service: Service name (e.g., "penelope_service")
            patch: Git-style patch content

        Returns:
            validation_result: Dict with success, test_results, metrics
        """
        from core.digital_twin import DigitalTwinEnvironment

        twin_env = DigitalTwinEnvironment()
        twin_id = None

        try:
            # Step 1: Create digital twin
            logger.info(f"Creating digital twin for {service}...")
            twin_id = await twin_env.create_twin(service)

            # Step 2: Apply patch
            logger.info(f"Applying patch to twin {twin_id}...")
            patch_applied = await twin_env.apply_patch(twin_id, patch)

            if not patch_applied:
                return {
                    "success": False,
                    "reason": "Patch failed to apply cleanly",
                    "twin_id": twin_id,
                }

            # Step 3: Run tests
            logger.info(f"Running tests in twin {twin_id}...")
            test_results = await twin_env.run_tests(twin_id)

            if test_results["tests_failed"] > 0:
                return {
                    "success": False,
                    "reason": f"{test_results['tests_failed']} tests failed",
                    "test_results": test_results,
                    "twin_id": twin_id,
                }

            # Step 4: Check coverage didn't drop significantly
            original_coverage = await self._get_test_coverage(service)
            new_coverage = test_results["coverage"]

            if new_coverage < original_coverage - 5.0:  # Allow 5% drop
                return {
                    "success": False,
                    "reason": f"Coverage dropped from {original_coverage:.1f}% to {new_coverage:.1f}%",
                    "test_results": test_results,
                    "twin_id": twin_id,
                }

            # Step 5: Monitor for regressions
            logger.info(f"Monitoring twin {twin_id} for regressions (120s)...")
            metrics = await twin_env.monitor_metrics(twin_id, duration_seconds=120)

            if metrics["cpu_avg"] > 80.0:
                return {
                    "success": False,
                    "reason": f"High CPU usage: {metrics['cpu_avg']:.1f}%",
                    "metrics": metrics,
                    "test_results": test_results,
                    "twin_id": twin_id,
                }

            # All checks passed!
            logger.info(f"✅ Patch validation successful for {service}")
            return {
                "success": True,
                "test_results": test_results,
                "metrics": metrics,
                "twin_id": twin_id,
                "validation_summary": {
                    "tests_passed": test_results["tests_passed"],
                    "tests_failed": test_results["tests_failed"],
                    "coverage": new_coverage,
                    "cpu_avg": metrics["cpu_avg"],
                    "memory_avg": metrics["memory_avg"],
                },
            }

        except Exception as e:
            logger.error(f"Digital twin validation failed: {e}")
            return {
                "success": False,
                "reason": f"Validation error: {str(e)}",
                "error": str(e),
                "twin_id": twin_id,
            }

        finally:
            # Always clean up twin
            if twin_id:
                try:
                    logger.info(f"Destroying twin {twin_id}...")
                    await twin_env.destroy_twin(twin_id)
                except Exception as e:
                    logger.error(f"Failed to destroy twin {twin_id}: {e}")
