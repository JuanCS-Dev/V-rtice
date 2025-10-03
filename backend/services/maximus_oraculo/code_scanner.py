"""
Code Scanner - MAXIMUS Code Analysis
=====================================

Escaneia o codebase do MAXIMUS para auto-análise.

Capacidades:
- Escaneia todos os arquivos Python/JS/MD do MAXIMUS
- Filtra arquivos relevantes
- Extrai código e contexto
- Prepara para análise LLM
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CodeFile:
    """Representa um arquivo de código"""
    path: str
    relative_path: str
    extension: str
    size_bytes: int
    lines_of_code: int
    content: str
    last_modified: datetime
    is_core: bool  # Se é parte crítica do MAXIMUS


class CodeScanner:
    """
    Escaneia codebase do MAXIMUS para auto-análise

    Features:
    - Scan recursivo de diretórios
    - Filtros por extensão
    - Exclusão de node_modules, venv, etc
    - Priorização de arquivos core
    """

    # Diretórios do MAXIMUS
    MAXIMUS_SERVICES = [
        "maximus_core_service",
        "maximus_orchestrator_service",
        "maximus_predict",
        "maximus_oraculo"
    ]

    # Extensões relevantes
    RELEVANT_EXTENSIONS = [".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".yaml", ".yml"]

    # Diretórios a ignorar
    EXCLUDE_DIRS = [
        "node_modules",
        "venv",
        "__pycache__",
        ".git",
        "build",
        "dist",
        ".pytest_cache",
        "coverage"
    ]

    # Arquivos core críticos
    CORE_FILES = [
        "main.py",
        "reasoning_engine.py",
        "memory_system.py",
        "tools_world_class.py",
        "tool_orchestrator.py",
        "oraculo.py"
    ]

    def __init__(self, base_path: str = "/home/juan/vertice-dev/backend/services"):
        self.base_path = Path(base_path)
        self.scanned_files: List[CodeFile] = []

    def scan_maximus_codebase(self) -> List[CodeFile]:
        """
        Escaneia todo o codebase do MAXIMUS

        Returns:
            Lista de arquivos CodeFile
        """
        logger.info("🔍 Iniciando scan do codebase MAXIMUS...")

        self.scanned_files = []

        # Escaneia cada serviço MAXIMUS
        for service in self.MAXIMUS_SERVICES:
            service_path = self.base_path / service

            if not service_path.exists():
                logger.warning(f"Serviço não encontrado: {service}")
                continue

            logger.info(f"📂 Escaneando: {service}")
            self._scan_directory(service_path)

        # Ordena por prioridade (core files primeiro)
        self.scanned_files.sort(key=lambda f: (not f.is_core, f.size_bytes), reverse=True)

        logger.info(
            f"✅ Scan completo: {len(self.scanned_files)} arquivos | "
            f"{sum(f.lines_of_code for f in self.scanned_files)} LOC"
        )

        return self.scanned_files

    def _scan_directory(self, directory: Path):
        """Escaneia diretório recursivamente"""
        try:
            for item in directory.iterdir():
                # Ignora diretórios excluídos
                if item.is_dir():
                    if item.name in self.EXCLUDE_DIRS:
                        continue
                    self._scan_directory(item)

                # Processa arquivos relevantes
                elif item.is_file():
                    if item.suffix in self.RELEVANT_EXTENSIONS:
                        code_file = self._process_file(item)
                        if code_file:
                            self.scanned_files.append(code_file)

        except PermissionError:
            logger.warning(f"Sem permissão para acessar: {directory}")
        except Exception as e:
            logger.error(f"Erro ao escanear {directory}: {e}")

    def _process_file(self, file_path: Path) -> Optional[CodeFile]:
        """Processa arquivo individual"""
        try:
            # Lê conteúdo
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Conta linhas de código (ignora linhas vazias e comentários)
            lines = content.split('\n')
            loc = sum(
                1 for line in lines
                if line.strip() and not line.strip().startswith(('#', '//', '/*', '*'))
            )

            # Determina se é arquivo core
            is_core = file_path.name in self.CORE_FILES

            # Cria objeto CodeFile
            return CodeFile(
                path=str(file_path),
                relative_path=str(file_path.relative_to(self.base_path)),
                extension=file_path.suffix,
                size_bytes=file_path.stat().st_size,
                lines_of_code=loc,
                content=content,
                last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
                is_core=is_core
            )

        except Exception as e:
            logger.error(f"Erro ao processar {file_path}: {e}")
            return None

    def get_core_files(self) -> List[CodeFile]:
        """Retorna apenas arquivos core críticos"""
        return [f for f in self.scanned_files if f.is_core]

    def get_files_by_extension(self, extension: str) -> List[CodeFile]:
        """Filtra arquivos por extensão"""
        return [f for f in self.scanned_files if f.extension == extension]

    def build_context_for_llm(
        self,
        max_files: int = 10,
        max_total_chars: int = 50000,
        prioritize_core: bool = True
    ) -> str:
        """
        Constrói contexto otimizado para análise LLM

        Args:
            max_files: Máximo de arquivos a incluir
            max_total_chars: Máximo de caracteres total
            prioritize_core: Priorizar arquivos core

        Returns:
            String formatada para LLM
        """
        files_to_include = self.scanned_files[:max_files]

        context_parts = []
        total_chars = 0

        for code_file in files_to_include:
            # Header do arquivo
            header = f"""
{'='*80}
FILE: {code_file.relative_path}
TYPE: {'CORE' if code_file.is_core else 'SUPPORTING'}
SIZE: {code_file.lines_of_code} LOC
MODIFIED: {code_file.last_modified.strftime('%Y-%m-%d')}
{'='*80}

