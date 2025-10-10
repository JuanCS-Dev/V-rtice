#!/bin/bash

# ==============================================================================
#  SCRIPT DE SETUP AUTOMÁTICO PARA A FERRAMENTA `vertice-cli`
#  Cria a estrutura de diretórios e arquivos iniciais.
#  Projeto: VÉRTICE
# ==============================================================================

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CLI_DIR="vertice_cli"

echo -e "${GREEN}Iniciando a estruturação da ferramenta '${YELLOW}${CLI_DIR}${NC}'...${NC}"

# --- 1. Verificação e Criação do Diretório ---
if [ -d "$CLI_DIR" ]; then
    echo -e "${YELLOW}Aviso: O diretório '${CLI_DIR}' já existe. Nenhuma ação será tomada para evitar sobrescrever arquivos.${NC}"
    exit 1
fi
mkdir -p $CLI_DIR
echo -e "-> Diretório '${GREEN}${CLI_DIR}${NC}' criado."

# --- 2. Gerando requirements.txt ---
cat <<EOF > ${CLI_DIR}/requirements.txt
typer[all]
python-dotenv
google-generativeai
EOF
echo -e "-> Arquivo '${GREEN}requirements.txt${NC}' gerado."

# --- 3. Gerando .env.example ---
cat <<EOF > ${CLI_DIR}/.env.example
GEMINI_API_KEY="SUA_CHAVE_API_VEM_AQUI"
EOF
echo -e "-> Arquivo '${GREEN}.env.example${NC}' gerado."

# --- 4. Gerando o código principal cli.py ---
# Usamos 'EOF' com aspas para garantir que o conteúdo seja escrito literalmente,
# sem que o shell tente interpretar variáveis como $PATH.
cat <<'EOF' > ${CLI_DIR}/cli.py
import typer
import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Carrega as variáveis de ambiente (sua API key)
load_dotenv()

# Configura a API
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
except KeyError:
    print("🚨 Erro: A variável de ambiente GEMINI_API_KEY não foi encontrada.")
    print("Crie um arquivo '.env' a partir do '.env.example' e insira sua chave.")
    raise typer.Exit()
except Exception as e:
    print(f"🚨 Erro ao configurar a API Gemini: {e}")
    raise typer.Exit()

app = typer.Typer(help="CLI para automação de desenvolvimento do Projeto VÉRTICE, com a IA Gemini.")

@app.command()
def ask(prompt: str):
    """
    Envia um prompt genérico diretamente para o Gemini Pro.
    """
    print("🧠 Pensando...")
    try:
        response = model.generate_content(prompt)
        print("\n✨ Gemini Pro Responde:")
        print(response.text)
    except Exception as e:
        print(f"🚨 Erro ao gerar conteúdo: {e}")

@app.command()
def review(file_path: Path = typer.Argument(..., help="O caminho para o arquivo a ser analisado.")):
    """
    Pede ao Gemini para fazer um code review de um arquivo local.
    """
    print(f"🔎 Analisando o arquivo: {file_path}")

    if not file_path.is_file():
        print(f"🚨 Erro: O arquivo '{file_path}' não foi encontrado ou não é um arquivo válido.")
        raise typer.Exit()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Criando um prompt mais estruturado para a IA
        prompt = f"""
        Como um programador sênior e arquiteto de software, faça um code review detalhado,
        pragmático e direto ao ponto do seguinte arquivo de código.
        Identifique possíveis bugs, melhorias de performance, e sugestões de refatoração ou estilo.

        Arquivo: `{file_path.name}`
        ---
        ```python
        {content}
        ```
        ---
        Análise:
        """

        print("🧠 Enviando para análise do Gemini Pro...")
        response = model.generate_content(prompt)

        print("\n✅ Análise Concluída:")
        print(response.text)

    except Exception as e:
        print(f"🚨 Ocorreu um erro durante a análise: {e}")


if __name__ == "__main__":
    app()
EOF
echo -e "-> Código principal '${GREEN}cli.py${NC}' gerado."

echo -e "\n${GREEN}=====================================================${NC}"
echo -e "${GREEN}      Estrutura do VÉRTICE CLI criada com sucesso!     ${NC}"
echo -e "${GREEN}=====================================================${NC}"
