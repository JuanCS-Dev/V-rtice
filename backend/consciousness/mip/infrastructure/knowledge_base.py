"""
Knowledge Base Repository - MIP

Repository pattern para Neo4j com operações CRUD e queries éticas.

Componentes:
- KnowledgeBaseRepository: CRUD básico
- PrincipleQueryService: Queries sobre princípios
- AuditTrailService: Log imutável de decisões
- PrecedentSearchService: Busca de casos similares

Autor: Juan Carlos de Souza
Lei Governante: Constituição Vértice v2.6
"""

import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.exceptions import Neo4jError

from .knowledge_models import (
    Principle,
    Decision,
    Precedent,
    Concept,
    PrincipleLevel,
    DecisionStatus,
    ViolationReport,
    PrecedentOutcome,
    PrincipleHierarchy
)

logger = logging.getLogger(__name__)


class KnowledgeBaseRepository:
    """
    Repository principal para MIP Knowledge Base.
    
    Gerencia conexão Neo4j e operações CRUD básicas para:
    - Principles (princípios éticos)
    - Decisions (decisões registradas)
    - Precedents (casos históricos)
    - Concepts (conceitos morais)
    
    Serve Lei II: Auditoria e rastreabilidade completas.
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "neo4j123",
        database: str = "neo4j",
        max_connection_pool_size: int = 50,
    ):
        """
        Inicializa repository.
        
        Args:
            uri: Neo4j URI
            user: Username
            password: Password
            database: Database name
            max_connection_pool_size: Connection pool size
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.max_connection_pool_size = max_connection_pool_size
        
        self.driver: Optional[AsyncDriver] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Inicializa driver Neo4j.
        
        Raises:
            Neo4jError: Se falha ao conectar
        """
        if self._initialized:
            logger.warning("Knowledge Base repository already initialized")
            return
        
        try:
            logger.info(f"Connecting to Neo4j: {self.uri}")
            
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=self.max_connection_pool_size,
                connection_timeout=30.0,
            )
            
            # Verify connectivity
            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 AS test")
                await result.single()
            
            self._initialized = True
            logger.info("✅ Neo4j connection established")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise
    
    async def close(self) -> None:
        """Fecha conexão Neo4j."""
        if self.driver:
            await self.driver.close()
            self._initialized = False
            logger.info("Neo4j connection closed")
    
    async def _create_indexes(self) -> None:
        """
        Cria indexes para performance.
        
        Indexes críticos:
        - Principle.name (busca por nome)
        - Decision.action_plan_id (audit trail)
        - Precedent.scenario_hash (similarity)
        - Concept.name (semantic search)
        """
        if not self.driver:
            return
        
        indexes = [
            "CREATE INDEX principle_name IF NOT EXISTS FOR (p:Principle) ON (p.name)",
            "CREATE INDEX principle_level IF NOT EXISTS FOR (p:Principle) ON (p.level)",
            "CREATE INDEX decision_plan_id IF NOT EXISTS FOR (d:Decision) ON (d.action_plan_id)",
            "CREATE INDEX decision_timestamp IF NOT EXISTS FOR (d:Decision) ON (d.timestamp)",
            "CREATE INDEX precedent_hash IF NOT EXISTS FOR (p:Precedent) ON (p.scenario_hash)",
            "CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)",
        ]
        
        async with self.driver.session(database=self.database) as session:
            for index_query in indexes:
                try:
                    await session.run(index_query)
                except Neo4jError as e:
                    logger.warning(f"Index creation warning: {e}")
        
        logger.info("✅ Indexes created/verified")
    
    # ============================================================================
    # PRINCIPLE OPERATIONS
    # ============================================================================
    
    async def create_principle(self, principle: Principle) -> UUID:
        """
        Cria um novo princípio ético no grafo.
        
        Args:
            principle: Principle object
            
        Returns:
            UUID do princípio criado
            
        Raises:
            Neo4jError: Se falha ao criar
        """
        if not self.driver:
            raise RuntimeError("Repository not initialized")
        
        query = """
        CREATE (p:Principle {
            id: $id,
            name: $name,
            level: $level,
            description: $description,
            severity: $severity,
            parent_principle_id: $parent_principle_id,
            applies_to_action_types: $applies_to_action_types,
            philosophical_foundation: $philosophical_foundation,
            references: $references,
            created_at: $created_at,
            immutable: $immutable
        })
        RETURN p.id AS id
        """
        
        params = {
            "id": str(principle.id),
            "name": principle.name,
            "level": principle.level.value,
            "description": principle.description,
            "severity": principle.severity,
            "parent_principle_id": str(principle.parent_principle_id) if principle.parent_principle_id else None,
            "applies_to_action_types": principle.applies_to_action_types,
            "philosophical_foundation": principle.philosophical_foundation,
            "references": principle.references,
            "created_at": principle.created_at.isoformat(),
            "immutable": principle.immutable,
        }
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, params)
            record = await result.single()
            
            # Create hierarchy relationship if has parent
            if principle.parent_principle_id:
                await self._create_principle_hierarchy(
                    principle.id, 
                    principle.parent_principle_id
                )
        
        logger.info(f"✅ Principle created: {principle.name}")
        return principle.id
    
    async def _create_principle_hierarchy(
        self, 
        child_id: UUID, 
        parent_id: UUID
    ) -> None:
        """Cria relação DERIVES_FROM entre princípios."""
        if not self.driver:
            return
        
        query = """
        MATCH (child:Principle {id: $child_id})
        MATCH (parent:Principle {id: $parent_id})
        MERGE (child)-[:DERIVES_FROM]->(parent)
        """
        
        async with self.driver.session(database=self.database) as session:
            await session.run(query, {
                "child_id": str(child_id),
                "parent_id": str(parent_id)
            })
    
    async def get_principle(self, principle_id: UUID) -> Optional[Principle]:
        """
        Busca princípio por ID.
        
        Args:
            principle_id: UUID do princípio
            
        Returns:
            Principle object ou None se não encontrado
        """
        if not self.driver:
            raise RuntimeError("Repository not initialized")
        
        query = """
        MATCH (p:Principle {id: $id})
        RETURN p
        """
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, {"id": str(principle_id)})
            record = await result.single()
            
            if not record:
                return None
            
            data = dict(record["p"])
            return self._principle_from_dict(data)
    
    async def get_principle_by_name(self, name: str) -> Optional[Principle]:
        """
        Busca princípio por nome.
        
        Args:
            name: Nome do princípio (ex: "Lei Zero")
            
        Returns:
            Principle object ou None
        """
        if not self.driver:
            raise RuntimeError("Repository not initialized")
        
        query = """
        MATCH (p:Principle {name: $name})
        RETURN p
        """
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, {"name": name})
            record = await result.single()
            
            if not record:
                return None
            
            data = dict(record["p"])
            return self._principle_from_dict(data)
    
    async def list_principles(
        self, 
        level: Optional[PrincipleLevel] = None
    ) -> List[Principle]:
        """
        Lista todos os princípios, opcionalmente filtrados por nível.
        
        Args:
            level: Filtrar por PrincipleLevel (opcional)
            
        Returns:
            Lista de Principles
        """
        if not self.driver:
            raise RuntimeError("Repository not initialized")
        
        if level:
            query = """
            MATCH (p:Principle {level: $level})
            RETURN p
            ORDER BY p.severity DESC, p.name
            """
            params = {"level": level.value}
        else:
            query = """
            MATCH (p:Principle)
            RETURN p
            ORDER BY p.severity DESC, p.name
            """
            params = {}
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, params)
            records = await result.data()
            
            return [
                self._principle_from_dict(dict(record["p"]))
                for record in records
            ]
    
    # ============================================================================
    # DECISION OPERATIONS
    # ============================================================================
    
    async def create_decision(self, decision: Decision) -> UUID:
        """
        Registra uma decisão ética no audit trail.
        
        Args:
            decision: Decision object
            
        Returns:
            UUID da decisão criada
        """
        if not self.driver:
            raise RuntimeError("Repository not initialized")
        
        query = """
        CREATE (d:Decision {
            id: $id,
            action_plan_id: $action_plan_id,
            action_plan_name: $action_plan_name,
            status: $status,
            aggregate_score: $aggregate_score,
            confidence: $confidence,
            kantian_score: $kantian_score,
            utilitarian_score: $utilitarian_score,
            virtue_score: $virtue_score,
            principialism_score: $principialism_score,
            summary: $summary,
            detailed_reasoning: $detailed_reasoning,
            violated_principles: $violated_principles,
            violation_severity: $violation_severity,
            conflicts_detected: $conflicts_detected,
            resolution_method: $resolution_method,
            requires_human_review: $requires_human_review,
            escalation_reason: $escalation_reason,
            urgency: $urgency,
            risk_level: $risk_level,
            novel_situation: $novel_situation,
            evaluation_duration_ms: $evaluation_duration_ms,
            timestamp: $timestamp,
            evaluator_version: $evaluator_version
        })
        RETURN d.id AS id
        """
        
        params = {
            "id": str(decision.id),
            "action_plan_id": str(decision.action_plan_id),
            "action_plan_name": decision.action_plan_name,
            "status": decision.status.value,
            "aggregate_score": decision.aggregate_score,
            "confidence": decision.confidence,
            "kantian_score": decision.kantian_score,
            "utilitarian_score": decision.utilitarian_score,
            "virtue_score": decision.virtue_score,
            "principialism_score": decision.principialism_score,
            "summary": decision.summary,
            "detailed_reasoning": decision.detailed_reasoning,
            "violated_principles": [str(p) for p in decision.violated_principles],
            "violation_severity": decision.violation_severity.value,
            "conflicts_detected": decision.conflicts_detected,
            "resolution_method": decision.resolution_method,
            "requires_human_review": decision.requires_human_review,
            "escalation_reason": decision.escalation_reason,
            "urgency": decision.urgency,
            "risk_level": decision.risk_level,
            "novel_situation": decision.novel_situation,
            "evaluation_duration_ms": decision.evaluation_duration_ms,
            "timestamp": decision.timestamp.isoformat(),
            "evaluator_version": decision.evaluator_version,
        }
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, params)
            
            # Create relationships to violated/honored principles
            if decision.violated_principles:
                await self._link_decision_violations(decision)
        
        logger.info(f"✅ Decision logged: {decision.action_plan_name}")
        return decision.id
    
    async def _link_decision_violations(self, decision: Decision) -> None:
        """Cria relações VIOLATES entre decisão e princípios violados."""
        if not self.driver:
            return
        
        query = """
        MATCH (d:Decision {id: $decision_id})
        MATCH (p:Principle {id: $principle_id})
        MERGE (d)-[r:VIOLATES]->(p)
        SET r.severity = $severity
        """
        
        async with self.driver.session(database=self.database) as session:
            for principle_id in decision.violated_principles:
                await session.run(query, {
                    "decision_id": str(decision.id),
                    "principle_id": str(principle_id),
                    "severity": decision.violation_severity.value
                })
    
    async def get_decision(self, decision_id: UUID) -> Optional[Decision]:
        """
        Busca decisão por ID.
        
        Args:
            decision_id: UUID da decisão
            
        Returns:
            Decision object ou None
        """
        if not self.driver:
            raise RuntimeError("Repository not initialized")
        
        query = """
        MATCH (d:Decision {id: $id})
        RETURN d
        """
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, {"id": str(decision_id)})
            record = await result.single()
            
            if not record:
                return None
            
            data = dict(record["d"])
            return self._decision_from_dict(data)
    
    async def get_decisions_by_plan(
        self, 
        action_plan_id: UUID
    ) -> List[Decision]:
        """
        Busca todas as decisões de um plano específico.
        
        Args:
            action_plan_id: UUID do ActionPlan
            
        Returns:
            Lista de Decisions (histórico completo)
        """
        if not self.driver:
            raise RuntimeError("Repository not initialized")
        
        query = """
        MATCH (d:Decision {action_plan_id: $plan_id})
        RETURN d
        ORDER BY d.timestamp DESC
        """
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, {"plan_id": str(action_plan_id)})
            records = await result.data()
            
            return [
                self._decision_from_dict(dict(record["d"]))
                for record in records
            ]
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _principle_from_dict(self, data: Dict[str, Any]) -> Principle:
        """Converte dict do Neo4j para Principle object."""
        from uuid import UUID
        from datetime import datetime
        
        return Principle(
            id=UUID(data["id"]),
            name=data["name"],
            level=PrincipleLevel(data["level"]),
            description=data["description"],
            severity=data["severity"],
            parent_principle_id=UUID(data["parent_principle_id"]) if data.get("parent_principle_id") else None,
            applies_to_action_types=data.get("applies_to_action_types", []),
            philosophical_foundation=data.get("philosophical_foundation", ""),
            references=data.get("references", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            immutable=data.get("immutable", True),
        )
    
    def _decision_from_dict(self, data: Dict[str, Any]) -> Decision:
        """Converte dict do Neo4j para Decision object."""
        from uuid import UUID
        from datetime import datetime
        
        return Decision(
            id=UUID(data["id"]),
            action_plan_id=UUID(data["action_plan_id"]),
            action_plan_name=data["action_plan_name"],
            status=DecisionStatus(data["status"]),
            aggregate_score=data.get("aggregate_score"),
            confidence=data["confidence"],
            kantian_score=data.get("kantian_score"),
            utilitarian_score=data.get("utilitarian_score"),
            virtue_score=data.get("virtue_score"),
            principialism_score=data.get("principialism_score"),
            summary=data.get("summary", ""),
            detailed_reasoning=data.get("detailed_reasoning", ""),
            violated_principles=[UUID(p) for p in data.get("violated_principles", [])],
            violation_severity=data.get("violation_severity", "none"),
            conflicts_detected=data.get("conflicts_detected", []),
            resolution_method=data.get("resolution_method", ""),
            requires_human_review=data.get("requires_human_review", False),
            escalation_reason=data.get("escalation_reason", ""),
            urgency=data.get("urgency", 0.5),
            risk_level=data.get("risk_level", 0.5),
            novel_situation=data.get("novel_situation", False),
            evaluation_duration_ms=data.get("evaluation_duration_ms", 0.0),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            evaluator_version=data.get("evaluator_version", "1.0.0"),
        )


class PrincipleQueryService:
    """
    Serviço de consultas sobre princípios éticos.
    
    Queries especializadas para análise ética:
    - Hierarquia de princípios
    - Princípios aplicáveis a ações
    - Detecção de violações
    """
    
    def __init__(self, repo: KnowledgeBaseRepository):
        """
        Inicializa service.
        
        Args:
            repo: KnowledgeBaseRepository instance
        """
        self.repo = repo
    
    async def get_principle_hierarchy(self) -> PrincipleHierarchy:
        """
        Retorna hierarquia completa de princípios.
        
        Returns:
            Dict mapeando PrincipleLevel -> List[Principle]
        """
        all_principles = await self.repo.list_principles()
        
        hierarchy: PrincipleHierarchy = {
            PrincipleLevel.PRIMORDIAL: [],
            PrincipleLevel.ZERO: [],
            PrincipleLevel.FUNDAMENTAL: [],
            PrincipleLevel.DERIVED: [],
            PrincipleLevel.OPERATIONAL: [],
        }
        
        for principle in all_principles:
            hierarchy[principle.level].append(principle)
        
        return hierarchy
    
    async def get_fundamental_laws(self) -> List[Principle]:
        """
        Retorna as leis fundamentais (Primordial, Zero, I, II, III).
        
        Returns:
            Lista com Lei Primordial, Zero, I, II, III
        """
        primordial = await self.repo.list_principles(PrincipleLevel.PRIMORDIAL)
        zero = await self.repo.list_principles(PrincipleLevel.ZERO)
        fundamental = await self.repo.list_principles(PrincipleLevel.FUNDAMENTAL)
        
        return primordial + zero + fundamental


class AuditTrailService:
    """
    Serviço de audit trail imutável.
    
    Gerencia histórico completo de decisões éticas para:
    - Rastreabilidade (Lei II)
    - Análise estatística
    - Compliance e reporting
    """
    
    def __init__(self, repo: KnowledgeBaseRepository):
        """
        Inicializa service.
        
        Args:
            repo: KnowledgeBaseRepository instance
        """
        self.repo = repo
    
    async def log_decision(self, decision: Decision) -> UUID:
        """
        Registra decisão no audit trail.
        
        Args:
            decision: Decision object
            
        Returns:
            UUID da decisão registrada
        """
        return await self.repo.create_decision(decision)
    
    async def get_decision_history(
        self, 
        action_plan_id: UUID
    ) -> List[Decision]:
        """
        Retorna histórico completo de um plano.
        
        Args:
            action_plan_id: UUID do plano
            
        Returns:
            Lista de decisões ordenadas por timestamp
        """
        return await self.repo.get_decisions_by_plan(action_plan_id)