"""

            file_context = header + code_file.content

            # Verifica limite de caracteres
            if total_chars + len(file_context) > max_total_chars:
                # Trunca conteúdo
                remaining = max_total_chars - total_chars
                file_context = file_context[:remaining] + "\n\n[TRUNCADO]"
                context_parts.append(file_context)
                break

            context_parts.append(file_context)
            total_chars += len(file_context)

        return "\n\n".join(context_parts)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do scan"""
        return {
            'total_files': len(self.scanned_files),
            'core_files': len(self.get_core_files()),
            'total_loc': sum(f.lines_of_code for f in self.scanned_files),
            'total_size_mb': sum(f.size_bytes for f in self.scanned_files) / 1024 / 1024,
            'by_extension': {
                ext: len(self.get_files_by_extension(ext))
                for ext in self.RELEVANT_EXTENSIONS
            },
            'largest_files': [
                {'path': f.relative_path, 'loc': f.lines_of_code}
                for f in sorted(self.scanned_files, key=lambda x: x.lines_of_code, reverse=True)[:5]
            ]
        }


# Função helper
def scan_maximus() -> List[CodeFile]:
    """Helper function para scan rápido"""
    scanner = CodeScanner()
    return scanner.scan_maximus_codebase()


if __name__ == "__main__":
    # Teste standalone
    logging.basicConfig(level=logging.INFO)

    scanner = CodeScanner()
    files = scanner.scan_maximus_codebase()

    print("\n📊 ESTATÍSTICAS DO SCAN:")
    stats = scanner.get_stats()
    print(f"Total de arquivos: {stats['total_files']}")
    print(f"Arquivos core: {stats['core_files']}")
    print(f"Linhas de código: {stats['total_loc']:,}")
    print(f"Tamanho total: {stats['total_size_mb']:.2f} MB")

    print("\n🔥 ARQUIVOS CORE:")
    for f in scanner.get_core_files():
        print(f"  - {f.relative_path} ({f.lines_of_code} LOC)")

    print("\n📝 CONTEXTO LLM (sample):")
    context = scanner.build_context_for_llm(max_files=2, max_total_chars=2000)
    print(context[:1000] + "...")
