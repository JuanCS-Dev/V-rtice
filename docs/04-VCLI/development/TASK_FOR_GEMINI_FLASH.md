# 🤖 TAREFA PARA GEMINI FLASH - IMPLEMENTAÇÃO AUTÔNOMA

> **Desenvolvedor Autônomo:** Gemini Flash 1.5
> **Supervisor:** Claude (eu)
> **Nível de Dificuldade:** Júnior
> **Tempo Estimado:** 2-3 horas
> **Data:** 2025-10-02

---

## 📋 CONTEXTO

Você é o **Gemini Flash**, um modelo de IA que vai **implementar código sozinho**. Este documento contém instruções **EXTREMAMENTE DETALHADAS** para que você possa completar a tarefa sem supervisão humana constante.

**IMPORTANTE:**
- ⚠️ Leia CADA seção COMPLETAMENTE antes de começir
- ⚠️ Execute os comandos EXATAMENTE como escritos
- ⚠️ NÃO pule etapas
- ⚠️ Se algo der errado, PARE e reporte o erro

---

## 🎯 OBJETIVO DA TAREFA

**Implementar um sistema de "Auto-Documentação Inteligente"** que:

1. Lê todos os arquivos Python do projeto `vertice-terminal`
2. Usa VOCÊ MESMO (Gemini Flash) via API para gerar documentação
3. Cria arquivos `.md` com documentação completa de cada módulo
4. Gera um índice navegável com links

**Por que essa tarefa?**
- Você vai documentar o próprio código que está usando
- É recursivo e interessante
- Não afeta código crítico (só gera docs)
- Usa suas capacidades de análise de código

---

## 📁 ESTRUTURA DE ARQUIVOS

Você vai criar estes arquivos:

```
vertice-terminal/
├── autodoc/                          # NOVO - você vai criar
│   ├── __init__.py                  # Módulo Python
│   ├── analyzer.py                  # Analisa código
│   ├── gemini_documenter.py        # Usa API Gemini Flash
│   └── generator.py                 # Gera arquivos .md
├── docs/                            # NOVO - você vai criar
│   ├── index.md                     # Índice principal
│   └── modules/                     # Docs de cada módulo
│       ├── cli.md
│       ├── commands/
│       └── connectors/
└── requirements.txt                 # Atualizar com novas deps
```

---

## 🔧 PRÉ-REQUISITOS

### Verificação Inicial

**PROMPT PARA VOCÊ (Gemini Flash):**
```
Verifique se os seguintes arquivos existem executando comandos shell:

1. ls /home/juan/vertice-dev/vertice-terminal/
2. ls /home/juan/vertice-dev/.env
3. cat /home/juan/vertice-dev/.env | grep GEMINI_API_KEY

Se GEMINI_API_KEY estiver presente, responda: "✅ Pré-requisitos OK"
Se não estiver, responda: "❌ GEMINI_API_KEY não encontrada"
```

---

## 📝 IMPLEMENTAÇÃO - PASSO A PASSO

### ETAPA 1: Criar Estrutura de Diretórios

**COMANDO EXATO:**
```bash
cd /home/juan/vertice-dev/vertice-terminal
mkdir -p autodoc docs/modules
touch autodoc/__init__.py
```

**PROMPT DE VALIDAÇÃO:**
```
Execute: ls -la autodoc/
Execute: ls -la docs/

Se ambos existirem, responda: "✅ Etapa 1 completa"
Caso contrário, reporte o erro completo.
```

---

### ETAPA 2: Criar `autodoc/analyzer.py`

**PROMPT PARA VOCÊ:**
```
Crie o arquivo /home/juan/vertice-dev/vertice-terminal/autodoc/analyzer.py com o seguinte código:

IMPORTANTE:
- Use EXATAMENTE este código
- NÃO modifique nada
- Copie e cole

CÓDIGO:
```python
"""
Analyzer - Analisa arquivos Python do projeto.
"""
import os
import ast
from pathlib import Path
from typing import List, Dict, Any


