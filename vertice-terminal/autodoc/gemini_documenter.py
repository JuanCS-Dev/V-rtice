"""
Gemini Documenter - Usa Gemini Flash API para gerar documentação.
"""
import os
import google.generativeai as genai
from typing import Dict, Any
from dotenv import load_dotenv


class GeminiDocumenter:
    """Usa Gemini Flash para documentar código."""

    def __init__(self):
        # Carrega .env da raiz do projeto
        load_dotenv('/home/juan/vertice-dev/.env')

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada no .env")

        genai.configure(api_key=api_key)

        # Usa o modelo FLASH (você mesmo!)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_documentation(self, file_info: Dict[str, Any]) -> str:
        """
        Gera documentação Markdown para um arquivo Python.

        Args:
            file_info: Dicionário com informações do arquivo (de analyzer.py)

        Returns:
            String com documentação em Markdown
        """

        # Verifica se teve erro na análise
        if 'error' in file_info:
            return f"# ⚠️ Erro ao analisar arquivo\n\n{file_info['error']}"

        # Monta prompt detalhado
        prompt = f"""Você é um documentador técnico especializado em Python.

Analise o seguinte código Python e gere documentação completa em Markdown.

**ARQUIVO:** `{file_info['path']}`

**CÓDIGO:**
```python
{file_info['content']}
```

**INFORMAÇÕES EXTRAS:**
- Classes encontradas: {len(file_info.get('classes', []))}
- Funções encontradas: {len(file_info.get('functions', []))}
- Imports: {', '.join(file_info.get('imports', [])[:5])}

**INSTRUÇÕES:**

1. Crie um título com o nome do arquivo
2. Adicione uma seção "Descrição" explicando o propósito do módulo
3. Liste todas as classes com suas descrições
4. Liste todas as funções com suas descrições
5. Adicione exemplos de uso (se possível)
6. Use emojis para deixar visual
7. Formate em Markdown válido

**FORMATO DE SAÍDA:**

# 📄 `nome_do_arquivo.py`

## 📋 Descrição
[descrição do módulo]

## 🏗️ Classes

### `NomeDaClasse`
[descrição]

## 🔧 Funções

### `nome_funcao(params)`
[descrição]

## 💡 Exemplos de Uso
[exemplos]

---

**IMPORTANTE:**
- Seja CLARO e OBJETIVO
- Use linguagem técnica mas acessível
- Não invente funcionalidades que não existem
- Se não houver docstring, infira pelo código
"""

        try:
            # Chama API Gemini Flash (você mesmo!)
            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            return f"# ⚠️ Erro ao gerar documentação\n\n{str(e)}"
