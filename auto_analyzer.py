# auto_analyzer.py

import os
import json
import subprocess
from datetime import datetime
import re

# ============================================================================ 
# CONFIGURAÇÃO
# ============================================================================ 

PROJECT_ROOT = "/home/juan/vertice-dev/vertice-terminal"
REPORTS_DIR = os.path.join(PROJECT_ROOT, "security_analysis")

# Comandos das ferramentas com output em JSON, se possível
# Usamos tee para capturar o output e o exit code de forma mais confiável
LINTER_CMD = "flake8 --format=json"
FORMATTER_CMD = "black --check ."
TYPE_CHECKER_CMD = "mypy . --ignore-missing-imports --pretty"
SECURITY_SCANNER_CMD = "bandit -r . -f json"
# Safety não foi encontrado, então o comando permanece um placeholder
DEPENDENCY_SCANNER_CMD = "echo '{\"error\": \"safety tool not found\"}'"

ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL")

# ============================================================================ 
# FUNÇÕES PARSERS
# ============================================================================ 

def parse_flake8_json(output):
    """Parseia o output JSON do flake8."""
    try:
        # O flake8-json retorna um JSON por linha
        lines = output.strip().splitlines()
        data = [json.loads(line) for line in lines]
        summary = {
            "total_errors": len(data),
            "errors_by_code": {}
        }
        for error in data:
            code = error.get("code")
            summary["errors_by_code"][code] = summary["errors_by_code"].get(code, 0) + 1
        return summary
    except (json.JSONDecodeError, IndexError):
        return {"error": "Failed to parse flake8 JSON output", "raw_output": output}

def parse_bandit_json(output):
    """Parseia o output JSON do bandit."""
    try:
        data = json.loads(output)
        summary = {
            "total_issues": data["metrics"]["_totals"]["Issues"],
            "by_severity": {
                "LOW": data["metrics"]["_totals"]["SEVERITY.LOW"],
                "MEDIUM": data["metrics"]["_totals"]["SEVERITY.MEDIUM"],
                "HIGH": data["metrics"]["_totals"]["SEVERITY.HIGH"],
            }
        }
        return summary
    except (json.JSONDecodeError, KeyError):
        return {"error": "Failed to parse bandit JSON output", "raw_output": output}

def parse_black_output(output):
    """Parseia o output do black --check."""
    files_to_reformat = len(re.findall(r"would reformat", output))
    return {"files_needing_reformat": files_to_reformat}

def parse_mypy_output(output):
    """Parseia o output do mypy."""
    found_errors = re.search(r"Found (\d+) errors? in (\d+) files?", output)
    if found_errors:
        return {"total_errors": int(found_errors.group(1)), "files_with_errors": int(found_errors.group(2))}
    elif "Success: no issues found" in output:
        return {"total_errors": 0, "files_with_errors": 0}
    else:
        return {"error": "Could not parse mypy output", "raw_output": output}

# ============================================================================ 
# CLASSE PRINCIPAL DO ANALISADOR
# ============================================================================ 