class CodeAnalyzer:
    """Analisa estrutura de código Python."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def find_python_files(self) -> List[Path]:
        """Encontra todos os arquivos .py no projeto."""
        python_files = []

        # Ignora estas pastas
        ignore_dirs = {'__pycache__', 'venv', '.venv', 'dist', 'build', '.git'}

        for file_path in self.base_path.rglob('*.py'):
            # Verifica se está em pasta ignorada
            if any(ignored in file_path.parts for ignored in ignore_dirs):
                continue
            python_files.append(file_path)

        return sorted(python_files)

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analisa um arquivo Python e extrai informações."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Extrai informações
            info = {
                'path': str(file_path.relative_to(self.base_path)),
                'content': content,
                'functions': [],
                'classes': [],
                'imports': [],
                'docstring': ast.get_docstring(tree) or ""
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    info['functions'].append({
                        'name': node.name,
                        'docstring': ast.get_docstring(node) or "",
                        'line': node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    info['classes'].append({
                        'name': node.name,
                        'docstring': ast.get_docstring(node) or "",
                        'line': node.lineno
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        info['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        info['imports'].append(node.module)

            return info

        except Exception as e:
            return {
                'path': str(file_path.relative_to(self.base_path)),
                'error': str(e),
                'content': ''
            }

    def analyze_all(self) -> List[Dict[str, Any]]:
        """Analisa todos os arquivos Python."""
        files = self.find_python_files()
        results = []

        for file_path in files:
            results.append(self.analyze_file(file_path))

        return results
```

Após criar o arquivo, execute:
cat /home/juan/vertice-dev/vertice-terminal/autodoc/analyzer.py | wc -l

Se retornar ~80 linhas, responda: "✅ Etapa 2 completa - analyzer.py criado"
```

---

### ETAPA 3: Criar `autodoc/gemini_documenter.py`

**PROMPT PARA VOCÊ:**
```
Crie o arquivo /home/juan/vertice-dev/vertice-terminal/autodoc/gemini_documenter.py

IMPORTANTE: Este arquivo usa SUA PRÓPRIA API (Gemini Flash) para gerar documentação!

CÓDIGO:
```python
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
```

Após criar, execute:
python -c "from autodoc.gemini_documenter import GeminiDocumenter; doc = GeminiDocumenter(); print('✅ Gemini Documenter inicializado')"

Se funcionar, responda: "✅ Etapa 3 completa - gemini_documenter.py criado e testado"
```

---

### ETAPA 4: Criar `autodoc/generator.py`

**PROMPT PARA VOCÊ:**
```
Crie o arquivo /home/juan/vertice-dev/vertice-terminal/autodoc/generator.py

CÓDIGO:
```python
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
```

Após criar, responda: "✅ Etapa 4 completa - generator.py criado"
```

---

### ETAPA 5: Atualizar `requirements.txt`

**PROMPT PARA VOCÊ:**
```
Execute estes comandos EXATAMENTE:

cd /home/juan/vertice-dev/vertice-terminal

# Verifica se google-generativeai já está
grep "google-generativeai" requirements.txt

# Se NÃO estiver, adicione:
echo "google-generativeai>=0.3.0" >> requirements.txt

# Instale
pip install google-generativeai python-dotenv

Responda: "✅ Etapa 5 completa - Dependências instaladas"
```

---

### ETAPA 6: EXECUTAR A DOCUMENTAÇÃO

**PROMPT PARA VOCÊ:**
```
Agora você vai EXECUTAR seu próprio código e gerar a documentação!

Execute EXATAMENTE:

cd /home/juan/vertice-dev/vertice-terminal
python -m autodoc.generator

IMPORTANTE:
- Isso vai levar alguns minutos
- Você vai chamar SUA PRÓPRIA API várias vezes
- Cada arquivo Python será documentado

Monitore a saída e reporte:
1. Quantos arquivos foram processados
2. Se houve algum erro
3. Onde a documentação foi salva

Quando terminar, responda:
"✅ Etapa 6 completa - Documentação gerada!
Processados: [N] arquivos
Localização: /home/juan/vertice-dev/vertice-terminal/docs/"
```

---

### ETAPA 7: Validação Final

**PROMPT PARA VOCÊ:**
```
Valide que tudo funcionou:

1. Liste arquivos gerados:
   ls -la /home/juan/vertice-dev/vertice-terminal/docs/
   ls -la /home/juan/vertice-dev/vertice-terminal/docs/modules/

2. Conte quantos arquivos .md foram criados:
   find /home/juan/vertice-dev/vertice-terminal/docs -name "*.md" | wc -l

3. Mostre preview do índice:
   head -20 /home/juan/vertice-dev/vertice-terminal/docs/index.md

4. Mostre preview de UMA documentação gerada:
   head -30 /home/juan/vertice-dev/vertice-terminal/docs/modules/cli.md

Se tudo estiver OK, responda:
"✅ TAREFA COMPLETA!
- [N] arquivos .md gerados
- Índice criado
- Preview OK"
```

---

## 🎯 CRITÉRIOS DE SUCESSO

Você terá completado a tarefa com sucesso se:

- [ ] Todos os 4 arquivos Python foram criados em `autodoc/`
- [ ] `docs/index.md` foi gerado
- [ ] Pelo menos 10 arquivos `.md` foram gerados em `docs/modules/`
- [ ] Não houve erros durante a execução
- [ ] A documentação está em Markdown válido
- [ ] Os links no índice funcionam

---

## ⚠️ TRATAMENTO DE ERROS

### Se der erro de API Key:
```bash
cat /home/juan/vertice-dev/.env | grep GEMINI
# Verifique se GEMINI_API_KEY está presente
```

### Se der erro de importação:
```bash
pip install -r requirements.txt
```

### Se der erro de permissão:
```bash
chmod -R 755 /home/juan/vertice-dev/vertice-terminal/autodoc/
```

### Se travar ou demorar muito:
- Você provavelmente está fazendo muitas chamadas de API
- Adicione `time.sleep(1)` entre chamadas em `generator.py`

---

## 📊 RELATÓRIO FINAL

Ao terminar, gere um relatório com:

```markdown
# 📋 RELATÓRIO DE EXECUÇÃO - Auto-Documentação

**Data:** [data]
**Executor:** Gemini Flash 1.5
**Status:** ✅ Sucesso / ❌ Falha

## Estatísticas

- Arquivos Python analisados: [N]
- Documentações geradas: [N]
- Tempo total: [X] minutos
- Chamadas de API: ~[N]

## Arquivos Criados

- `autodoc/analyzer.py` - ✅
- `autodoc/gemini_documenter.py` - ✅
- `autodoc/generator.py` - ✅
- `docs/index.md` - ✅
- `docs/modules/*.md` - ✅ ([N] arquivos)

## Erros Encontrados

[Liste erros ou "Nenhum"]

## Observações

[Qualquer comentário sobre a execução]

---

**Auto-assinado:** 🤖 Gemini Flash
```

Salve este relatório em: `/home/juan/vertice-dev/vertice-terminal/docs/EXECUTION_REPORT.md`

---

## 🚀 COMEÇAR AGORA

**PRIMEIRO PROMPT PARA VOCÊ (Gemini Flash):**

```
Eu sou o Gemini Flash e vou executar a tarefa de auto-documentação.

Começando pela Etapa 1:

[Execute os comandos da Etapa 1 aqui]
```

**BOA SORTE, GEMINI FLASH! 🤖**

---

*Criado por: Claude (Sonnet 4.5)*
*Para: Gemini Flash 1.5*
*Projeto: Vertice Terminal*
