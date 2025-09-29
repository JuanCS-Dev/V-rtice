# vertice_cli/modules/cyber.py

import typer
import questionary
from rich.table import Table
from rich.panel import Panel
from ..utils.api_client import VerticeAPI
from ..utils import console, print_success, print_error, print_info, print_warning

app = typer.Typer(help="🛡️ Cyber Security Module - Ferramentas de segurança ofensiva e defensiva")

@app.command()
def menu():
    """🛡️ Menu interativo do módulo Cyber Security"""
    console.print(Panel.fit(
        "[bold cyan]🛡️ VÉRTICE CYBER SECURITY MODULE[/bold cyan]\n"
        "[dim]Ferramentas avançadas para análise e testes de segurança[/dim]\n"
        "\n"
        "[yellow]Exemplos de uso:[/yellow]\n"
        "[dim]• cyber ip-intel --target 8.8.8.8[/dim]\n"
        "[dim]• cyber domain --domain google.com[/dim]\n"
        "[dim]• cyber vuln-scan --target 192.168.1.1 --type quick[/dim]",
        style="cyan"
    ))

    choices = [
        "🌐 IP Intelligence & Geolocation - Análise completa de endereços IP",
        "🔍 Domain Analysis - WHOIS, DNS, certificados SSL",
        "🎯 Vulnerability Scanner [OFENSIVO] - Descoberta de vulnerabilidades",
        "🎭 Social Engineering Toolkit [OFENSIVO] - Simulação de ataques",
        "📚 Ver exemplos e documentação",
        "🔙 Voltar ao menu principal"
    ]

    choice = questionary.select(
        "Selecione uma ferramenta:",
        choices=choices
    ).ask()

    if "IP Intelligence" in choice:
        show_ip_help()
        ip_intel()
    elif "Domain Analysis" in choice:
        show_domain_help()
        domain_analysis()
    elif "Vulnerability Scanner" in choice:
        show_vuln_help()
        vuln_scanner()
    elif "Social Engineering" in choice:
        show_social_help()
        social_eng()
    elif "exemplos" in choice:
        show_examples()
    else:
        return

@app.command()
def ip_intel(target: str = typer.Option(None, "--target", "-t", help="IP para análise")):
    """🌐 Análise de IP Intelligence e Geolocalização"""
    if not target:
        target = questionary.text("Digite o IP para análise:").ask()

    print_info(f"Analisando IP: {target}")

    # TODO: Implementar chamada para API
    api = VerticeAPI()
    result = api.analyze_ip(target)

    if result:
        print_success("Análise concluída!")
        # TODO: Formatar e exibir resultados
    else:
        print_error("Falha na análise do IP")

@app.command()
def domain_analysis(domain: str = typer.Option(None, "--domain", "-d", help="Domínio para análise")):
    """🔍 Análise completa de domínio"""
    if not domain:
        domain = questionary.text("Digite o domínio para análise:").ask()

    print_info(f"Analisando domínio: {domain}")
    # TODO: Implementar

@app.command()
def vuln_scanner():
    """🎯 Vulnerability Scanner - FERRAMENTA OFENSIVA"""
    console.print(Panel.fit(
        "[bold red]⚠️ FERRAMENTA OFENSIVA ⚠️[/bold red]\n"
        "[yellow]Uso autorizado apenas em sistemas próprios ou com permissão explícita[/yellow]",
        style="red"
    ))

    confirm = questionary.confirm("Confirma que tem autorização para usar esta ferramenta?").ask()
    if not confirm:
        print_warning("Operação cancelada pelo usuário")
        return

    # TODO: Implementar vulnerability scanner
    print_info("Vulnerability Scanner - Em implementação")

