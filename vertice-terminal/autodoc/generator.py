"""
Generator - Gera arquivos de documentação Markdown.
"""
from pathlib import Path
from typing import List, Dict, Any
from autodoc.analyzer import CodeAnalyzer
from autodoc.gemini_documenter import GeminiDocumenter


class DocumentationGenerator:
    """Orquestra a geração de documentação."""

    def __init__(self, project_path: str, output_path: str):
        self.project_path = Path(project_path)
        self.output_path = Path(output_path)
        self.analyzer = CodeAnalyzer(project_path)
        self.documenter = GeminiDocumenter()

    def generate_all(self):
        """Gera documentação para todos os arquivos."""
        print("🔍 Analisando arquivos Python...")
        file_infos = self.analyzer.analyze_all()

        print(f"📝 Encontrados {len(file_infos)} arquivos Python")

        # Cria estrutura de pastas
        self.output_path.mkdir(parents=True, exist_ok=True)

        index_content = "# 📚 Documentação do Vertice Terminal\n\n"
        index_content += "## 📋 Índice de Módulos\n\n"

        for idx, file_info in enumerate(file_infos, 1):
            print(f"📄 [{idx}/{len(file_infos)}] Documentando: {file_info['path']}")

            # Gera documentação com Gemini
            doc_content = self.documenter.generate_documentation(file_info)

            # Caminho do arquivo de documentação
            relative_path = Path(file_info['path'])
            doc_filename = relative_path.with_suffix('.md').name
            doc_path = self.output_path / 'modules' / doc_filename

            # Cria subdiretórios se necessário
            doc_path.parent.mkdir(parents=True, exist_ok=True)

            # Salva documentação
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)

            # Adiciona ao índice
            link_path = f"modules/{doc_filename}"
            index_content += f"- [{file_info['path']}]({link_path})\n"

        # Salva índice
        index_path = self.output_path / 'index.md'
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)

        print(f"\n✅ Documentação gerada em: {self.output_path}")
        print(f"📖 Índice: {index_path}")


if __name__ == "__main__":
    generator = DocumentationGenerator(
        project_path="/home/juan/vertice-dev/vertice-terminal/vertice",
        output_path="/home/juan/vertice-dev/vertice-terminal/docs"
    )
    generator.generate_all()
