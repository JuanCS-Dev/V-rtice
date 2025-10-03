"""
Tool Orchestrator - Parallel Execution & Smart Validation
==========================================================

Sistema inteligente para:
1. Execução paralela de múltiplas tools
2. Validação de resultados
3. Retry logic inteligente
4. Error recovery
5. Result caching
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib


class ExecutionStatus(str, Enum):
    """Status de execução de tool"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CACHED = "cached"


class ValidationLevel(str, Enum):
    """Nível de validação de resultado"""
    NONE = "none"       # Sem validação
    BASIC = "basic"     # Validação básica (tipo, estrutura)
    STRICT = "strict"   # Validação rigorosa (conteúdo, consistência)


@dataclass
class ToolExecution:
    """Representa execução de uma tool"""
    tool_name: str
    tool_input: Dict[str, Any]
    executor: Callable
    priority: int = 5  # 1-10, quanto maior mais prioritário
    timeout: int = 30  # segundos
    retry_count: int = 0
    max_retries: int = 2
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    execution_time_ms: Optional[int] = None
    cached: bool = False


@dataclass
class ValidationResult:
    """Resultado de validação"""
    valid: bool
    confidence: float  # 0-1
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResultCache:
    """
    Cache de resultados de tools para evitar execuções redundantes.
    """

    def __init__(self, ttl_seconds: int = 300):  # 5 minutos
        self.cache: Dict[str, Tuple[Dict, datetime]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)
        self.hits = 0
        self.misses = 0

    def _make_key(self, tool_name: str, tool_input: Dict) -> str:
        """Cria chave de cache baseada em tool + input"""
        input_str = json.dumps(tool_input, sort_keys=True)
        hash_val = hashlib.md5(f"{tool_name}:{input_str}".encode()).hexdigest()
        return hash_val

    def get(self, tool_name: str, tool_input: Dict) -> Optional[Dict]:
        """Busca resultado no cache"""
        key = self._make_key(tool_name, tool_input)

        if key in self.cache:
            result, timestamp = self.cache[key]

            # Verifica se não expirou
            if datetime.now() - timestamp < self.ttl:
                self.hits += 1
                return result
            else:
                # Expirado, remove
                del self.cache[key]

        self.misses += 1
        return None

    def set(self, tool_name: str, tool_input: Dict, result: Dict):
        """Armazena resultado no cache"""
        key = self._make_key(tool_name, tool_input)
        self.cache[key] = (result, datetime.now())

    def clear(self):
        """Limpa cache"""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        hit_rate = (self.hits / (self.hits + self.misses) * 100) if (self.hits + self.misses) > 0 else 0

        return {
            "entries": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "ttl_seconds": self.ttl.total_seconds()
        }


