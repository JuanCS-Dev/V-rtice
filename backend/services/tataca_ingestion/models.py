"""Tatacá Ingestion Service - Data Models.

Pydantic models for entities in the criminal investigation domain.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataSource(str, Enum):
    """Data source identifiers."""
    SINESP = "sinesp"
    PRISIONAL = "prisional"
    ANTECEDENTES = "antecedentes"
    ANPR = "anpr"  # Automatic Number Plate Recognition
    MANUAL = "manual"


class EntityType(str, Enum):
    """Entity types in the knowledge graph."""
    PESSOA = "pessoa"
    VEICULO = "veiculo"
    ENDERECO = "endereco"
    OCORRENCIA = "ocorrencia"


class RelationType(str, Enum):
    """Relationship types in the knowledge graph."""
    POSSUI = "possui"  # Pessoa -> Veículo
    ENVOLVIDO_EM = "envolvido_em"  # Pessoa -> Ocorrência
    RESIDE_EM = "reside_em"  # Pessoa -> Endereço
    OCORREU_EM = "ocorreu_em"  # Ocorrência -> Endereço
    REGISTRADO_EM = "registrado_em"  # Veículo -> Endereço


# Domain Entities

class Pessoa(BaseModel):
    """Person entity."""
    cpf: Optional[str] = Field(None, description="CPF number")
    nome: str = Field(..., description="Full name")
    data_nascimento: Optional[datetime] = Field(None, description="Birth date")
    mae: Optional[str] = Field(None, description="Mother's name")
    pai: Optional[str] = Field(None, description="Father's name")
    rg: Optional[str] = Field(None, description="RG number")
    telefone: Optional[str] = Field(None, description="Phone number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Veiculo(BaseModel):
    """Vehicle entity."""
    placa: str = Field(..., description="License plate")
    renavam: Optional[str] = Field(None, description="RENAVAM number")
    chassi: Optional[str] = Field(None, description="Chassis number")
    marca: Optional[str] = Field(None, description="Brand")
    modelo: Optional[str] = Field(None, description="Model")
    ano_fabricacao: Optional[int] = Field(None, description="Manufacturing year")
    ano_modelo: Optional[int] = Field(None, description="Model year")
    cor: Optional[str] = Field(None, description="Color")
    situacao: Optional[str] = Field(None, description="Status (regular, roubado, etc)")
    proprietario_cpf: Optional[str] = Field(None, description="Owner's CPF")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Endereco(BaseModel):
    """Address entity."""
    cep: Optional[str] = Field(None, description="ZIP code")
    logradouro: str = Field(..., description="Street address")
    numero: Optional[str] = Field(None, description="Number")
    complemento: Optional[str] = Field(None, description="Complement")
    bairro: Optional[str] = Field(None, description="Neighborhood")
    cidade: str = Field(..., description="City")
    estado: str = Field(..., description="State")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Ocorrencia(BaseModel):
    """Criminal occurrence entity."""
    numero_bo: str = Field(..., description="Police report number")
    tipo: str = Field(..., description="Occurrence type")
    data_hora: datetime = Field(..., description="Date and time")
    descricao: Optional[str] = Field(None, description="Description")
    local_logradouro: Optional[str] = Field(None, description="Location street")
    local_bairro: Optional[str] = Field(None, description="Location neighborhood")
    local_cidade: Optional[str] = Field(None, description="Location city")
    local_estado: Optional[str] = Field(None, description="Location state")
    delegacia: Optional[str] = Field(None, description="Police station")
    status: Optional[str] = Field(None, description="Status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ETL Models

class IngestJobRequest(BaseModel):
    """Request to create an ingestion job."""
    source: DataSource = Field(..., description="Data source")
    entity_type: Optional[EntityType] = Field(None, description="Entity type to ingest")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    load_to_postgres: bool = Field(default=True, description="Load to PostgreSQL")
    load_to_neo4j: bool = Field(default=True, description="Load to Neo4j")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job metadata")


class IngestJobResponse(BaseModel):
    """Response for job creation."""
    job_id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Job status")
    source: DataSource = Field(..., description="Data source")
    created_at: datetime = Field(..., description="Creation timestamp")
    message: str = Field(..., description="Status message")


class IngestJobStatus(BaseModel):
    """Job status response."""
    job_id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Current status")
    source: DataSource = Field(..., description="Data source")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    records_processed: int = Field(default=0, description="Records processed")
    records_failed: int = Field(default=0, description="Records failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job metadata")


class ScheduleJobRequest(BaseModel):
    """Request to schedule a recurring job."""
    source: DataSource = Field(..., description="Data source")
    entity_type: Optional[EntityType] = Field(None, description="Entity type")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    enabled: bool = Field(default=True, description="Whether schedule is enabled")


class EntityRelationship(BaseModel):
    """Relationship between entities for Neo4j."""
    source_type: EntityType = Field(..., description="Source entity type")
    source_id: str = Field(..., description="Source entity ID")
    target_type: EntityType = Field(..., description="Target entity type")
    target_id: str = Field(..., description="Target entity ID")
    relation_type: RelationType = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relation properties")


# Connector Response Models

class SinespVehicleResponse(BaseModel):
    """SINESP vehicle data response."""
    placa: str
    situacao: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ano: Optional[str] = None
    cor: Optional[str] = None
    chassi: Optional[str] = None
    municipio: Optional[str] = None

    def to_veiculo(self) -> Veiculo:
        """Convert to Veiculo entity."""
        return Veiculo(
            placa=self.placa,
            chassi=self.chassi,
            marca=self.marca,
            modelo=self.modelo,
            ano_modelo=int(self.ano) if self.ano else None,
            cor=self.cor,
            situacao=self.situacao,
            metadata={
                "municipio": self.municipio,
                "source": "sinesp"
            }
        )


class TransformResult(BaseModel):
    """Result of data transformation."""
    success: bool = Field(..., description="Whether transformation succeeded")
    entity_type: EntityType = Field(..., description="Entity type")
    entity_data: Optional[Dict[str, Any]] = Field(None, description="Transformed entity data")
    relationships: List[EntityRelationship] = Field(
        default_factory=list,
        description="Related entities"
    )
    error_message: Optional[str] = Field(None, description="Error if failed")


class LoadResult(BaseModel):
    """Result of data loading."""
    success: bool = Field(..., description="Whether load succeeded")
    entity_type: EntityType = Field(..., description="Entity type")
    entity_id: str = Field(..., description="Entity ID")
    postgres_loaded: bool = Field(default=False, description="Loaded to PostgreSQL")
    neo4j_loaded: bool = Field(default=False, description="Loaded to Neo4j")
    error_message: Optional[str] = Field(None, description="Error if failed")
