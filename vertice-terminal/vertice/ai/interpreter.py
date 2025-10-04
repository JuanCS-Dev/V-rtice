"""
🧠 AI Interpreter - Natural Language → VeQL

Usa Gemini AI para traduzir perguntas em linguagem natural para queries VeQL.

Exemplo:
    "Show me all PowerShell processes making external connections"
    →
    "SELECT process.name, network.remote_ip FROM endpoints
     WHERE process.name = 'powershell.exe'
     AND network.remote_ip NOT IN ('127.0.0.1')"
"""

import os
from typing import Optional, Dict, Any, List
import google.generativeai as genai


class AIInterpreter:
    """
    Interpreta linguagem natural e gera VeQL queries
    """

    # Prompt do sistema que ensina VeQL ao Gemini
    SYSTEM_PROMPT = """You are an expert VeQL (Vértice Query Language) translator.

VeQL is a SQL-like language for threat hunting across endpoints.

Schema:
- TABLE: endpoints (represents all endpoints in the fleet)
- FIELDS:
  - process.name (string) - Process name
  - process.pid (int) - Process ID
  - process.parent (string) - Parent process name
  - process.cmdline (string) - Command line arguments
  - network.remote_ip (string) - Remote IP address
  - network.remote_port (int) - Remote port
  - network.local_port (int) - Local port
  - file.path (string) - File path
  - file.hash (string) - File hash
  - registry.key (string) - Registry key path
  - registry.value (string) - Registry value

Syntax:
SELECT <fields> FROM endpoints WHERE <conditions> [LIMIT <n>]

Operators: =, !=, >, <, >=, <=, IN, NOT IN, LIKE, AND, OR

Examples:
Q: "Show me all PowerShell processes"
A: SELECT process.name, process.pid FROM endpoints WHERE process.name = "powershell.exe"

Q: "Find processes making external network connections"
A: SELECT process.name, network.remote_ip FROM endpoints WHERE network.remote_ip NOT IN ("127.0.0.1", "0.0.0.0")

Q: "Show suspicious parent-child relationships"
A: SELECT process.name, process.parent FROM endpoints WHERE process.parent = "cmd.exe" OR process.parent = "powershell.exe"

IMPORTANT:
- Always use double quotes for strings
- Field names are case-sensitive
- Table name is always "endpoints"
- Return ONLY the VeQL query, nothing else
- If query is ambiguous, make reasonable assumptions
- Use LIMIT to prevent overwhelming results (default 100)

Now translate the following natural language query to VeQL:"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API key (default: GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY env var or pass api_key parameter."
            )

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

    def natural_to_veql(
        self,
        natural_query: str,
        context: Optional[List[str]] = None
    ) -> str:
        """
        Traduz linguagem natural para VeQL

        Args:
            natural_query: Pergunta em linguagem natural
            context: Contexto adicional (queries anteriores, etc)

        Returns:
            VeQL query gerada

        Raises:
            ValueError: Se não conseguir gerar query válida
        """
        # Monta prompt
        prompt = self.SYSTEM_PROMPT + "\n\n"

        # Adiciona contexto se houver
        if context:
            prompt += "Previous context:\n"
            for ctx in context[-3:]:  # Últimas 3 interações
                prompt += f"- {ctx}\n"
            prompt += "\n"

        prompt += f"User query: {natural_query}\n\nVeQL query:"

        # Chama Gemini
        try:
            response = self.model.generate_content(prompt)
            veql_query = response.text.strip()

            # Remove markdown code blocks se houver
            if veql_query.startswith("```"):
                lines = veql_query.split("\n")
                veql_query = "\n".join(lines[1:-1])

            # Remove prefixos comuns
            veql_query = veql_query.replace("VeQL:", "").strip()
            veql_query = veql_query.replace("Query:", "").strip()

            return veql_query

        except Exception as e:
            raise ValueError(f"Failed to generate VeQL: {e}")

    def explain_query(self, veql_query: str) -> str:
        """
        Explica uma VeQL query em linguagem natural

        Args:
            veql_query: Query VeQL

        Returns:
            Explicação em linguagem natural
        """
        prompt = f"""Explain this VeQL query in simple terms:

{veql_query}

Provide a concise 1-2 sentence explanation of what this query does."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Failed to explain query: {e}"

    def suggest_next_steps(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Sugere próximos passos baseado nos resultados

        Args:
            query: Query VeQL executada
            results: Resultados obtidos

        Returns:
            Lista de sugestões de próximos passos
        """
        # Analisa resultados
        num_results = len(results)

        if num_results == 0:
            return [
                "No results found. Try broadening your search criteria.",
                "Check if the field names are correct.",
                "Verify that endpoints are online and responding.",
            ]

        # Pega amostra dos resultados
        sample = results[:5]

        prompt = f"""Based on this threat hunting query and results, suggest 3 logical next investigation steps:

Query: {query}
Results count: {num_results}
Sample results: {sample}

Provide 3 actionable next steps for a security analyst."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Parse sugestões (assume que vêm numeradas)
            suggestions = []
            for line in text.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                    # Remove numeração/bullet
                    suggestion = line.lstrip("0123456789.-•) ").strip()
                    if suggestion:
                        suggestions.append(suggestion)

            return suggestions[:3]  # Máximo 3

        except Exception:
            return [
                "Investigate suspicious entries in the results",
                "Pivot to related entities",
                "Check for additional IOCs",
            ]

    def detect_threat_level(self, results: List[Dict[str, Any]]) -> str:
        """
        Detecta nível de ameaça baseado nos resultados

        Args:
            results: Resultados da query

        Returns:
            Nível de ameaça: LOW, MEDIUM, HIGH, CRITICAL
        """
        if not results:
            return "LOW"

        num_results = len(results)

        # Heurísticas simples
        if num_results > 50:
            return "CRITICAL"  # Muitas detecções = possível outbreak
        elif num_results > 20:
            return "HIGH"
        elif num_results > 5:
            return "MEDIUM"
        else:
            return "LOW"
