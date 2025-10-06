"""Tatacá Ingestion - PostgreSQL Loader.

Loads transformed entities into PostgreSQL Aurora database with deduplication
and conflict resolution.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, MetaData, Column, String, Integer, DateTime, JSON, Float, text
from sqlalchemy.dialects.postgresql import insert

from models import EntityType, LoadResult
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PostgresLoader:
    """
    Loads entities into PostgreSQL database.

    Handles schema creation, data insertion, deduplication, and conflict
    resolution for all entity types in the Aurora database.
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize PostgreSQL loader.

        Args:
            connection_string: Database URL (defaults to settings)
        """
        self.connection_string = connection_string or settings.postgres_url
        self.engine = None
        self.session_factory = None
        self.metadata = MetaData()

        # Define table schemas
        self._define_tables()

    def _define_tables(self):
        """Define SQLAlchemy table schemas for entities."""

        # Pessoa table
        self.pessoa_table = Table(
            'tataca_pessoas',
            self.metadata,
            Column('cpf', String(11), primary_key=True, nullable=True),
            Column('nome', String(255), nullable=False),
            Column('data_nascimento', DateTime, nullable=True),
            Column('mae', String(255), nullable=True),
            Column('pai', String(255), nullable=True),
            Column('rg', String(20), nullable=True),
            Column('telefone', String(20), nullable=True),
            Column('metadata', JSON, nullable=False),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        )

        # Veiculo table
        self.veiculo_table = Table(
            'tataca_veiculos',
            self.metadata,
            Column('placa', String(10), primary_key=True),
            Column('renavam', String(20), nullable=True),
            Column('chassi', String(20), nullable=True),
            Column('marca', String(100), nullable=True),
            Column('modelo', String(100), nullable=True),
            Column('ano_fabricacao', Integer, nullable=True),
            Column('ano_modelo', Integer, nullable=True),
            Column('cor', String(50), nullable=True),
            Column('situacao', String(50), nullable=True),
            Column('proprietario_cpf', String(11), nullable=True),
            Column('metadata', JSON, nullable=False),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        )

        # Endereco table
        self.endereco_table = Table(
            'tataca_enderecos',
            self.metadata,
            Column('id', String(500), primary_key=True),  # Composite ID
            Column('cep', String(8), nullable=True),
            Column('logradouro', String(255), nullable=False),
            Column('numero', String(20), nullable=True),
            Column('complemento', String(100), nullable=True),
            Column('bairro', String(100), nullable=True),
            Column('cidade', String(100), nullable=False),
            Column('estado', String(2), nullable=False),
            Column('latitude', Float, nullable=True),
            Column('longitude', Float, nullable=True),
            Column('metadata', JSON, nullable=False),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        )

        # Ocorrencia table
        self.ocorrencia_table = Table(
            'tataca_ocorrencias',
            self.metadata,
            Column('numero_bo', String(50), primary_key=True),
            Column('tipo', String(100), nullable=False),
            Column('data_hora', DateTime, nullable=False),
            Column('descricao', String(1000), nullable=True),
            Column('local_logradouro', String(255), nullable=True),
            Column('local_bairro', String(100), nullable=True),
            Column('local_cidade', String(100), nullable=True),
            Column('local_estado', String(2), nullable=True),
            Column('delegacia', String(100), nullable=True),
            Column('status', String(50), nullable=True),
            Column('metadata', JSON, nullable=False),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        )

    async def initialize(self):
        """Initialize database connection and create tables."""
        try:
            logger.info("Initializing PostgreSQL loader...")

            # Create async engine
            self.engine = create_async_engine(
                self.connection_string,
                echo=False,
                pool_size=20,
                max_overflow=40
            )

            # Create session factory
            self.session_factory = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Create tables if they don't exist
            async with self.engine.begin() as conn:
                await conn.run_sync(self.metadata.create_all)

            logger.info("✅ PostgreSQL loader initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL loader: {e}", exc_info=True)
            raise

    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("PostgreSQL loader closed")

    async def load_entity(
        self,
        entity_type: EntityType,
        entity_data: Dict[str, Any]
    ) -> LoadResult:
        """
        Load a single entity into PostgreSQL.

        Args:
            entity_type: Type of entity
            entity_data: Entity data dictionary

        Returns:
            LoadResult with success status
        """
        try:
            # Select appropriate table
            if entity_type == EntityType.PESSOA:
                return await self._load_pessoa(entity_data)
            elif entity_type == EntityType.VEICULO:
                return await self._load_veiculo(entity_data)
            elif entity_type == EntityType.ENDERECO:
                return await self._load_endereco(entity_data)
            elif entity_type == EntityType.OCORRENCIA:
                return await self._load_ocorrencia(entity_data)
            else:
                return LoadResult(
                    success=False,
                    entity_type=entity_type,
                    entity_id="unknown",
                    postgres_loaded=False,
                    error_message=f"Unknown entity type: {entity_type}"
                )

        except Exception as e:
            logger.error(f"Error loading entity {entity_type}: {e}", exc_info=True)
            return LoadResult(
                success=False,
                entity_type=entity_type,
                entity_id=str(entity_data.get("cpf") or entity_data.get("placa") or entity_data.get("numero_bo") or "unknown"),
                postgres_loaded=False,
                error_message=str(e)
            )

    async def _load_pessoa(self, data: Dict[str, Any]) -> LoadResult:
        """Load Pessoa entity with upsert."""
        async with self.session_factory() as session:
            # Prepare data
            pessoa_id = data.get("cpf") or data.get("nome")

            stmt = insert(self.pessoa_table).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['cpf'] if data.get('cpf') else ['nome'],
                set_={
                    'nome': stmt.excluded.nome,
                    'data_nascimento': stmt.excluded.data_nascimento,
                    'mae': stmt.excluded.mae,
                    'pai': stmt.excluded.pai,
                    'rg': stmt.excluded.rg,
                    'telefone': stmt.excluded.telefone,
                    'metadata': stmt.excluded.metadata,
                    'updated_at': datetime.utcnow()
                }
            )

            await session.execute(stmt)
            await session.commit()

            logger.info(f"Loaded Pessoa: {pessoa_id}")

            return LoadResult(
                success=True,
                entity_type=EntityType.PESSOA,
                entity_id=pessoa_id,
                postgres_loaded=True
            )

    async def _load_veiculo(self, data: Dict[str, Any]) -> LoadResult:
        """Load Veiculo entity with upsert."""
        async with self.session_factory() as session:
            placa = data.get("placa")

            stmt = insert(self.veiculo_table).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['placa'],
                set_={
                    'renavam': stmt.excluded.renavam,
                    'chassi': stmt.excluded.chassi,
                    'marca': stmt.excluded.marca,
                    'modelo': stmt.excluded.modelo,
                    'ano_fabricacao': stmt.excluded.ano_fabricacao,
                    'ano_modelo': stmt.excluded.ano_modelo,
                    'cor': stmt.excluded.cor,
                    'situacao': stmt.excluded.situacao,
                    'proprietario_cpf': stmt.excluded.proprietario_cpf,
                    'metadata': stmt.excluded.metadata,
                    'updated_at': datetime.utcnow()
                }
            )

            await session.execute(stmt)
            await session.commit()

            logger.info(f"Loaded Veiculo: {placa}")

            return LoadResult(
                success=True,
                entity_type=EntityType.VEICULO,
                entity_id=placa,
                postgres_loaded=True
            )

    async def _load_endereco(self, data: Dict[str, Any]) -> LoadResult:
        """Load Endereco entity with upsert."""
        async with self.session_factory() as session:
            # Build composite ID
            endereco_id = f"{data['logradouro']}-{data['cidade']}-{data['estado']}"
            if data.get('numero'):
                endereco_id = f"{data['logradouro']}-{data['numero']}-{data['cidade']}-{data['estado']}"

            data['id'] = endereco_id

            stmt = insert(self.endereco_table).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'cep': stmt.excluded.cep,
                    'complemento': stmt.excluded.complemento,
                    'bairro': stmt.excluded.bairro,
                    'latitude': stmt.excluded.latitude,
                    'longitude': stmt.excluded.longitude,
                    'metadata': stmt.excluded.metadata,
                    'updated_at': datetime.utcnow()
                }
            )

            await session.execute(stmt)
            await session.commit()

            logger.info(f"Loaded Endereco: {endereco_id}")

            return LoadResult(
                success=True,
                entity_type=EntityType.ENDERECO,
                entity_id=endereco_id,
                postgres_loaded=True
            )

    async def _load_ocorrencia(self, data: Dict[str, Any]) -> LoadResult:
        """Load Ocorrencia entity with upsert."""
        async with self.session_factory() as session:
            numero_bo = data.get("numero_bo")

            stmt = insert(self.ocorrencia_table).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['numero_bo'],
                set_={
                    'tipo': stmt.excluded.tipo,
                    'data_hora': stmt.excluded.data_hora,
                    'descricao': stmt.excluded.descricao,
                    'local_logradouro': stmt.excluded.local_logradouro,
                    'local_bairro': stmt.excluded.local_bairro,
                    'local_cidade': stmt.excluded.local_cidade,
                    'local_estado': stmt.excluded.local_estado,
                    'delegacia': stmt.excluded.delegacia,
                    'status': stmt.excluded.status,
                    'metadata': stmt.excluded.metadata,
                    'updated_at': datetime.utcnow()
                }
            )

            await session.execute(stmt)
            await session.commit()

            logger.info(f"Loaded Ocorrencia: {numero_bo}")

            return LoadResult(
                success=True,
                entity_type=EntityType.OCORRENCIA,
                entity_id=numero_bo,
                postgres_loaded=True
            )

    async def load_batch(
        self,
        entity_type: EntityType,
        entities: List[Dict[str, Any]]
    ) -> List[LoadResult]:
        """
        Load multiple entities in batch.

        Args:
            entity_type: Type of entities
            entities: List of entity data dictionaries

        Returns:
            List of LoadResult objects
        """
        results = []

        for entity_data in entities:
            result = await self.load_entity(entity_type, entity_data)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        logger.info(f"Batch loaded {success_count}/{len(entities)} {entity_type} entities")

        return results

    async def health_check(self) -> bool:
        """
        Check PostgreSQL connection health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.engine:
                return False

            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            return True

        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False
