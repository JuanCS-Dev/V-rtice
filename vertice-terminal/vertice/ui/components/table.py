"""
📊 Table Widget Primoroso
Tabela avançada com sorting, filtering, pagination
"""

from textual.widgets import DataTable
from textual.reactive import reactive
from rich.text import Text
from typing import List, Dict, Any, Optional, Callable

from ..themes import THEME


class VerticeTable(DataTable):
    """
    Tabela primorosa com features avançadas.
    Suporta sorting, filtering, pagination e gradientes.
    """

    DEFAULT_CSS = """
    VerticeTable {
        border: solid $primary;
        background: $panel;
        height: 100%;
    }

    VerticeTable > .datatable--header {
        background: $surface;
        color: $primary;
        text-style: bold;
    }

    VerticeTable > .datatable--cursor {
        background: $accent 30%;
    }

    VerticeTable > .datatable--hover {
        background: $surface;
    }
    """

    # Estado reativo
    sort_column: reactive[Optional[str]] = reactive(None)
    sort_reverse: reactive[bool] = reactive(False)
    filter_text: reactive[str] = reactive("")
    current_page: reactive[int] = reactive(0)
    page_size: reactive[int] = reactive(50)

    def __init__(
        self,
        show_header: bool = True,
        show_cursor: bool = True,
        zebra_stripes: bool = True,
        *args,
        **kwargs
    ):
        super().__init__(
            show_header=show_header,
            show_cursor=show_cursor,
            zebra_stripes=zebra_stripes,
            *args,
            **kwargs
        )
        self._full_data: List[Dict[str, Any]] = []
        self._filtered_data: List[Dict[str, Any]] = []

    def load_data(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> None:
        """
        Carrega dados na tabela.

        Args:
            data: Lista de dicionários com dados
            columns: Lista de colunas (keys) a mostrar. Se None, usa todas.
        """
        if not data:
            return

        self._full_data = data
        self._filtered_data = data.copy()

        # Define colunas
        if columns is None:
            columns = list(data[0].keys()) if data else []

        # Limpa tabela
        self.clear(columns=True)

        # Adiciona colunas com gradiente
        for idx, col in enumerate(columns):
            # Gradiente para header
            from ...utils.banner import create_gradient_text
            colors = THEME.get_gradient_colors()
            num_cols = len(columns)
            color_idx = int((idx / num_cols) * (len(colors) - 1)) if num_cols > 1 else 0

            col_gradient = create_gradient_text(
                col.upper(),
                [colors[color_idx], colors[min(color_idx + 1, len(colors) - 1)]]
            )
            self.add_column(col_gradient, key=col)

        # Adiciona linhas
        self._render_page()

    def _render_page(self) -> None:
        """Renderiza página atual"""
        # Calcula range da página
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size

        # Pega dados da página
        page_data = self._filtered_data[start_idx:end_idx]

        # Remove linhas antigas
        self.clear(columns=False)

        # Adiciona linhas da página
        for row_dict in page_data:
            row_values = []
            for col in self.columns.keys():
                value = row_dict.get(col, "")

                # Formata valor
                if isinstance(value, bool):
                    symbol = THEME.symbols.SUCCESS if value else THEME.symbols.ERROR
                    color = THEME.colors.SUCCESS if value else THEME.colors.ERROR
                    text = Text(symbol, style=color)
                elif isinstance(value, (int, float)):
                    text = Text(str(value), style=THEME.colors.CIANO_BRILHO)
                else:
                    text = Text(str(value), style=THEME.colors.BRANCO)

                row_values.append(text)

            self.add_row(*row_values)

    def sort_by_column(self, column: str, reverse: bool = False) -> None:
        """Ordena por coluna"""
        if column in [col.value for col in self.columns.values()]:
            self.sort_column = column
            self.sort_reverse = reverse

            # Ordena dados filtrados
            try:
                self._filtered_data.sort(
                    key=lambda x: x.get(column, ""),
                    reverse=reverse
                )
                self._render_page()
            except Exception:
                # Se falhar ordenação, ignora
                pass

    def filter_data(self, filter_func: Callable[[Dict[str, Any]], bool]) -> None:
        """
        Filtra dados com função customizada.

        Args:
            filter_func: Função que retorna True para linhas que devem ser mostradas
        """
        self._filtered_data = [row for row in self._full_data if filter_func(row)]
        self.current_page = 0
        self._render_page()

    def search(self, text: str) -> None:
        """
        Busca texto em todas as colunas.

        Args:
            text: Texto para buscar
        """
        if not text:
            self._filtered_data = self._full_data.copy()
        else:
            text_lower = text.lower()
            self._filtered_data = [
                row for row in self._full_data
                if any(text_lower in str(value).lower() for value in row.values())
            ]

        self.current_page = 0
        self._render_page()

    def next_page(self) -> None:
        """Próxima página"""
        max_page = len(self._filtered_data) // self.page_size
        if self.current_page < max_page:
            self.current_page += 1
            self._render_page()

    def previous_page(self) -> None:
        """Página anterior"""
        if self.current_page > 0:
            self.current_page -= 1
            self._render_page()

    def get_selected_row(self) -> Optional[Dict[str, Any]]:
        """Retorna linha selecionada"""
        if self.cursor_row >= 0:
            data_idx = (self.current_page * self.page_size) + self.cursor_row
            if data_idx < len(self._filtered_data):
                return self._filtered_data[data_idx]
        return None

    def get_page_info(self) -> str:
        """Retorna info da paginação"""
        total_pages = (len(self._filtered_data) - 1) // self.page_size + 1
        total_rows = len(self._filtered_data)
        return f"Page {self.current_page + 1}/{total_pages} | Total: {total_rows} rows"
