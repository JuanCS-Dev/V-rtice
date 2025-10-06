"""Tatacá Ingestion - Entity Transformer.

Transforms raw data from various sources into normalized domain entities with
validation, cleansing, and enrichment.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from models import (
    Pessoa,
    Veiculo,
    Endereco,
    Ocorrencia,
    DataSource,
    EntityType,
    TransformResult
)

logger = logging.getLogger(__name__)


class EntityTransformer:
    """
    Transforms raw data into normalized domain entities.

    Handles data validation, cleansing, normalization, and enrichment for
    entities in the criminal investigation domain.
    """

    def __init__(self):
        """Initialize entity transformer."""
        self._cpf_pattern = re.compile(r'^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$')
        self._placa_pattern = re.compile(r'^[A-Z]{3}-?\d{4}$|^[A-Z]{3}\d[A-Z]\d{2}$')
        self._cep_pattern = re.compile(r'^\d{5}-?\d{3}$')

    def transform_pessoa(
        self,
        raw_data: Dict[str, Any],
        source: DataSource
    ) -> TransformResult:
        """
        Transform raw person data into Pessoa entity.

        Args:
            raw_data: Raw person data from source
            source: Data source identifier

        Returns:
            TransformResult with Pessoa entity or error
        """
        try:
            # Extract and normalize fields
            cpf = self._normalize_cpf(raw_data.get("cpf"))
            nome = self._normalize_name(raw_data.get("nome", ""))

            if not nome:
                return TransformResult(
                    success=False,
                    entity_type=EntityType.PESSOA,
                    error_message="Nome is required"
                )

            # Parse birth date
            data_nascimento = None
            if raw_data.get("data_nascimento"):
                data_nascimento = self._parse_date(raw_data["data_nascimento"])

            # Build metadata
            metadata = {
                "source": source.value,
                "ingested_at": datetime.utcnow().isoformat(),
                "raw_data_hash": self._compute_hash(raw_data)
            }

            # Add optional raw fields to metadata
            for key in ["profissao", "naturalidade", "estado_civil"]:
                if key in raw_data:
                    metadata[key] = raw_data[key]

            # Create Pessoa entity
            pessoa = Pessoa(
                cpf=cpf,
                nome=nome,
                data_nascimento=data_nascimento,
                mae=self._normalize_name(raw_data.get("mae", "")),
                pai=self._normalize_name(raw_data.get("pai", "")),
                rg=self._normalize_rg(raw_data.get("rg")),
                telefone=self._normalize_phone(raw_data.get("telefone")),
                metadata=metadata
            )

            logger.info(f"Transformed Pessoa: {nome} (CPF: {cpf})")

            return TransformResult(
                success=True,
                entity_type=EntityType.PESSOA,
                entity_data=pessoa.model_dump(),
                relationships=[]
            )

        except Exception as e:
            logger.error(f"Error transforming Pessoa: {e}", exc_info=True)
            return TransformResult(
                success=False,
                entity_type=EntityType.PESSOA,
                error_message=str(e)
            )

    def transform_veiculo(
        self,
        raw_data: Dict[str, Any],
        source: DataSource
    ) -> TransformResult:
        """
        Transform raw vehicle data into Veiculo entity.

        Args:
            raw_data: Raw vehicle data from source
            source: Data source identifier

        Returns:
            TransformResult with Veiculo entity or error
        """
        try:
            # Extract and normalize plate
            placa = self._normalize_placa(raw_data.get("placa", ""))

            if not placa:
                return TransformResult(
                    success=False,
                    entity_type=EntityType.VEICULO,
                    error_message="Placa is required"
                )

            # Parse years
            ano_fabricacao = self._parse_year(raw_data.get("ano_fabricacao"))
            ano_modelo = self._parse_year(raw_data.get("ano_modelo") or raw_data.get("ano"))

            # Build metadata
            metadata = {
                "source": source.value,
                "ingested_at": datetime.utcnow().isoformat(),
                "raw_data_hash": self._compute_hash(raw_data)
            }

            # Add optional fields
            if raw_data.get("municipio"):
                metadata["municipio"] = raw_data["municipio"]
            if raw_data.get("uf"):
                metadata["uf"] = raw_data["uf"]

            # Create Veiculo entity
            veiculo = Veiculo(
                placa=placa,
                renavam=raw_data.get("renavam"),
                chassi=self._normalize_chassi(raw_data.get("chassi")),
                marca=self._normalize_text(raw_data.get("marca")),
                modelo=self._normalize_text(raw_data.get("modelo")),
                ano_fabricacao=ano_fabricacao,
                ano_modelo=ano_modelo,
                cor=self._normalize_text(raw_data.get("cor")),
                situacao=self._normalize_text(raw_data.get("situacao")),
                proprietario_cpf=self._normalize_cpf(raw_data.get("proprietario_cpf")),
                metadata=metadata
            )

            logger.info(f"Transformed Veiculo: {placa}")

            return TransformResult(
                success=True,
                entity_type=EntityType.VEICULO,
                entity_data=veiculo.model_dump(),
                relationships=[]
            )

        except Exception as e:
            logger.error(f"Error transforming Veiculo: {e}", exc_info=True)
            return TransformResult(
                success=False,
                entity_type=EntityType.VEICULO,
                error_message=str(e)
            )

    def transform_endereco(
        self,
        raw_data: Dict[str, Any],
        source: DataSource
    ) -> TransformResult:
        """
        Transform raw address data into Endereco entity.

        Args:
            raw_data: Raw address data from source
            source: Data source identifier

        Returns:
            TransformResult with Endereco entity or error
        """
        try:
            logradouro = self._normalize_text(raw_data.get("logradouro", ""))
            cidade = self._normalize_text(raw_data.get("cidade", ""))
            estado = raw_data.get("estado", "").upper()

            if not logradouro or not cidade or not estado:
                return TransformResult(
                    success=False,
                    entity_type=EntityType.ENDERECO,
                    error_message="Logradouro, cidade, and estado are required"
                )

            # Parse coordinates
            latitude = self._parse_float(raw_data.get("latitude"))
            longitude = self._parse_float(raw_data.get("longitude"))

            # Build metadata
            metadata = {
                "source": source.value,
                "ingested_at": datetime.utcnow().isoformat(),
                "raw_data_hash": self._compute_hash(raw_data)
            }

            # Create Endereco entity
            endereco = Endereco(
                cep=self._normalize_cep(raw_data.get("cep")),
                logradouro=logradouro,
                numero=raw_data.get("numero"),
                complemento=raw_data.get("complemento"),
                bairro=self._normalize_text(raw_data.get("bairro")),
                cidade=cidade,
                estado=estado,
                latitude=latitude,
                longitude=longitude,
                metadata=metadata
            )

            logger.info(f"Transformed Endereco: {logradouro}, {cidade}-{estado}")

            return TransformResult(
                success=True,
                entity_type=EntityType.ENDERECO,
                entity_data=endereco.model_dump(),
                relationships=[]
            )

        except Exception as e:
            logger.error(f"Error transforming Endereco: {e}", exc_info=True)
            return TransformResult(
                success=False,
                entity_type=EntityType.ENDERECO,
                error_message=str(e)
            )

    def transform_ocorrencia(
        self,
        raw_data: Dict[str, Any],
        source: DataSource
    ) -> TransformResult:
        """
        Transform raw occurrence data into Ocorrencia entity.

        Args:
            raw_data: Raw occurrence data from source
            source: Data source identifier

        Returns:
            TransformResult with Ocorrencia entity or error
        """
        try:
            numero_bo = raw_data.get("numero_bo", "")
            tipo = self._normalize_text(raw_data.get("tipo", ""))

            if not numero_bo or not tipo:
                return TransformResult(
                    success=False,
                    entity_type=EntityType.OCORRENCIA,
                    error_message="numero_bo and tipo are required"
                )

            # Parse datetime
            data_hora = self._parse_datetime(raw_data.get("data_hora"))
            if not data_hora:
                return TransformResult(
                    success=False,
                    entity_type=EntityType.OCORRENCIA,
                    error_message="data_hora is required and must be valid"
                )

            # Build metadata
            metadata = {
                "source": source.value,
                "ingested_at": datetime.utcnow().isoformat(),
                "raw_data_hash": self._compute_hash(raw_data)
            }

            # Add optional fields
            for key in ["gravidade", "envolvidos", "latitude", "longitude"]:
                if key in raw_data:
                    metadata[key] = raw_data[key]

            # Create Ocorrencia entity
            ocorrencia = Ocorrencia(
                numero_bo=numero_bo,
                tipo=tipo,
                data_hora=data_hora,
                descricao=raw_data.get("descricao"),
                local_logradouro=self._normalize_text(raw_data.get("local_logradouro")),
                local_bairro=self._normalize_text(raw_data.get("local_bairro")),
                local_cidade=self._normalize_text(raw_data.get("local_cidade")),
                local_estado=raw_data.get("local_estado", "").upper() if raw_data.get("local_estado") else None,
                delegacia=raw_data.get("delegacia"),
                status=self._normalize_text(raw_data.get("status")),
                metadata=metadata
            )

            logger.info(f"Transformed Ocorrencia: {numero_bo} ({tipo})")

            return TransformResult(
                success=True,
                entity_type=EntityType.OCORRENCIA,
                entity_data=ocorrencia.model_dump(),
                relationships=[]
            )

        except Exception as e:
            logger.error(f"Error transforming Ocorrencia: {e}", exc_info=True)
            return TransformResult(
                success=False,
                entity_type=EntityType.OCORRENCIA,
                error_message=str(e)
            )

    # Normalization helpers

    def _normalize_cpf(self, cpf: Optional[str]) -> Optional[str]:
        """Normalize CPF: remove formatting, validate pattern."""
        if not cpf:
            return None

        # Remove formatting
        cpf_clean = re.sub(r'[^\d]', '', cpf)

        # Validate length
        if len(cpf_clean) != 11:
            return None

        return cpf_clean

    def _normalize_placa(self, placa: Optional[str]) -> Optional[str]:
        """Normalize license plate: uppercase, remove formatting."""
        if not placa:
            return None

        # Convert to uppercase and remove hyphens
        placa_clean = placa.upper().replace("-", "")

        # Validate pattern (old: ABC1234 or new: ABC1D23)
        if not re.match(r'^[A-Z]{3}\d{4}$|^[A-Z]{3}\d[A-Z]\d{2}$', placa_clean):
            return None

        return placa_clean

    def _normalize_rg(self, rg: Optional[str]) -> Optional[str]:
        """Normalize RG: remove formatting."""
        if not rg:
            return None
        return re.sub(r'[^\dX]', '', rg.upper())

    def _normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """Normalize phone: remove formatting."""
        if not phone:
            return None
        return re.sub(r'[^\d]', '', phone)

    def _normalize_cep(self, cep: Optional[str]) -> Optional[str]:
        """Normalize CEP: remove formatting."""
        if not cep:
            return None
        cep_clean = re.sub(r'[^\d]', '', cep)
        if len(cep_clean) != 8:
            return None
        return cep_clean

    def _normalize_chassi(self, chassi: Optional[str]) -> Optional[str]:
        """Normalize chassis: uppercase, no spaces."""
        if not chassi:
            return None
        return re.sub(r'\s+', '', chassi.upper())

    def _normalize_name(self, name: Optional[str]) -> Optional[str]:
        """Normalize person name: title case, trim."""
        if not name:
            return None
        return ' '.join(name.strip().title().split())

    def _normalize_text(self, text: Optional[str]) -> Optional[str]:
        """Normalize generic text: trim, title case."""
        if not text:
            return None
        return text.strip().title()

    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse date from various formats."""
        if not date_value:
            return None

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, str):
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue

        return None

    def _parse_datetime(self, dt_value: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if not dt_value:
            return None

        if isinstance(dt_value, datetime):
            return dt_value

        if isinstance(dt_value, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
            except:
                pass

            # Try other formats
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d"
            ]:
                try:
                    return datetime.strptime(dt_value, fmt)
                except ValueError:
                    continue

        return None

    def _parse_year(self, year_value: Any) -> Optional[int]:
        """Parse year from various formats."""
        if not year_value:
            return None

        if isinstance(year_value, int):
            return year_value if 1900 <= year_value <= 2100 else None

        if isinstance(year_value, str):
            try:
                year = int(year_value)
                return year if 1900 <= year <= 2100 else None
            except ValueError:
                return None

        return None

    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse float from various formats."""
        if not value:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None

        return None

    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute hash of raw data for deduplication."""
        import hashlib
        import json

        # Sort keys for consistent hashing
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
