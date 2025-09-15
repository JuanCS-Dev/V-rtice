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