@app.command()
def social_eng():
    """🎭 Social Engineering Toolkit - FERRAMENTA OFENSIVA"""
    console.print(Panel.fit(
        "[bold red]⚠️ FERRAMENTA OFENSIVA ⚠️[/bold red]\n"
        "[yellow]Uso autorizado apenas para treinamentos e testes internos[/yellow]",
        style="red"
    ))

    confirm = questionary.confirm("Confirma que tem autorização para usar esta ferramenta?").ask()
    if not confirm:
        print_warning("Operação cancelada pelo usuário")
        return

    # TODO: Implementar social engineering toolkit
    print_info("Social Engineering Toolkit - Em implementação")

# Funções de Help Detalhadas

def show_ip_help():
    """Mostra help detalhado para IP Intelligence"""
    help_content = Panel.fit(
        "[bold green]🌐 IP INTELLIGENCE & GEOLOCATION[/bold green]\n\n"
        "[cyan]O que faz:[/cyan]\n"
        "Analisa endereços IP fornecendo geolocalização, informações do ISP,\n"
        "reputação de segurança, DNS reverso e detecção de ameaças.\n\n"
        "[cyan]Exemplos práticos:[/cyan]\n"
        "[dim]cyber ip-intel --target 8.8.8.8[/dim]          # Analisa DNS público do Google\n"
        "[dim]cyber ip-intel --target 1.1.1.1[/dim]          # Analisa DNS da Cloudflare\n"
        "[dim]cyber ip-intel --target 192.168.1.1[/dim]      # IP local (sem dados externos)\n\n"
        "[cyan]Informações retornadas:[/cyan]\n"
        "• Localização geográfica (país, região, cidade, coordenadas)\n"
        "• Provedor de internet (ISP) e organização\n"
        "• Número e nome do ASN (Autonomous System)\n"
        "• Registro PTR (DNS reverso)\n"
        "• Score de reputação e categorias de ameaça\n"
        "• Portas abertas e serviços detectados\n\n"
        "[yellow]Dica:[/yellow] Use 'cyber my-ip' para analisar seu próprio IP público",
        style="green"
    )
    console.print(help_content)

def show_domain_help():
    """Mostra help detalhado para Domain Analysis"""
    help_content = Panel.fit(
        "[bold blue]🔍 DOMAIN ANALYSIS[/bold blue]\n\n"
        "[cyan]O que faz:[/cyan]\n"
        "Análise completa de domínios incluindo WHOIS, registros DNS,\n"
        "certificados SSL, subdomínios e análise de reputação.\n\n"
        "[cyan]Exemplos práticos:[/cyan]\n"
        "[dim]cyber domain --domain google.com[/dim]          # Análise do Google\n"
        "[dim]cyber domain --domain github.com[/dim]          # Análise do GitHub\n"
        "[dim]cyber domain --domain suspicious-site.com[/dim] # Site suspeito\n\n"
        "[cyan]Informações retornadas:[/cyan]\n"
        "• Dados WHOIS (registrante, datas de criação/expiração)\n"
        "• Registros DNS (A, AAAA, MX, NS, TXT)\n"
        "• Certificado SSL/TLS (emissor, validade, SAN)\n"
        "• Subdomínios descobertos\n"
        "• Análise de reputação e classificação de segurança\n"
        "• Tecnologias web detectadas",
        style="blue"
    )
    console.print(help_content)

