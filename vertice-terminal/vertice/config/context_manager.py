"""
Sistema de Contextos do Vértice CLI
Inspirado no sistema de contextos do kubectl

Permite gerenciar múltiplos engagements/projetos com contextos isolados
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import tomli
import tomli_w
from dataclasses import dataclass, asdict


@dataclass
class Context:
    """Representa um contexto de engajamento"""
    name: str
    target: str
    output_dir: str
    created_at: str
    updated_at: str
    proxy: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (para TOML)"""
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}


class ContextError(Exception):
    """Exceção para erros de contexto"""
    pass


class ContextManager:
    """Gerenciador de contextos"""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            self.config_dir = Path.home() / ".config" / "vertice"
        else:
            self.config_dir = Path(config_dir)

        self.contexts_file = self.config_dir / "contexts.toml"
        self.current_file = self.config_dir / "current-context"

        # Criar diretórios se não existirem
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar arquivos se não existirem
        if not self.contexts_file.exists():
            self._init_contexts_file()

    def _init_contexts_file(self):
        """Inicializa arquivo de contextos vazio"""
        with open(self.contexts_file, 'wb') as f:
            tomli_w.dump({"contexts": {}}, f)

    def _load_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Carrega todos os contextos do arquivo TOML"""
        if not self.contexts_file.exists():
            return {}

        with open(self.contexts_file, 'rb') as f:
            data = tomli.load(f)
            return data.get("contexts", {})

    def _save_contexts(self, contexts: Dict[str, Dict[str, Any]]):
        """Salva contextos no arquivo TOML"""
        with open(self.contexts_file, 'wb') as f:
            tomli_w.dump({"contexts": contexts}, f)

    def create(
        self,
        name: str,
        target: str,
        output_dir: Optional[str] = None,
        proxy: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_use: bool = True
    ) -> Context:
        """
        Cria um novo contexto

        Args:
            name: Nome do contexto (ex: pentest-acme)
            target: Alvo do engagement (IP, range, domain)
            output_dir: Diretório de output (auto-criado se não existir)
            proxy: Proxy HTTP (opcional)
            notes: Notas sobre o engagement
            metadata: Metadados adicionais
            auto_use: Se True, ativa o contexto automaticamente

        Returns:
            Context criado

        Raises:
            ContextError: Se contexto já existir
        """
        contexts = self._load_contexts()

        if name in contexts:
            raise ContextError(f"Contexto '{name}' já existe")

        # Validar nome
        if not name or not name.replace('-', '').replace('_', '').isalnum():
            raise ContextError(
                f"Nome de contexto inválido: '{name}'. "
                "Use apenas letras, números, hífens e underscores"
            )

        # Output dir padrão
        if output_dir is None:
            output_dir = str(Path.home() / "vertice-engagements" / name)

        # Expandir ~ e criar diretório
        output_path = Path(output_dir).expanduser()
        output_path.mkdir(parents=True, exist_ok=True)

        # Criar subdiretórios padrão
        (output_path / "scans").mkdir(exist_ok=True)
        (output_path / "recon").mkdir(exist_ok=True)
        (output_path / "exploits").mkdir(exist_ok=True)
        (output_path / "loot").mkdir(exist_ok=True)
        (output_path / "reports").mkdir(exist_ok=True)

        now = datetime.now().isoformat()

        context = Context(
            name=name,
            target=target,
            output_dir=str(output_path),
            created_at=now,
            updated_at=now,
            proxy=proxy,
            notes=notes,
            metadata=metadata or {}
        )

        contexts[name] = context.to_dict()
        self._save_contexts(contexts)

        if auto_use:
            self.use(name)

        return context

    def list(self) -> List[Context]:
        """Lista todos os contextos"""
        contexts = self._load_contexts()
        return [Context(**ctx_data) for ctx_data in contexts.values()]

    def get(self, name: str) -> Optional[Context]:
        """Obtém um contexto específico"""
        contexts = self._load_contexts()
        ctx_data = contexts.get(name)

        if ctx_data is None:
            return None

        return Context(**ctx_data)

    def use(self, name: str):
        """
        Ativa um contexto

        Args:
            name: Nome do contexto

        Raises:
            ContextError: Se contexto não existir
        """
        contexts = self._load_contexts()

        if name not in contexts:
            raise ContextError(
                f"Contexto '{name}' não existe. "
                f"Use 'vertice context list' para ver contextos disponíveis"
            )

        # Salvar contexto atual
        with open(self.current_file, 'w') as f:
            f.write(name)

    def get_current(self) -> Optional[Context]:
        """Retorna o contexto atual (ativo)"""
        if not self.current_file.exists():
            return None

        with open(self.current_file, 'r') as f:
            current_name = f.read().strip()

        if not current_name:
            return None

        return self.get(current_name)

    def get_current_name(self) -> Optional[str]:
        """Retorna o nome do contexto atual"""
        current = self.get_current()
        return current.name if current else None

    def delete(self, name: str, delete_files: bool = False):
        """
        Deleta um contexto

        Args:
            name: Nome do contexto
            delete_files: Se True, deleta também os arquivos do output_dir

        Raises:
            ContextError: Se contexto não existir ou estiver ativo
        """
        contexts = self._load_contexts()

        if name not in contexts:
            raise ContextError(f"Contexto '{name}' não existe")

        # Verificar se é o contexto atual
        current_name = self.get_current_name()
        if current_name == name:
            raise ContextError(
                f"Não é possível deletar o contexto ativo '{name}'. "
                "Use outro contexto primeiro: vertice context use <outro>"
            )

        # Deletar arquivos se solicitado
        if delete_files:
            output_dir = Path(contexts[name]["output_dir"])
            if output_dir.exists():
                import shutil
                shutil.rmtree(output_dir)

        # Remover do arquivo
        del contexts[name]
        self._save_contexts(contexts)

    def update(
        self,
        name: str,
        target: Optional[str] = None,
        proxy: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Atualiza um contexto existente

        Args:
            name: Nome do contexto
            target: Novo alvo (opcional)
            proxy: Novo proxy (opcional)
            notes: Novas notas (opcional)
            metadata: Novos metadados (opcional)

        Raises:
            ContextError: Se contexto não existir
        """
        contexts = self._load_contexts()

        if name not in contexts:
            raise ContextError(f"Contexto '{name}' não existe")

        ctx = contexts[name]

        if target is not None:
            ctx["target"] = target
        if proxy is not None:
            ctx["proxy"] = proxy
        if notes is not None:
            ctx["notes"] = notes
        if metadata is not None:
            if "metadata" not in ctx:
                ctx["metadata"] = {}
            ctx["metadata"].update(metadata)

        ctx["updated_at"] = datetime.now().isoformat()

        contexts[name] = ctx
        self._save_contexts(contexts)

    def require_context(self) -> Context:
        """
        Requer que um contexto esteja ativo
        Usa-se em comandos que precisam de contexto

        Returns:
            Contexto atual

        Raises:
            ContextError: Se nenhum contexto estiver ativo
        """
        current = self.get_current()

        if current is None:
            raise ContextError(
                "Nenhum contexto ativo.\n"
                "Crie um contexto: vertice context create <name> --target <target>\n"
                "Ou ative um existente: vertice context use <name>"
            )

        return current


# Singleton global
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Retorna instância singleton do ContextManager"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
