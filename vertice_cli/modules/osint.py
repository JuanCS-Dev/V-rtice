# vertice_cli/modules/osint.py

import typer
import questionary
from rich.table import Table
from rich.panel import Panel
from ..utils.api_client import VerticeAPI
from ..utils import console, print_success, print_error, print_info

app = typer.Typer(help="🔍 OSINT Module - Open Source Intelligence Gathering")

@app.command()
def menu():
    """🔍 Menu interativo do módulo OSINT"""
    console.print(Panel.fit(
        "[bold purple]🔍 VÉRTICE OSINT MODULE[/bold purple]\n"
        "[dim]Open Source Intelligence - Coleta de inteligência em fontes abertas[/dim]\n"
        "\n"
        "[yellow]Exemplos de uso:[/yellow]\n"
        "[dim]• osint email --email target@company.com[/dim]\n"
        "[dim]• osint phone --phone +5511987654321[/dim]\n"
        "[dim]• osint username --username john_doe[/dim]\n"
        "[dim]• osint social --platform instagram --id @targetuser[/dim]",
        style="purple"
    ))

    choices = [
        "📧 Email Analysis - Vazamentos, reputação, MX records",
        "📱 Phone Investigation - Operadora, localização, tipo de linha",
        "👤 Username Investigation - Busca em múltiplas plataformas",
        "🌐 Social Media Analysis - Perfis, posts, análise comportamental",
        "🌍 Geospatial Intelligence - Análise de coordenadas e locais",
        "📚 Ver exemplos e documentação",
        "🔙 Voltar ao menu principal"
    ]

    choice = questionary.select(
        "Selecione uma ferramenta:",
        choices=choices
    ).ask()

    if "Email Analysis" in choice:
        show_email_help()
        email_analysis()
    elif "Phone Investigation" in choice:
        show_phone_help()
        phone_investigation()
    elif "Username Investigation" in choice:
        show_username_help()
        username_investigation()
    elif "Social Media" in choice:
        show_social_media_help()
        social_media_analysis()
    elif "Geospatial" in choice:
        show_geospatial_help()
        geospatial_analysis()
    elif "exemplos" in choice:
        show_osint_examples()
    else:
        return

@app.command()
def email_analysis(email: str = typer.Option(None, "--email", "-e", help="Email para análise")):
    """📧 Análise completa de email"""
    if not email:
        email = questionary.text("Digite o email para análise:").ask()

    print_info(f"Analisando email: {email}")

    # TODO: Implementar chamada para API
    api = VerticeAPI()
    result = api.analyze_email(email)

    if result:
        print_success("Análise de email concluída!")
        # TODO: Exibir resultados formatados
    else:
        print_error("Falha na análise do email")

@app.command()
def phone_investigation(phone: str = typer.Option(None, "--phone", "-p", help="Telefone para investigação")):
    """📱 Investigação de número de telefone"""
    if not phone:
        phone = questionary.text("Digite o número de telefone:").ask()

    print_info(f"Investigando telefone: {phone}")

    # TODO: Implementar
    api = VerticeAPI()
    result = api.analyze_phone(phone)

@app.command()
def username_investigation(username: str = typer.Option(None, "--username", "-u", help="Username para investigação")):
    """👤 Investigação de username em múltiplas plataformas"""
    if not username:
        username = questionary.text("Digite o username:").ask()

    print_info(f"Investigando username: {username}")

    # TODO: Implementar
    api = VerticeAPI()
    result = api.investigate_username(username)

@app.command()
def social_media_analysis():
    """🌐 Análise de perfis em redes sociais"""
    platform = questionary.select(
        "Selecione a plataforma:",
        choices=["Instagram", "Twitter/X", "LinkedIn", "Facebook", "Discord", "Telegram"]
    ).ask()

    identifier = questionary.text(f"Digite o username/ID do perfil no {platform}:").ask()

    print_info(f"Analisando perfil {identifier} no {platform}")

    # TODO: Implementar
    api = VerticeAPI()
    result = api.analyze_social_profile(platform.lower(), identifier)

@app.command()
def geospatial_analysis():
    """🌍 Análise de inteligência geoespacial"""
    print_info("Geospatial Intelligence - Em implementação")
    # TODO: Implementar análise geoespacial

# Funções de Help Detalhadas