def show_vuln_help():
    """Mostra help detalhado para Vulnerability Scanner"""
    help_content = Panel.fit(
        "[bold red]🎯 VULNERABILITY SCANNER [FERRAMENTA OFENSIVA][/bold red]\n\n"
        "[yellow]⚠️ AVISO IMPORTANTE:[/yellow]\n"
        "Esta ferramenta deve ser usada APENAS em sistemas próprios ou com\n"
        "autorização explícita por escrito. Uso não autorizado é CRIME.\n\n"
        "[cyan]O que faz:[/cyan]\n"
        "Executa scans de portas, detecta serviços e identifica\n"
        "vulnerabilidades conhecidas em sistemas remotos.\n\n"
        "[cyan]Tipos de scan disponíveis:[/cyan]\n"
        "[dim]--type quick[/dim]       # Scan rápido (portas comuns)\n"
        "[dim]--type full[/dim]        # Scan completo (todas as portas)\n"
        "[dim]--type stealth[/dim]     # Scan silencioso (evita detecção)\n"
        "[dim]--type aggressive[/dim]  # Scan agressivo (máxima informação)\n\n"
        "[cyan]Exemplos práticos:[/cyan]\n"
        "[dim]cyber vuln-scan --target 192.168.1.100 --type quick[/dim]\n"
        "[dim]cyber vuln-scan --target testphp.vulnweb.com --type full[/dim]\n\n"
        "[red]Uso responsável:[/red] Sempre teste em ambientes controlados",
        style="red"
    )
    console.print(help_content)

def show_social_help():
    """Mostra help detalhado para Social Engineering Toolkit"""
    help_content = Panel.fit(
        "[bold magenta]🎭 SOCIAL ENGINEERING TOOLKIT [FERRAMENTA OFENSIVA][/bold magenta]\n\n"
        "[yellow]⚠️ AVISO IMPORTANTE:[/yellow]\n"
        "Esta ferramenta deve ser usada APENAS para treinamentos\n"
        "internos de conscientização em segurança.\n\n"
        "[cyan]O que faz:[/cyan]\n"
        "Cria campanhas de phishing simuladas para treinar funcionários\n"
        "e testa a resistência organizacional a ataques sociais.\n\n"
        "[cyan]Funcionalidades:[/cyan]\n"
        "• Templates de email de phishing personalizáveis\n"
        "• Landing pages falsas para coleta de credenciais\n"
        "• Campanhas de conscientização em segurança\n"
        "• Analytics detalhados de campanhas\n"
        "• Treinamento interativo pós-teste\n\n"
        "[cyan]Exemplos de uso ético:[/cyan]\n"
        "[dim]• Testes de conscientização em TI corporativo[/dim]\n"
        "[dim]• Treinamento de equipes de segurança[/dim]\n"
        "[dim]• Simulações de Red Team autorizadas[/dim]\n\n"
        "[red]Uso responsável:[/red] Sempre com consentimento e documentação",
        style="magenta"
    )
    console.print(help_content)

def show_examples():
    """Mostra exemplos práticos completos"""
    examples_content = Panel.fit(
        "[bold yellow]📚 EXEMPLOS PRÁTICOS DO MÓDULO CYBER[/bold yellow]\n\n"
        "[green]1. Investigação de IP Suspeito:[/green]\n"
        "[dim]cyber ip-intel --target 185.220.101.1[/dim]\n"
        "[dim]# Analisa IP conhecido por atividade suspeita[/dim]\n\n"
        "[green]2. Auditoria de Domínio Corporativo:[/green]\n"
        "[dim]cyber domain --domain minha-empresa.com[/dim]\n"
        "[dim]# Verifica configurações DNS e certificados[/dim]\n\n"
        "[green]3. Pentest Autorizado:[/green]\n"
        "[dim]cyber vuln-scan --target 10.0.0.0/24 --type stealth[/dim]\n"
        "[dim]# Scan de rede interna (com autorização)[/dim]\n\n"
        "[green]4. Treinamento de Phishing:[/green]\n"
        "[dim]cyber social-eng --template it-support --targets equipe-ti.txt[/dim]\n"
        "[dim]# Campanha educativa para equipe de TI[/dim]\n\n"
        "[green]5. Análise do Próprio IP:[/green]\n"
        "[dim]cyber my-ip[/dim]\n"
        "[dim]# Detecta e analisa seu IP público atual[/dim]\n\n"
        "[yellow]Dica Pro:[/yellow] Use '--help' em qualquer comando para opções avançadas",
        style="yellow"
    )
    console.print(examples_content)

if __name__ == "__main__":
    app()