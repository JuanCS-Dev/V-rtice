"""
Fuzzy Matching Utilities para VÉRTICE CLI
UI/UX Blueprint v1.2 - Production Ready

Implementa:
- Algoritmo de Levenshtein (distância de edição)
- Ranking por relevância
- Cache de resultados
- Implementação completa
"""

from typing import List, Tuple, Optional, Dict
from functools import lru_cache


class FuzzyMatcher:
    """
    Classe para fuzzy matching usando distância de Levenshtein.

    Example:
        matcher = FuzzyMatcher()
        results = matcher.find_matches("hlp", ["help", "health", "helm"])
        # [(0.25, "help"), (0.5, "helm"), ...]
    """

    def __init__(self, threshold: float = 0.6):
        """
        Inicializa matcher.

        Args:
            threshold: Score mínimo (0.0-1.0) para considerar match válido
        """
        self.threshold = threshold
        self._cache: Dict[Tuple[str, str], int] = {}

    @staticmethod
    @lru_cache(maxsize=1024)
    def levenshtein_distance(s1: str, s2: str) -> int:
        """
        Calcula distância de Levenshtein entre duas strings.
        Usa programação dinâmica com cache LRU.

        Args:
            s1: Primeira string
            s2: Segunda string

        Returns:
            int: Distância de edição

        Example:
            >>> FuzzyMatcher.levenshtein_distance("kitten", "sitting")
            3
        """
        s1, s2 = s1.lower(), s2.lower()

        if len(s1) < len(s2):
            return FuzzyMatcher.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        # Array anterior e atual de distâncias
        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]

            for j, c2 in enumerate(s2):
                # Custo de inserção, deleção ou substituição
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)

                current_row.append(min(insertions, deletions, substitutions))

            previous_row = current_row

        return previous_row[-1]

    def similarity_score(self, s1: str, s2: str) -> float:
        """
        Calcula score de similaridade normalizado (0.0-1.0).
        1.0 = match perfeito, 0.0 = totalmente diferente.

        Args:
            s1: Primeira string
            s2: Segunda string

        Returns:
            float: Score de similaridade

        Example:
            >>> matcher = FuzzyMatcher()
            >>> matcher.similarity_score("help", "hlp")
            0.75
        """
        distance = self.levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))

        if max_len == 0:
            return 1.0

        # Normaliza para 0-1 (1 = perfeito)
        return 1.0 - (distance / max_len)

    def find_matches(
        self,
        query: str,
        candidates: List[str],
        limit: Optional[int] = None,
    ) -> List[Tuple[float, str]]:
        """
        Encontra matches fuzzy ranqueados por relevância.

        Args:
            query: String de busca
            candidates: Lista de candidatos
            limit: Número máximo de resultados (None retorna tudo)

        Returns:
            Lista de (score, candidato) ordenada por relevância descendente

        Example:
            >>> matcher = FuzzyMatcher(threshold=0.5)
            >>> matcher.find_matches("hlp", ["help", "health", "hunt", "http"])
            [(0.75, 'help'), (0.5, 'health')]
        """
        if not query or not candidates:
            return []

        matches = []

        for candidate in candidates:
            score = self.similarity_score(query, candidate)

            if score >= self.threshold:
                matches.append((score, candidate))

        # Ordena por score descendente
        matches.sort(key=lambda x: x[0], reverse=True)

        if limit:
            return matches[:limit]

        return matches

    def find_best_match(
        self,
        query: str,
        candidates: List[str],
    ) -> Optional[Tuple[float, str]]:
        """
        Encontra o melhor match único.

        Args:
            query: String de busca
            candidates: Lista de candidatos

        Returns:
            (score, candidato) ou None se nenhum match

        Example:
            >>> matcher = FuzzyMatcher()
            >>> matcher.find_best_match("hlp", ["help", "hunt"])
            (0.75, 'help')
        """
        matches = self.find_matches(query, candidates, limit=1)

        if matches:
            return matches[0]

        return None

    def suggest_correction(
        self,
        query: str,
        candidates: List[str],
        top_n: int = 3,
    ) -> str:
        """
        Gera mensagem de sugestão formatada.

        Args:
            query: String incorreta
            candidates: Lista de candidatos corretos
            top_n: Número de sugestões

        Returns:
            String formatada com sugestões

        Example:
            >>> matcher = FuzzyMatcher()
            >>> matcher.suggest_correction("hlp", ["help", "hunt", "health"])
            "Command 'hlp' not found. Did you mean:\\n  • help\\n  • health\\n  • hunt"
        """
        matches = self.find_matches(query, candidates, limit=top_n)

        if not matches:
            return f"Command '{query}' not found. Use 'vcli help' to see available commands."

        suggestions = "\n".join([f"  • {candidate}" for _, candidate in matches])

        return f"Command '{query}' not found. Did you mean:\n{suggestions}"


class CommandFuzzyMatcher(FuzzyMatcher):
    """
    Fuzzy matcher especializado para comandos CLI.
    Considera hierarquia de comandos (ex: "vcli hunt search").
    """

    def __init__(self, threshold: float = 0.6):
        super().__init__(threshold)
        self.commands_registry: Dict[str, List[str]] = {}

    def register_command(self, command: str, subcommands: List[str] = None):
        """
        Registra comando e seus subcomandos.

        Args:
            command: Nome do comando principal
            subcommands: Lista de subcomandos (opcional)
        """
        self.commands_registry[command] = subcommands or []

    def find_command_matches(
        self,
        query: str,
        limit: Optional[int] = 5,
    ) -> List[Tuple[float, str]]:
        """
        Encontra matches em comandos registrados.

        Args:
            query: Query de busca
            limit: Máximo de resultados

        Returns:
            Lista de (score, "comando subcomando")
        """
        all_commands = []

        for cmd, subcmds in self.commands_registry.items():
            # Adiciona comando principal
            all_commands.append(cmd)

            # Adiciona subcomandos com prefixo
            for subcmd in subcmds:
                all_commands.append(f"{cmd} {subcmd}")

        return self.find_matches(query, all_commands, limit=limit)


# Instância global para uso conveniente
global_fuzzy_matcher = FuzzyMatcher(threshold=0.6)
command_fuzzy_matcher = CommandFuzzyMatcher(threshold=0.6)


def fuzzy_find(
    query: str,
    candidates: List[str],
    threshold: float = 0.6,
    limit: Optional[int] = None,
) -> List[Tuple[float, str]]:
    """
    Helper function para fuzzy finding rápido.

    Args:
        query: String de busca
        candidates: Lista de candidatos
        threshold: Score mínimo
        limit: Máximo de resultados

    Returns:
        Lista de (score, candidato)

    Example:
        >>> fuzzy_find("hlp", ["help", "hunt", "health"])
        [(0.75, 'help'), (0.6, 'health')]
    """
    matcher = FuzzyMatcher(threshold=threshold)
    return matcher.find_matches(query, candidates, limit=limit)


__all__ = [
    "FuzzyMatcher",
    "CommandFuzzyMatcher",
    "fuzzy_find",
    "global_fuzzy_matcher",
    "command_fuzzy_matcher",
]