class AutoAnalyzer:
    """Sistema de Análise de Regressão de Segurança e Qualidade."""

    def __init__(self, project_path, reports_path):
        self.project_path = project_path
        self.reports_path = reports_path
        os.makedirs(self.reports_path, exist_ok=True)
        self.current_report = None
        self.previous_report = None

    def run_analysis(self):
        """Orquestra a execução de todas as ferramentas de análise."""
        print("🚀 Iniciando análise automática...")
        
        analysis_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "linter": self._run_tool("Linter (flake8)", LINTER_CMD, parse_flake8_json),
            "formatter": self._run_tool("Formatter (black)", FORMATTER_CMD, parse_black_output),
            "type_checker": self._run_tool("Type Checker (mypy)", TYPE_CHECKER_CMD, parse_mypy_output),
            "security_scan": self._run_tool("Security Scanner (bandit)", SECURITY_SCANNER_CMD, parse_bandit_json),
            "dependency_scan": json.loads(DEPENDENCY_SCANNER_CMD) # Simples placeholder
        }

        self.current_report = analysis_result
        self._save_report(analysis_result)
        print("✅ Análise concluída.")

    def compare_and_alert(self):
        """Compara o relatório atual com o anterior e envia alertas."""
        print("🔍 Comparando relatórios e procurando por regressões...")
        self.previous_report = self._load_previous_report()

        if not self.previous_report:
            print("⚠️ Relatório anterior não encontrado. Pulando comparação.")
            return

        regressions = self._find_regressions()

        if regressions:
            print(f"🚨 {len(regressions)} regressões detectadas!")
            self._send_alerts(regressions)
        else:
            print("🎉 Nenhuma regressão detectada.")

    def _run_tool(self, name, command, parser_func):
        """Executa uma ferramenta e parseia seu output."""
        print(f"  - Executando {name}...")
        try:
            # Usamos shell=True por simplicidade, mas em produção, seria melhor passar os args como lista
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=self.project_path)
            # Ferramentas de lint/check podem retornar non-zero exit code para indicar issues, o que não é um erro de execução
            return parser_func(result.stdout or result.stderr)
        except Exception as e:
            return {"error": f"Falha ao executar o comando: {e}"}

    def _find_regressions(self):
        """Lógica para encontrar regressões."""
        regressions = []
        prev = self.previous_report
        curr = self.current_report

        # 1. Regressão de Linting
        if curr["linter"].get("total_errors", 0) > prev["linter"].get("total_errors", 0):
            regressions.append({
                "metric": "Linter Errors",
                "previous_value": prev["linter"].get("total_errors", 0),
                "current_value": curr["linter"].get("total_errors", 0),
                "description": "O número de erros de linting aumentou."
            })

        # 2. Regressão de Formatação
        if curr["formatter"].get("files_needing_reformat", 0) > 0:
            regressions.append({
                "metric": "Code Formatting",
                "previous_value": 0,
                "current_value": curr["formatter"].get("files_needing_reformat", 0),
                "description": "Novos arquivos precisam de reformatação."
            })

        # 3. Regressão de Segurança (Bandit)
        if curr["security_scan"].get("total_issues", 0) > prev["security_scan"].get("total_issues", 0):
            regressions.append({
                "metric": "Bandit Security Issues",
                "previous_value": prev["security_scan"].get("total_issues", 0),
                "current_value": curr["security_scan"].get("total_issues", 0),
                "description": "Novas issues de segurança foram detectadas pelo Bandit."
            })

        return regressions

    def _send_alerts(self, regressions):
        """Envia alertas detalhados para um webhook."""
        if not ALERT_WEBHOOK_URL:
            print("\n⚠️ Webhook de alerta não configurado. Exibindo payload do alerta no console:")
        else:
            print(f"\n📤 Enviando {len(regressions)} alertas para o webhook...")

        report_summary = f"Análise de {self.current_report['timestamp']} detectou {len(regressions)} regressões desde a última análise."
        
        fields = []
        for reg in regressions:
            fields.append({
                "title": f"🚨 {reg['metric']}",
                "value": f"Valor anterior: `{reg['previous_value']}` | Valor atual: `{reg['current_value']}`\n{reg['description']}",
                "short": False
            })

        message = {
            "username": "Vértice Auto-Analyzer",
            "icon_url": "https://i.imgur.com/g340k3p.png",
            "text": report_summary,
            "attachments": [{
                "color": "#ff0000",
                "fields": fields
            }]
        }
        
        # Em uma implementação real, faríamos a requisição POST aqui
        # import requests
        # try:
        #     requests.post(ALERT_WEBHOOK_URL, json=message)
        #     print("✅ Alertas enviados com sucesso.")
        # except Exception as e:
        #     print(f"❌ Erro ao enviar alertas: {e}")
        print(json.dumps(message, indent=2))

    def _save_report(self, report_data):
        report_path = os.path.join(self.reports_path, f"auto_analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"📄 Relatório salvo em: {report_path}")

    def _load_previous_report(self):
        try:
            report_files = sorted([f for f in os.listdir(self.reports_path) if f.startswith("auto_analysis_")])
            if len(report_files) > 1:
                with open(os.path.join(self.reports_path, report_files[-2]), 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, IndexError, json.JSONDecodeError):
            return None

if __name__ == "__main__":
    analyzer = AutoAnalyzer(PROJECT_ROOT, REPORTS_DIR)
    analyzer.run_analysis()
    analyzer.compare_and_alert()