def show_email_help():
    """Help detalhado para Email Analysis"""
    help_content = Panel.fit(
        "[bold cyan]📧 EMAIL ANALYSIS[/bold cyan]\n\n"
        "[cyan]O que faz:[/cyan]\n"
        "Analisa endereços de email buscando vazamentos de dados, reputação,\n"
        "configurações DNS e presença em redes sociais.\n\n"
        "[cyan]Exemplos práticos:[/cyan]\n"
        "[dim]osint email --email john.doe@company.com[/dim]    # Email corporativo\n"
        "[dim]osint email --email user123@gmail.com[/dim]       # Email pessoal\n"
        "[dim]osint email --email admin@target-site.com[/dim]   # Email de admin\n\n"
        "[cyan]Informações coletadas:[/cyan]\n"
        "• Vazamentos de dados (breaches conhecidos)\n"
        "• Score de reputação e classificação de spam\n"
        "• Registros MX e configuração de email\n"
        "• Contas em redes sociais associadas\n"
        "• Domínios e organizações relacionadas\n"
        "• Atividade em fóruns e comunidades online\n\n"
        "[cyan]Fontes consultadas:[/cyan]\n"
        "HaveIBeenPwned, DeHashed, Holehe, EmailRep, DNS records",
        style="cyan"
    )
    console.print(help_content)

def show_phone_help():
    """Help detalhado para Phone Investigation"""
    help_content = Panel.fit(
        "[bold green]📱 PHONE INVESTIGATION[/bold green]\n\n"
        "[cyan]O que faz:[/cyan]\n"
        "Investiga números de telefone fornecendo informações sobre\n"
        "operadora, localização, tipo de linha e possíveis associações.\n\n"
        "[cyan]Exemplos práticos:[/cyan]\n"
        "[dim]osint phone --phone +5511987654321[/dim]          # Celular brasileiro\n"
        "[dim]osint phone --phone +1234567890[/dim]             # Número internacional\n"
        "[dim]osint phone --phone 011987654321[/dim]            # Formato nacional\n\n"
        "[cyan]Informações coletadas:[/cyan]\n"
        "• País e região de origem\n"
        "• Operadora e tipo de linha (móvel/fixo)\n"
        "• Código de área e localização aproximada\n"
        "• Formato válido e variações\n"
        "• Possíveis contas em redes sociais\n"
        "• Histórico de vazamentos (se disponível)\n\n"
        "[yellow]Dica:[/yellow] Use formato internacional (+55...) para melhor precisão\n"
        "[yellow]Limitações:[/yellow] Dados variam conforme país e operadora",
        style="green"
    )
    console.print(help_content)

def show_username_help():
    """Help detalhado para Username Investigation"""
    help_content = Panel.fit(
        "[bold blue]👤 USERNAME INVESTIGATION[/bold blue]\n\n"
        "[cyan]O que faz:[/cyan]\n"
        "Busca um username específico em centenas de plataformas\n"
        "e redes sociais, mapeando a presença digital do alvo.\n\n"
        "[cyan]Exemplos práticos:[/cyan]\n"
        "[dim]osint username --username john_doe[/dim]           # Username comum\n"
        "[dim]osint username --username cybersec_expert[/dim]    # Username especializado\n"
        "[dim]osint username --username target123[/dim]         # Username alfanumérico\n\n"
        "[cyan]Plataformas verificadas:[/cyan]\n"
        "• Redes sociais: Instagram, Twitter, Facebook, LinkedIn\n"
        "• Plataformas dev: GitHub, GitLab, Stack Overflow\n"
        "• Fóruns: Reddit, Discord, Telegram\n"
        "• Outros: YouTube, TikTok, Twitch, Steam, Xbox\n"
        "• Sites adultos, dating e marketplace\n\n"
        "[cyan]Informações retornadas:[/cyan]\n"
        "• Lista de contas encontradas com URLs\n"
        "• Probabilidade de ser a mesma pessoa\n"
        "• Dados públicos dos perfis (quando disponível)\n"
        "• Cross-reference entre plataformas",
        style="blue"
    )
    console.print(help_content)