class ToolOrchestrator:
    """
    Orquestrador de tools com execução paralela e validação.
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        enable_cache: bool = True,
        cache_ttl: int = 300,
        default_timeout: int = 30
    ):
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.cache = ResultCache(cache_ttl) if enable_cache else None

        # Stats
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.cached_executions = 0

    async def execute_parallel(
        self,
        executions: List[ToolExecution],
        fail_fast: bool = False
    ) -> List[ToolExecution]:
        """
        Executa múltiplas tools em paralelo.

        Args:
            executions: Lista de execuções
            fail_fast: Se True, para tudo no primeiro erro

        Returns:
            Lista de execuções com resultados
        """

        # Ordenar por prioridade (maior primeiro)
        executions.sort(key=lambda x: x.priority, reverse=True)

        # Semaphore para limitar concorrência
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def execute_one(execution: ToolExecution):
            async with semaphore:
                await self._execute_single(execution)

                if fail_fast and execution.status == ExecutionStatus.FAILED:
                    # Cancela outras tasks
                    raise Exception(f"Tool {execution.tool_name} failed")

        # Executar todas em paralelo
        try:
            await asyncio.gather(*[execute_one(e) for e in executions])
        except Exception as e:
            # Se fail_fast, algumas tools podem não ter executado
            pass

        return executions

    async def _execute_single(self, execution: ToolExecution):
        """Executa uma tool única com retry logic"""
        # Verifica cache primeiro
        if self.cache:
            cached_result = self.cache.get(execution.tool_name, execution.tool_input)
            if cached_result:
                execution.status = ExecutionStatus.CACHED
                execution.result = cached_result
                execution.cached = True
                self.cached_executions += 1
                self.total_executions += 1
                return

        # Retry loop
        for attempt in range(execution.max_retries + 1):
            execution.retry_count = attempt

            try:
                execution.status = ExecutionStatus.RUNNING
                execution.start_time = datetime.now().isoformat()
                start_ms = datetime.now().timestamp() * 1000

                # Executar com timeout
                result = await asyncio.wait_for(
                    execution.executor(execution.tool_input),
                    timeout=execution.timeout
                )

                end_ms = datetime.now().timestamp() * 1000
                execution.execution_time_ms = int(end_ms - start_ms)
                execution.end_time = datetime.now().isoformat()
                execution.result = result
                execution.status = ExecutionStatus.SUCCESS

                # Salvar no cache
                if self.cache:
                    self.cache.set(execution.tool_name, execution.tool_input, result)

                self.successful_executions += 1
                self.total_executions += 1
                return

            except asyncio.TimeoutError:
                execution.status = ExecutionStatus.TIMEOUT
                execution.error = f"Timeout after {execution.timeout}s"

                if attempt < execution.max_retries:
                    # Retry
                    await asyncio.sleep(1)  # Backoff
                    continue
                else:
                    self.failed_executions += 1
                    self.total_executions += 1
                    return

            except Exception as e:
                execution.status = ExecutionStatus.FAILED
                execution.error = str(e)

                if attempt < execution.max_retries:
                    # Retry
                    await asyncio.sleep(1)
                    continue
                else:
                    self.failed_executions += 1
                    self.total_executions += 1
                    return

    async def execute_with_validation(
        self,
        executions: List[ToolExecution],
        validation_level: ValidationLevel = ValidationLevel.BASIC
    ) -> Tuple[List[ToolExecution], List[ValidationResult]]:
        """
        Executa tools e valida resultados.

        Returns:
            (execuções, validações)
        """
        # Executar
        executions = await self.execute_parallel(executions)

        # Validar
        validations = []
        for execution in executions:
            if execution.status == ExecutionStatus.SUCCESS:
                validation = await self._validate_result(
                    execution.tool_name,
                    execution.result,
                    validation_level
                )
                validations.append(validation)
            else:
                # Falhou, não valida
                validations.append(ValidationResult(
                    valid=False,
                    confidence=0.0,
                    issues=[f"Execution failed: {execution.error}"]
                ))

        return executions, validations

    async def _validate_result(
        self,
        tool_name: str,
        result: Dict,
        level: ValidationLevel
    ) -> ValidationResult:
        """Valida resultado de uma tool"""

        if level == ValidationLevel.NONE:
            return ValidationResult(valid=True, confidence=1.0)

        issues = []
        warnings = []
        confidence = 1.0

        # BASIC validation
        if not result:
            issues.append("Result is empty")
            confidence = 0.0

        if isinstance(result, dict):
            # Check for error indicators
            if "error" in result:
                issues.append(f"Result contains error: {result['error']}")
                confidence *= 0.5

            # Check for common fields
            if "note" in result and "pending" in result["note"].lower():
                warnings.append("Tool integration pending")
                confidence *= 0.7

        # STRICT validation
        if level == ValidationLevel.STRICT:
            # Check data completeness
            if isinstance(result, dict):
                # Conta campos com valores reais
                real_fields = sum(1 for v in result.values() if v not in [None, [], {}, "", 0, False])

                if real_fields == 0:
                    issues.append("No real data in result")
                    confidence = 0.0
                elif real_fields < 3:
                    warnings.append("Limited data in result")
                    confidence *= 0.8

        valid = len(issues) == 0

        return ValidationResult(
            valid=valid,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
            metadata={"tool_name": tool_name}
        )

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do orchestrator"""
        success_rate = (self.successful_executions / self.total_executions * 100) if self.total_executions > 0 else 0

        stats = {
            "total_executions": self.total_executions,
            "successful": self.successful_executions,
            "failed": self.failed_executions,
            "cached": self.cached_executions,
            "success_rate": f"{success_rate:.2f}%",
            "max_concurrent": self.max_concurrent
        }

        if self.cache:
            stats["cache"] = self.cache.get_stats()

        return stats


