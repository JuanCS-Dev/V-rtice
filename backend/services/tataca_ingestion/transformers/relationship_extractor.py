"""Tatacá Ingestion - Relationship Extractor.

Extracts relationships between entities for knowledge graph construction in Neo4j.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from models import (
    EntityType,
    RelationType,
    EntityRelationship,
    Pessoa,
    Veiculo,
    Endereco,
    Ocorrencia
)

logger = logging.getLogger(__name__)


class RelationshipExtractor:
    """
    Extracts relationships between entities for graph database.

    Analyzes entity data to identify and create explicit relationships that
    will be stored as edges in the Neo4j knowledge graph.
    """

    def __init__(self):
        """Initialize relationship extractor."""
        pass

    def extract_pessoa_relationships(
        self,
        pessoa: Pessoa,
        raw_data: Dict[str, Any]
    ) -> List[EntityRelationship]:
        """
        Extract relationships for a Pessoa entity.

        Args:
            pessoa: Pessoa entity
            raw_data: Original raw data that may contain relationship hints

        Returns:
            List of EntityRelationship objects
        """
        relationships = []

        # Extract Pessoa -> Veiculo (POSSUI)
        if raw_data.get("veiculos"):
            for veiculo_data in raw_data["veiculos"]:
                placa = veiculo_data.get("placa")
                if placa:
                    rel = EntityRelationship(
                        source_type=EntityType.PESSOA,
                        source_id=pessoa.cpf or pessoa.nome,
                        target_type=EntityType.VEICULO,
                        target_id=placa,
                        relation_type=RelationType.POSSUI,
                        properties={
                            "desde": veiculo_data.get("data_aquisicao"),
                            "ativo": veiculo_data.get("ativo", True),
                            "created_at": datetime.utcnow().isoformat()
                        }
                    )
                    relationships.append(rel)
                    logger.debug(f"Extracted POSSUI relationship: {pessoa.nome} -> {placa}")

        # Extract Pessoa -> Endereco (RESIDE_EM)
        if raw_data.get("enderecos"):
            for endereco_data in raw_data["enderecos"]:
                endereco_id = self._build_endereco_id(endereco_data)
                if endereco_id:
                    rel = EntityRelationship(
                        source_type=EntityType.PESSOA,
                        source_id=pessoa.cpf or pessoa.nome,
                        target_type=EntityType.ENDERECO,
                        target_id=endereco_id,
                        relation_type=RelationType.RESIDE_EM,
                        properties={
                            "tipo": endereco_data.get("tipo", "residencial"),
                            "principal": endereco_data.get("principal", False),
                            "desde": endereco_data.get("desde"),
                            "created_at": datetime.utcnow().isoformat()
                        }
                    )
                    relationships.append(rel)
                    logger.debug(f"Extracted RESIDE_EM relationship: {pessoa.nome} -> {endereco_id}")

        # Extract Pessoa -> Ocorrencia (ENVOLVIDO_EM)
        if raw_data.get("ocorrencias"):
            for ocorrencia_ref in raw_data["ocorrencias"]:
                numero_bo = ocorrencia_ref.get("numero_bo")
                if numero_bo:
                    rel = EntityRelationship(
                        source_type=EntityType.PESSOA,
                        source_id=pessoa.cpf or pessoa.nome,
                        target_type=EntityType.OCORRENCIA,
                        target_id=numero_bo,
                        relation_type=RelationType.ENVOLVIDO_EM,
                        properties={
                            "papel": ocorrencia_ref.get("papel", "envolvido"),  # vitima, suspeito, testemunha
                            "data_envolvimento": ocorrencia_ref.get("data"),
                            "created_at": datetime.utcnow().isoformat()
                        }
                    )
                    relationships.append(rel)
                    logger.debug(f"Extracted ENVOLVIDO_EM relationship: {pessoa.nome} -> {numero_bo}")

        return relationships

    def extract_veiculo_relationships(
        self,
        veiculo: Veiculo,
        raw_data: Dict[str, Any]
    ) -> List[EntityRelationship]:
        """
        Extract relationships for a Veiculo entity.

        Args:
            veiculo: Veiculo entity
            raw_data: Original raw data

        Returns:
            List of EntityRelationship objects
        """
        relationships = []

        # Extract Veiculo -> Pessoa (inverse of POSSUI - owner)
        if veiculo.proprietario_cpf:
            rel = EntityRelationship(
                source_type=EntityType.PESSOA,
                source_id=veiculo.proprietario_cpf,
                target_type=EntityType.VEICULO,
                target_id=veiculo.placa,
                relation_type=RelationType.POSSUI,
                properties={
                    "source": "vehicle_registration",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            relationships.append(rel)
            logger.debug(f"Extracted POSSUI relationship: {veiculo.proprietario_cpf} -> {veiculo.placa}")

        # Extract Veiculo -> Endereco (REGISTRADO_EM)
        municipio = veiculo.metadata.get("municipio")
        uf = veiculo.metadata.get("uf")
        if municipio and uf:
            # Create simplified address ID for registration location
            endereco_id = f"{municipio}-{uf}"
            rel = EntityRelationship(
                source_type=EntityType.VEICULO,
                source_id=veiculo.placa,
                target_type=EntityType.ENDERECO,
                target_id=endereco_id,
                relation_type=RelationType.REGISTRADO_EM,
                properties={
                    "municipio": municipio,
                    "uf": uf,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            relationships.append(rel)
            logger.debug(f"Extracted REGISTRADO_EM relationship: {veiculo.placa} -> {endereco_id}")

        # Extract Veiculo -> Ocorrencia (if vehicle involved in occurrences)
        if raw_data.get("ocorrencias"):
            for ocorrencia_ref in raw_data["ocorrencias"]:
                numero_bo = ocorrencia_ref.get("numero_bo")
                if numero_bo:
                    rel = EntityRelationship(
                        source_type=EntityType.VEICULO,
                        source_id=veiculo.placa,
                        target_type=EntityType.OCORRENCIA,
                        target_id=numero_bo,
                        relation_type=RelationType.ENVOLVIDO_EM,
                        properties={
                            "tipo_envolvimento": ocorrencia_ref.get("tipo", "mencionado"),
                            "created_at": datetime.utcnow().isoformat()
                        }
                    )
                    relationships.append(rel)
                    logger.debug(f"Extracted ENVOLVIDO_EM relationship: {veiculo.placa} -> {numero_bo}")

        return relationships

    def extract_ocorrencia_relationships(
        self,
        ocorrencia: Ocorrencia,
        raw_data: Dict[str, Any]
    ) -> List[EntityRelationship]:
        """
        Extract relationships for an Ocorrencia entity.

        Args:
            ocorrencia: Ocorrencia entity
            raw_data: Original raw data

        Returns:
            List of EntityRelationship objects
        """
        relationships = []

        # Extract Ocorrencia -> Endereco (OCORREU_EM)
        if ocorrencia.local_logradouro and ocorrencia.local_cidade and ocorrencia.local_estado:
            endereco_id = self._build_endereco_id({
                "logradouro": ocorrencia.local_logradouro,
                "cidade": ocorrencia.local_cidade,
                "estado": ocorrencia.local_estado,
                "bairro": ocorrencia.local_bairro
            })

            rel = EntityRelationship(
                source_type=EntityType.OCORRENCIA,
                source_id=ocorrencia.numero_bo,
                target_type=EntityType.ENDERECO,
                target_id=endereco_id,
                relation_type=RelationType.OCORREU_EM,
                properties={
                    "data_hora": ocorrencia.data_hora.isoformat(),
                    "tipo_ocorrencia": ocorrencia.tipo,
                    "latitude": raw_data.get("latitude"),
                    "longitude": raw_data.get("longitude"),
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            relationships.append(rel)
            logger.debug(f"Extracted OCORREU_EM relationship: {ocorrencia.numero_bo} -> {endereco_id}")

        # Extract Ocorrencia -> Pessoa (ENVOLVIDO_EM - inverse)
        if raw_data.get("envolvidos"):
            for pessoa_ref in raw_data["envolvidos"]:
                pessoa_id = pessoa_ref.get("cpf") or pessoa_ref.get("nome")
                if pessoa_id:
                    rel = EntityRelationship(
                        source_type=EntityType.PESSOA,
                        source_id=pessoa_id,
                        target_type=EntityType.OCORRENCIA,
                        target_id=ocorrencia.numero_bo,
                        relation_type=RelationType.ENVOLVIDO_EM,
                        properties={
                            "papel": pessoa_ref.get("papel", "envolvido"),
                            "nome": pessoa_ref.get("nome"),
                            "created_at": datetime.utcnow().isoformat()
                        }
                    )
                    relationships.append(rel)
                    logger.debug(f"Extracted ENVOLVIDO_EM relationship: {pessoa_id} -> {ocorrencia.numero_bo}")

        # Extract Ocorrencia -> Veiculo (if vehicles mentioned)
        if raw_data.get("veiculos_envolvidos"):
            for veiculo_ref in raw_data["veiculos_envolvidos"]:
                placa = veiculo_ref.get("placa")
                if placa:
                    rel = EntityRelationship(
                        source_type=EntityType.VEICULO,
                        source_id=placa,
                        target_type=EntityType.OCORRENCIA,
                        target_id=ocorrencia.numero_bo,
                        relation_type=RelationType.ENVOLVIDO_EM,
                        properties={
                            "situacao": veiculo_ref.get("situacao", "mencionado"),
                            "created_at": datetime.utcnow().isoformat()
                        }
                    )
                    relationships.append(rel)
                    logger.debug(f"Extracted ENVOLVIDO_EM relationship: {placa} -> {ocorrencia.numero_bo}")

        return relationships

    def extract_endereco_relationships(
        self,
        endereco: Endereco,
        raw_data: Dict[str, Any]
    ) -> List[EntityRelationship]:
        """
        Extract relationships for an Endereco entity.

        Args:
            endereco: Endereco entity
            raw_data: Original raw data

        Returns:
            List of EntityRelationship objects
        """
        relationships = []

        # Most Endereco relationships are created from other entities
        # (Pessoa -> RESIDE_EM -> Endereco, Ocorrencia -> OCORREU_EM -> Endereco)

        # Could add proximity relationships here in the future
        # (e.g., PROXIMO_DE for addresses within certain distance)

        logger.debug(f"Extracted {len(relationships)} relationships for Endereco")
        return relationships

    def _build_endereco_id(self, endereco_data: Dict[str, Any]) -> Optional[str]:
        """
        Build a unique identifier for an address.

        Args:
            endereco_data: Address data dictionary

        Returns:
            Unique address identifier or None
        """
        logradouro = endereco_data.get("logradouro", "").strip()
        cidade = endereco_data.get("cidade", "").strip()
        estado = endereco_data.get("estado", "").strip()

        if not logradouro or not cidade or not estado:
            return None

        # Build composite ID
        parts = [logradouro, cidade, estado]

        # Add optional parts if available
        if endereco_data.get("numero"):
            parts.insert(1, str(endereco_data["numero"]))
        if endereco_data.get("bairro"):
            parts.insert(2 if endereco_data.get("numero") else 1, endereco_data["bairro"])

        # Create normalized ID
        endereco_id = "-".join(parts).lower().replace(" ", "_")
        return endereco_id

    def infer_relationships_from_context(
        self,
        entities: List[Dict[str, Any]]
    ) -> List[EntityRelationship]:
        """
        Infer implicit relationships from entity context.

        Analyzes multiple entities to discover relationships that are not
        explicitly stated in the data but can be inferred from patterns.

        Args:
            entities: List of entity dictionaries with type and data

        Returns:
            List of inferred EntityRelationship objects
        """
        relationships = []

        # Example: If same CPF appears as proprietario in multiple vehicles
        # we can infer they're all owned by the same person

        pessoas_map = {}
        veiculos_map = {}
        enderecos_map = {}

        # Build entity maps
        for entity in entities:
            entity_type = entity.get("type")
            entity_data = entity.get("data")

            if entity_type == EntityType.PESSOA:
                cpf = entity_data.get("cpf")
                if cpf:
                    pessoas_map[cpf] = entity_data

            elif entity_type == EntityType.VEICULO:
                placa = entity_data.get("placa")
                if placa:
                    veiculos_map[placa] = entity_data

            elif entity_type == EntityType.ENDERECO:
                endereco_id = self._build_endereco_id(entity_data)
                if endereco_id:
                    enderecos_map[endereco_id] = entity_data

        # Infer relationships based on patterns
        # (This is where more sophisticated inference could happen)

        logger.info(f"Inferred {len(relationships)} implicit relationships from {len(entities)} entities")
        return relationships