def show_social_media_help():
    """Help detalhado para Social Media Analysis"""
    help_content = Panel.fit(
        "[bold magenta]🌐 SOCIAL MEDIA ANALYSIS[/bold magenta]\n\n"
        "[cyan]O que faz:[/cyan]\n"
        "Análise profunda de perfis em redes sociais incluindo posts,\n"
        "conexões, padrões comportamentais e metadados.\n\n"
        "[cyan]Plataformas suportadas:[/cyan]\n"
        "[dim]--platform instagram[/dim]  # Análise de perfil do Instagram\n"
        "[dim]--platform twitter[/dim]    # Posts e interações do Twitter\n"
        "[dim]--platform linkedin[/dim]   # Perfil profissional\n"
        "[dim]--platform facebook[/dim]   # Dados públicos do Facebook\n"
        "[dim]--platform telegram[/dim]   # Canais e grupos públicos\n\n"
        "[cyan]Exemplos práticos:[/cyan]\n"
        "[dim]osint social --platform instagram --id @john_doe[/dim]\n"
        "[dim]osint social --platform twitter --id johndoe123[/dim]\n"
        "[dim]osint social --platform linkedin --id john-doe-analyst[/dim]\n\n"
        "[cyan]Dados extraídos:[/cyan]\n"
        "• Informações do perfil (bio, foto, seguidores)\n"
        "• Posts recentes e análise de conteúdo\n"
        "• Padrões de atividade (horários, frequência)\n"
        "• Análise de sentimento e temas\n"
        "• Geolocalização (quando disponível)\n"
        "• Conexões e interações relevantes",
        style="magenta"
    )
    console.print(help_content)

def show_geospatial_help():
    """Help detalhado para Geospatial Intelligence"""
    help_content = Panel.fit(
        "[bold yellow]🌍 GEOSPATIAL INTELLIGENCE[/bold yellow]\n\n"
        "[cyan]O que faz:[/cyan]\n"
        "Análise de coordenadas, endereços e locais usando imagens de\n"
        "satélite, Street View e bases de dados geográficas.\n\n"
        "[cyan]Funcionalidades:[/cyan]\n"
        "• Análise de coordenadas GPS\n"
        "• Reverse geocoding (coordenadas → endereço)\n"
        "• Análise de metadados EXIF em imagens\n"
        "• Busca por landmarks e pontos de interesse\n"
        "• Correlação com dados de transporte público\n\n"
        "[cyan]Exemplos de uso:[/cyan]\n"
        "[dim]osint geospatial --coords \"-23.5505,-46.6333\"[/dim]  # São Paulo\n"
        "[dim]osint geospatial --address \"Times Square, NYC\"[/dim]\n"
        "[dim]osint geospatial --image /path/to/photo.jpg[/dim]     # Extrair EXIF\n\n"
        "[yellow]Aplicações:[/yellow]\n"
        "• Verificação de localização em posts\n"
        "• Análise forense de imagens\n"
        "• Investigação de check-ins\n"
        "• Correlação geográfica de dados",
        style="yellow"
    )
    console.print(help_content)

def show_osint_examples():
    """Exemplos práticos completos do módulo OSINT"""
    examples_content = Panel.fit(
        "[bold purple]📚 EXEMPLOS PRÁTICOS DO MÓDULO OSINT[/bold purple]\n\n"
        "[green]1. Investigação Completa de Pessoa:[/green]\n"
        "[dim]# Busca inicial por email[/dim]\n"
        "[dim]osint email --email target@company.com[/dim]\n"
        "[dim]# Investigar username encontrado[/dim]\n"
        "[dim]osint username --username target_user[/dim]\n"
        "[dim]# Analisar perfis sociais descobertos[/dim]\n"
        "[dim]osint social --platform linkedin --id target-user-analyst[/dim]\n\n"
        "[green]2. Due Diligence Empresarial:[/green]\n"
        "[dim]# Analisar domínio corporativo[/dim]\n"
        "[dim]cyber domain --domain target-company.com[/dim]\n"
        "[dim]# Investigar emails de executivos[/dim]\n"
        "[dim]osint email --email ceo@target-company.com[/dim]\n"
        "[dim]# Mapear presença digital da empresa[/dim]\n"
        "[dim]osint username --username target_company[/dim]\n\n"
        "[green]3. Investigação de Fraude Online:[/green]\n"
        "[dim]# Verificar telefone suspeito[/dim]\n"
        "[dim]osint phone --phone +5511999887766[/dim]\n"
        "[dim]# Analisar perfil social falso[/dim]\n"
        "[dim]osint social --platform instagram --id @fake_profile[/dim]\n\n"
        "[green]4. Background Check Completo:[/green]\n"
        "[dim]# Pipeline automatizado (exemplo)[/dim]\n"
        "[dim]osint email --email john@company.com | osint cross-reference[/dim]\n\n"
        "[yellow]Dica Ética:[/yellow] Sempre respeite privacidade e termos de uso das plataformas",
        style="purple"
    )
    console.print(examples_content)

if __name__ == "__main__":
    app()