class SmartRetry:
    """
    Sistema inteligente de retry que aprende.

    Ajusta retry strategy baseado em histórico.
    """

    def __init__(self):
        self.tool_stats: Dict[str, Dict] = {}

    def should_retry(self, tool_name: str, error: str, attempt: int) -> bool:
        """Decide se deve fazer retry baseado em histórico"""

        # Se é timeout, sempre retenta (pode ser load temporário)
        if "timeout" in error.lower():
            return True

        # Se é erro de rede, retenta
        if any(x in error.lower() for x in ["connection", "network", "unreachable"]):
            return True

        # Se é erro de API rate limit, retenta com backoff maior
        if "rate limit" in error.lower():
            return True

        # Se é erro de autenticação, não retenta (vai falhar de novo)
        if any(x in error.lower() for x in ["unauthorized", "forbidden", "authentication"]):
            return False

        # Se é erro de validação de input, não retenta
        if any(x in error.lower() for x in ["invalid", "validation", "bad request"]):
            return False

        # Default: retenta até max_retries
        return True

    def get_backoff_time(self, tool_name: str, attempt: int) -> float:
        """Retorna tempo de espera antes de retry (exponential backoff)"""
        base_delay = 1.0  # 1 segundo
        max_delay = 30.0  # 30 segundos

        delay = min(base_delay * (2 ** attempt), max_delay)

        return delay


class ResultValidator:
    """
    Validador avançado de resultados de tools.
    """

    def __init__(self):
        self.validation_rules = {
            # Rules por tipo de tool
            "ip": self._validate_ip_result,
            "domain": self._validate_domain_result,
            "hash": self._validate_hash_result,
            "generic": self._validate_generic_result
        }

    async def validate(
        self,
        tool_name: str,
        result: Dict,
        expected_type: Optional[str] = None
    ) -> ValidationResult:
        """Valida resultado baseado em regras"""

        # Detecta tipo se não fornecido
        if not expected_type:
            expected_type = self._detect_type(tool_name)

        # Aplica validação
        validator = self.validation_rules.get(expected_type, self._validate_generic_result)
        return await validator(result)

    def _detect_type(self, tool_name: str) -> str:
        """Detecta tipo baseado no nome da tool"""
        if "ip" in tool_name.lower():
            return "ip"
        elif "domain" in tool_name.lower():
            return "domain"
        elif "hash" in tool_name.lower() or "malware" in tool_name.lower():
            return "hash"
        else:
            return "generic"

    async def _validate_ip_result(self, result: Dict) -> ValidationResult:
        """Valida resultado de tool relacionada a IP"""
        issues = []
        warnings = []
        confidence = 1.0

        # Deve ter informação de geolocalização
        if "location" not in result and "geolocation" not in result:
            warnings.append("Missing geolocation data")
            confidence *= 0.9

        # Deve ter informação de ISP/ASN
        if "isp" not in result and "asn" not in result:
            warnings.append("Missing ISP/ASN data")
            confidence *= 0.9

        return ValidationResult(
            valid=len(issues) == 0,
            confidence=confidence,
            issues=issues,
            warnings=warnings
        )

    async def _validate_domain_result(self, result: Dict) -> ValidationResult:
        """Valida resultado de tool relacionada a domain"""
        issues = []
        warnings = []
        confidence = 1.0

        # Deve ter registros DNS ou WHOIS
        if "dns" not in result and "whois" not in result and "records" not in result:
            warnings.append("Missing DNS/WHOIS data")
            confidence *= 0.8

        return ValidationResult(
            valid=len(issues) == 0,
            confidence=confidence,
            issues=issues,
            warnings=warnings
        )

    async def _validate_hash_result(self, result: Dict) -> ValidationResult:
        """Valida resultado de análise de hash"""
        issues = []
        warnings = []
        confidence = 1.0

        # Deve ter veredicto (malicious/benign)
        if "malicious" not in result and "verdict" not in result and "is_malware" not in result:
            issues.append("Missing malware verdict")
            confidence = 0.5

        return ValidationResult(
            valid=len(issues) == 0,
            confidence=confidence,
            issues=issues,
            warnings=warnings
        )

    async def _validate_generic_result(self, result: Dict) -> ValidationResult:
        """Validação genérica"""
        issues = []
        warnings = []
        confidence = 1.0

        if not result:
            issues.append("Empty result")
            confidence = 0.0

        return ValidationResult(
            valid=len(issues) == 0,
            confidence=confidence,
            issues=issues,
            warnings=warnings
        )