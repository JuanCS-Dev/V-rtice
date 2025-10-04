"""
🔧 Tool Calling Framework - AI executa comandos Vértice

Permite que a IA invoque comandos do Vértice de forma segura.
"""

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from enum import Enum


class ToolApprovalMode(Enum):
    """Modo de aprovação de ferramentas"""
    ALWAYS_ASK = "always_ask"  # Sempre pede aprovação
    AUTO_SAFE = "auto_safe"    # Auto-executa ferramentas seguras
    YOLO = "yolo"              # Auto-executa tudo (perigoso!)


@dataclass
class Tool:
    """Ferramenta disponível para a IA"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]
    is_safe: bool = True  # Se pode auto-executar no modo AUTO_SAFE
    requires_confirmation: bool = False


class ToolRegistry:
    """
    Registry de ferramentas disponíveis para a IA
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Any],
        is_safe: bool = True,
        requires_confirmation: bool = False,
    ) -> None:
        """
        Registra ferramenta

        Args:
            name: Nome da ferramenta
            description: Descrição para a IA
            function: Função Python a executar
            parameters: Schema dos parâmetros
            is_safe: Se é segura para auto-execução
            requires_confirmation: Se requer confirmação do usuário
        """
        tool = Tool(
            name=name,
            description=description,
            function=function,
            parameters=parameters,
            is_safe=is_safe,
            requires_confirmation=requires_confirmation,
        )

        self.tools[name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Busca ferramenta por nome"""
        return self.tools.get(name)

    def list_tools(self) -> List[Tool]:
        """Lista todas as ferramentas"""
        return list(self.tools.values())

    def get_tool_descriptions(self) -> str:
        """
        Retorna descrições de ferramentas para prompt da IA

        Returns:
            String formatada com todas as ferramentas
        """
        descriptions = []

        for tool in self.tools.values():
            desc = f"""Tool: {tool.name}
Description: {tool.description}
Parameters: {tool.parameters}
Safe: {tool.is_safe}
"""
            descriptions.append(desc)

        return "\n".join(descriptions)


class ToolCaller:
    """
    Executor de ferramentas para a IA
    """

    def __init__(
        self,
        registry: ToolRegistry,
        approval_mode: ToolApprovalMode = ToolApprovalMode.ALWAYS_ASK,
    ):
        """
        Args:
            registry: Registry de ferramentas
            approval_mode: Modo de aprovação
        """
        self.registry = registry
        self.approval_mode = approval_mode
        self.execution_log: List[Dict[str, Any]] = []

    def call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        auto_approve: bool = False,
    ) -> Any:
        """
        Executa ferramenta

        Args:
            tool_name: Nome da ferramenta
            parameters: Parâmetros para passar
            auto_approve: Se True, pula aprovação

        Returns:
            Resultado da execução

        Raises:
            ValueError: Se ferramenta não existir ou aprovação negada
        """
        tool = self.registry.get(tool_name)

        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        # Verifica se precisa aprovação
        needs_approval = self._needs_approval(tool)

        if needs_approval and not auto_approve:
            approved = self._request_approval(tool, parameters)

            if not approved:
                raise ValueError(f"Execution of {tool_name} denied by user")

        # Executa
        try:
            result = tool.function(**parameters)

            # Log execução
            self.execution_log.append({
                "tool": tool_name,
                "parameters": parameters,
                "result": str(result)[:200],  # Trunca resultado
                "success": True,
            })

            return result

        except Exception as e:
            # Log erro
            self.execution_log.append({
                "tool": tool_name,
                "parameters": parameters,
                "error": str(e),
                "success": False,
            })

            raise

    def _needs_approval(self, tool: Tool) -> bool:
        """Verifica se ferramenta precisa aprovação"""
        if self.approval_mode == ToolApprovalMode.YOLO:
            return False

        if self.approval_mode == ToolApprovalMode.ALWAYS_ASK:
            return True

        # AUTO_SAFE mode
        return not tool.is_safe or tool.requires_confirmation

    def _request_approval(self, tool: Tool, parameters: Dict[str, Any]) -> bool:
        """
        Pede aprovação ao usuário (implementação simplificada)

        Args:
            tool: Ferramenta a executar
            parameters: Parâmetros

        Returns:
            True se aprovado, False caso contrário
        """
        print(f"\n⚠️  AI wants to execute: {tool.name}")
        print(f"   Description: {tool.description}")
        print(f"   Parameters: {parameters}")

        response = input("\nApprove execution? (y/n): ").strip().lower()

        return response in ["y", "yes"]


def register_default_tools(registry: ToolRegistry) -> None:
    """
    Registra ferramentas padrão do Vértice

    Args:
        registry: Registry para registrar ferramentas
    """
    # Ferramenta de query VeQL (segura)
    def execute_veql(query: str) -> str:
        """Executa VeQL query"""
        # Esta função seria chamada pelo AI para executar queries
        return f"Executing VeQL: {query}"

    registry.register(
        name="execute_veql_query",
        description="Execute a VeQL query across the fleet to hunt for threats",
        function=execute_veql,
        parameters={"query": "string - VeQL query to execute"},
        is_safe=True,
        requires_confirmation=False,
    )

    # Ferramenta de bloqueio de IP (não segura - requer confirmação)
    def block_ip(ip_address: str) -> str:
        """Bloqueia IP no firewall"""
        return f"Blocking IP: {ip_address}"

    registry.register(
        name="block_ip_address",
        description="Block an IP address at the network perimeter (DESTRUCTIVE)",
        function=block_ip,
        parameters={"ip_address": "string - IP to block"},
        is_safe=False,
        requires_confirmation=True,
    )

    # Ferramenta de isolamento de endpoint (não segura)
    def isolate_endpoint(endpoint_id: str) -> str:
        """Isola endpoint da rede"""
        return f"Isolating endpoint: {endpoint_id}"

    registry.register(
        name="isolate_endpoint",
        description="Isolate an endpoint from the network (DESTRUCTIVE)",
        function=isolate_endpoint,
        parameters={"endpoint_id": "string - Endpoint ID to isolate"},
        is_safe=False,
        requires_confirmation=True,
    )
