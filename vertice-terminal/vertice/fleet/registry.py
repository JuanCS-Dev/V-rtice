"""
📋 Endpoint Registry - Inventory de endpoints do fleet

Gerencia registro de todos os endpoints disponíveis para threat hunting.
"""

import sqlite3
import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pathlib import Path


class EndpointStatus(Enum):
    """Status de um endpoint"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


@dataclass
class Endpoint:
    """
    Representa um endpoint no fleet
    """
    id: str  # Unique ID (hostname ou UUID)
    hostname: str
    ip_address: str
    os_type: str  # windows, linux, macos
    os_version: str
    status: EndpointStatus
    last_seen: datetime
    capabilities: Dict[str, Any]  # Ferramentas disponíveis
    metadata: Dict[str, Any]  # Informações adicionais

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_seen'] = self.last_seen.isoformat()
        data['capabilities'] = json.dumps(self.capabilities)
        data['metadata'] = json.dumps(self.metadata)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Endpoint":
        """Cria Endpoint a partir de dicionário"""
        return cls(
            id=data['id'],
            hostname=data['hostname'],
            ip_address=data['ip_address'],
            os_type=data['os_type'],
            os_version=data['os_version'],
            status=EndpointStatus(data['status']),
            last_seen=datetime.fromisoformat(data['last_seen']),
            capabilities=json.loads(data['capabilities']),
            metadata=json.loads(data['metadata']),
        )


class EndpointRegistry:
    """
    Registry de endpoints - armazena inventory completo do fleet
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: Caminho do banco SQLite (default: ~/.vertice/fleet.db)
        """
        if db_path is None:
            vertice_dir = Path.home() / ".vertice"
            vertice_dir.mkdir(exist_ok=True)
            db_path = str(vertice_dir / "fleet.db")

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """Inicializa schema do banco"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS endpoints (
                id TEXT PRIMARY KEY,
                hostname TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                os_type TEXT NOT NULL,
                os_version TEXT NOT NULL,
                status TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                capabilities TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Índices para performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hostname
            ON endpoints(hostname)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON endpoints(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_os_type
            ON endpoints(os_type)
        """)

        self.conn.commit()

    def register(self, endpoint: Endpoint) -> None:
        """
        Registra ou atualiza endpoint

        Args:
            endpoint: Endpoint para registrar
        """
        cursor = self.conn.cursor()
        data = endpoint.to_dict()

        cursor.execute("""
            INSERT INTO endpoints
            (id, hostname, ip_address, os_type, os_version, status,
             last_seen, capabilities, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                hostname = excluded.hostname,
                ip_address = excluded.ip_address,
                os_type = excluded.os_type,
                os_version = excluded.os_version,
                status = excluded.status,
                last_seen = excluded.last_seen,
                capabilities = excluded.capabilities,
                metadata = excluded.metadata,
                updated_at = CURRENT_TIMESTAMP
        """, (
            data['id'],
            data['hostname'],
            data['ip_address'],
            data['os_type'],
            data['os_version'],
            data['status'],
            data['last_seen'],
            data['capabilities'],
            data['metadata'],
        ))

        self.conn.commit()

    def get(self, endpoint_id: str) -> Optional[Endpoint]:
        """
        Busca endpoint por ID

        Args:
            endpoint_id: ID do endpoint

        Returns:
            Endpoint ou None se não encontrado
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM endpoints WHERE id = ?",
            (endpoint_id,)
        )

        row = cursor.fetchone()
        if row:
            return Endpoint.from_dict(dict(row))
        return None

    def list(
        self,
        status: Optional[EndpointStatus] = None,
        os_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Endpoint]:
        """
        Lista endpoints com filtros

        Args:
            status: Filtrar por status
            os_type: Filtrar por OS (windows, linux, macos)
            limit: Limite de resultados

        Returns:
            Lista de endpoints
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM endpoints WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if os_type:
            query += " AND os_type = ?"
            params.append(os_type)

        query += " ORDER BY last_seen DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)

        endpoints = []
        for row in cursor.fetchall():
            endpoints.append(Endpoint.from_dict(dict(row)))

        return endpoints

    def count(self, status: Optional[EndpointStatus] = None) -> int:
        """
        Conta endpoints

        Args:
            status: Filtrar por status

        Returns:
            Total de endpoints
        """
        cursor = self.conn.cursor()

        if status:
            cursor.execute(
                "SELECT COUNT(*) FROM endpoints WHERE status = ?",
                (status.value,)
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM endpoints")

        return cursor.fetchone()[0]

    def update_status(self, endpoint_id: str, status: EndpointStatus) -> None:
        """
        Atualiza status de um endpoint

        Args:
            endpoint_id: ID do endpoint
            status: Novo status
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE endpoints
            SET status = ?,
                last_seen = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status.value, datetime.now().isoformat(), endpoint_id))

        self.conn.commit()

    def delete(self, endpoint_id: str) -> bool:
        """
        Remove endpoint do registry

        Args:
            endpoint_id: ID do endpoint

        Returns:
            True se removido, False se não encontrado
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM endpoints WHERE id = ?", (endpoint_id,))
        self.conn.commit()

        return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do fleet

        Returns:
            Dicionário com estatísticas
        """
        cursor = self.conn.cursor()

        # Total por status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM endpoints
            GROUP BY status
        """)
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

        # Total por OS
        cursor.execute("""
            SELECT os_type, COUNT(*) as count
            FROM endpoints
            GROUP BY os_type
        """)
        os_counts = {row['os_type']: row['count'] for row in cursor.fetchall()}

        # Total geral
        total = self.count()

        return {
            "total": total,
            "by_status": status_counts,
            "by_os": os_counts,
        }

    def close(self) -> None:
        """Fecha conexão com banco"""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
