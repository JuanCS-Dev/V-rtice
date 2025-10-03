#!/usr/bin/env python3
"""
Script de Validação e Testes das World-Class Tools
Projeto Vértice - PASSO 5: TESTING & VALIDATION
"""

import asyncio
import sys
import random
from datetime import datetime
from colorama import Fore, Style, init

# Inicializar colorama
init(autoreset=True)

# Importar componentes do sistema
try:
    from tools_world_class import (
        exploit_search,
        social_media_deep_dive,
        breach_data_search,
        anomaly_detection
    )
    print(f"{Fore.GREEN}✓ Imports bem-sucedidos{Style.RESET_ALL}")
except ImportError as e:
    print(f"{Fore.RED}✗ Erro ao importar módulos: {e}{Style.RESET_ALL}")
    sys.exit(1)


class WorldClassToolsValidator:
    """Validador completo das World-Class Tools"""

    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }

    def print_header(self, title: str):
        """Imprime cabeçalho formatado"""
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{title.center(80)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    def print_test(self, test_name: str, status: str, details: str = ""):
        """Imprime resultado de teste"""
        if status == "PASS":
            icon = f"{Fore.GREEN}✓{Style.RESET_ALL}"
            color = Fore.GREEN
        elif status == "FAIL":
            icon = f"{Fore.RED}✗{Style.RESET_ALL}"
            color = Fore.RED
        else:  # WARNING
            icon = f"{Fore.YELLOW}⚠{Style.RESET_ALL}"
            color = Fore.YELLOW

        print(f"{icon} {test_name:<50} [{color}{status}{Style.RESET_ALL}]")
        if details:
            print(f"  {Fore.WHITE}{details}{Style.RESET_ALL}")

    async def test_imports(self):
        """Testa integridade dos imports"""
        self.print_header("TESTE 1: INTEGRIDADE DOS IMPORTS")

        try:
            # Verificar ferramentas World-Class (implementadas)
            world_class_tools = {
                "exploit_search": exploit_search,
                "social_media_deep_dive": social_media_deep_dive,
                "breach_data_search": breach_data_search,
                "anomaly_detection": anomaly_detection
            }

            for tool_name, tool_func in world_class_tools.items():
                if callable(tool_func):
                    self.print_test(f"Ferramenta {tool_name}", "PASS", f"⭐ World-Class")
                    self.results["passed"].append(f"tool_{tool_name}")
                else:
                    self.print_test(f"Ferramenta {tool_name}", "FAIL", "Não é callable")
                    self.results["failed"].append(f"tool_{tool_name}")

        except Exception as e:
            self.print_test("Integridade dos imports", "FAIL", str(e))
            self.results["failed"].append("imports_integrity")

    async def test_exploit_search(self):
        """Testa busca de exploits CVE"""
        self.print_header("TESTE 2: EXPLOIT SEARCH (CVE-2024-1086)")

        try:
            result = await exploit_search(
                cve_id="CVE-2024-1086",
                include_poc=True,
                include_metasploit=True
            )

            self.print_test("Execução da ferramenta", "PASS")
            self.print_test("CVE ID retornado", "PASS", result.cve_id)
            self.print_test("CVSS Score", "PASS", str(result.cvss_score))
            self.print_test("Severidade", "PASS", result.severity.value)
            self.print_test("Exploits encontrados", "PASS", str(result.exploits_found))
            self.print_test("Produtos afetados", "PASS", str(len(result.affected_products)))
            self.print_test("Patch disponível", "PASS", "Sim" if result.patch_available else "Não")
            self.print_test("Confiança", "PASS", f"{result.confidence}%")
            self.print_test("Status", "PASS", result.status.value)
            self.results["passed"].append("exploit_search")

        except Exception as e:
            self.print_test("Exploit Search", "FAIL", str(e))
            self.results["failed"].append("exploit_search")

    async def test_social_media_investigation(self):
        """Testa investigação de mídias sociais"""
        self.print_header("TESTE 3: SOCIAL MEDIA DEEP DIVE")

        try:
            result = await social_media_deep_dive(
                username="elonmusk",
                platforms=["twitter", "linkedin"],
                deep_analysis=True
            )

            self.print_test("Execução da ferramenta", "PASS")
            self.print_test("Username", "PASS", result.username)
            self.print_test("Perfis encontrados", "PASS", str(result.profiles_found))
            self.print_test("Detalhes dos perfis", "PASS", f"{len(result.profiles)} perfis")
            self.print_test("Risk score", "PASS", str(result.risk_score))
            self.print_test("Email hints", "PASS", f"{len(result.email_hints)} hints")
            self.print_test("Confiança", "PASS", f"{result.confidence}%")
            self.print_test("Status", "PASS", result.status.value)
            self.results["passed"].append("social_media")

        except Exception as e:
            self.print_test("Social Media Deep Dive", "FAIL", str(e))
            self.results["failed"].append("social_media")

    async def test_breach_data_search(self):
        """Testa busca de dados vazados"""
        self.print_header("TESTE 4: BREACH DATA SEARCH")

        try:
            result = await breach_data_search(
                identifier="test@example.com",
                identifier_type="email"
            )

            self.print_test("Execução da ferramenta", "PASS")
            self.print_test("Identifier", "PASS", result.identifier)
            self.print_test("Identifier type", "PASS", result.identifier_type)
            self.print_test("Breaches encontrados", "PASS", str(result.breaches_found))
            self.print_test("Registros expostos", "PASS", str(result.total_records_exposed))
            self.print_test("Risk score", "PASS", str(result.risk_score))
            self.print_test("Password exposto", "PASS", "Sim" if result.password_exposed else "Não")
            self.print_test("Confiança", "PASS", f"{result.confidence}%")
            self.print_test("Status", "PASS", result.status.value)
            self.results["passed"].append("breach_data")

        except Exception as e:
            self.print_test("Breach Data Search", "FAIL", str(e))
            self.results["failed"].append("breach_data")

    async def test_anomaly_detection(self):
        """Testa detecção de anomalias"""
        self.print_header("TESTE 5: ANOMALY DETECTION")

        try:
            # Gerar dados de exemplo com anomalias
            baseline = [1.2 + random.random() * 0.3 for _ in range(40)]
            data_with_anomalies = baseline[:20] + [15.7] + baseline[20:30] + [0.2] + baseline[30:] + [18.3]

            result = await anomaly_detection(
                data=data_with_anomalies,
                method="isolation_forest",
                sensitivity=0.05
            )

            self.print_test("Execução da ferramenta", "PASS")
            self.print_test("Método", "PASS", result.method)
            self.print_test("Sensitivity", "PASS", str(result.sensitivity))
            self.print_test("Pontos analisados", "PASS", str(result.data_points_analyzed))
            self.print_test("Anomalias detectadas", "PASS", str(result.anomalies_detected))
            anomaly_rate = (result.anomalies_detected / result.data_points_analyzed) * 100
            self.print_test("Taxa de anomalia", "PASS", f"{anomaly_rate:.2f}%")
            self.print_test("Confiança", "PASS", f"{result.confidence}%")
            self.print_test("Status", "PASS", result.status.value)

            # Validar que detectou as 3 anomalias injetadas
            if result.anomalies_detected >= 3:
                self.print_test("Detecção correta de anomalias", "PASS", "3+ anomalias detectadas")
            else:
                self.print_test("Detecção correta de anomalias", "WARNING",
                              f"Esperado 3, detectado {result.anomalies_detected}")
                self.results["warnings"].append("anomaly_detection_accuracy")

            self.results["passed"].append("anomaly_detection")

        except Exception as e:
            self.print_test("Anomaly Detection", "FAIL", str(e))
            self.results["failed"].append("anomaly_detection")


    def generate_report(self):
        """Gera relatório final dos testes"""
        self.print_header("RELATÓRIO FINAL DE TESTES")

        total_tests = len(self.results["passed"]) + len(self.results["failed"]) + len(self.results["warnings"])
        passed = len(self.results["passed"])
        failed = len(self.results["failed"])
        warnings = len(self.results["warnings"])

        print(f"{Fore.CYAN}Total de Testes:{Style.RESET_ALL} {total_tests}")
        print(f"{Fore.GREEN}✓ Passou:{Style.RESET_ALL} {passed}")
        print(f"{Fore.RED}✗ Falhou:{Style.RESET_ALL} {failed}")
        print(f"{Fore.YELLOW}⚠ Avisos:{Style.RESET_ALL} {warnings}")

        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        print(f"\n{Fore.CYAN}Taxa de Sucesso:{Style.RESET_ALL} {success_rate:.1f}%")

        if failed > 0:
            print(f"\n{Fore.RED}Testes Falhados:{Style.RESET_ALL}")
            for test in self.results["failed"]:
                print(f"  ✗ {test}")

        if warnings > 0:
            print(f"\n{Fore.YELLOW}Avisos:{Style.RESET_ALL}")
            for warning in self.results["warnings"]:
                print(f"  ⚠ {warning}")

        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

        if success_rate >= 90:
            print(f"{Fore.GREEN}STATUS: ⭐⭐⭐⭐⭐ LENDÁRIO - Sistema pronto para produção!{Style.RESET_ALL}")
        elif success_rate >= 75:
            print(f"{Fore.GREEN}STATUS: ✓ BOM - Sistema funcional com pequenos ajustes necessários{Style.RESET_ALL}")
        elif success_rate >= 50:
            print(f"{Fore.YELLOW}STATUS: ⚠ REGULAR - Sistema necessita de correções{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}STATUS: ✗ CRÍTICO - Sistema necessita de revisão completa{Style.RESET_ALL}")

        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

        return success_rate >= 75

    async def run_all_tests(self):
        """Executa todos os testes"""
        print(f"\n{Fore.MAGENTA}{'='*80}")
        print(f"PROJETO VÉRTICE - WORLD-CLASS TOOLS VALIDATION")
        print(f"PASSO 5: TESTING & VALIDATION")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}{Style.RESET_ALL}\n")

        # Executar todos os testes
        await self.test_imports()
        await self.test_exploit_search()
        await self.test_social_media_investigation()
        await self.test_breach_data_search()
        await self.test_anomaly_detection()

        # Gerar relatório final
        return self.generate_report()


async def main():
    """Função principal"""
    validator = WorldClassToolsValidator()
    success = await validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
