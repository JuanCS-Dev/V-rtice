"""
Report Generator - Geração de relatórios OSINT
Projeto Vértice - SSP-GO
"""

import json
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Gera relatórios formatados de investigação OSINT"""
    
    @staticmethod
    def generate_html_report(data: Dict[str, Any]) -> str:
        """Gera relatório em HTML"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório OSINT - Projeto Vértice</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
                h1 {{ color: #9333ea; border-bottom: 2px solid #9333ea; padding-bottom: 10px; }}
                h2 {{ color: #a855f7; margin-top: 30px; }}
                .section {{ background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 8px; }}
                .info {{ background: #3a3a3a; padding: 10px; margin: 5px 0; border-left: 3px solid #9333ea; }}
                .warning {{ background: #4a2020; border-left: 3px solid #f00; }}
                .success {{ background: #204a20; border-left: 3px solid #0f0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th {{ background: #9333ea; padding: 10px; text-align: left; }}
                td {{ padding: 8px; border-bottom: 1px solid #444; }}
                .timestamp {{ color: #888; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <h1>🔍 Relatório de Inteligência OSINT</h1>
            <div class="timestamp">Gerado em: {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC</div>
            
            <div class="section">
                <h2>📊 Resumo Executivo</h2>
                <div class="info">
                    <strong>Query:</strong> {data.get('query', 'N/A')}<br>
                    <strong>Tipo:</strong> {data.get('search_type', 'N/A')}<br>
                    <strong>Status:</strong> {data.get('status', 'Completo')}
                </div>
            </div>
        """
        
        # Adicionar seções baseadas nos dados disponíveis
        if 'username_search' in data:
            html += ReportGenerator._generate_username_section(data['username_search'])
            
        if 'email_analysis' in data:
            html += ReportGenerator._generate_email_section(data['email_analysis'])
            
        if 'phone_analysis' in data:
            html += ReportGenerator._generate_phone_section(data['phone_analysis'])
            
        if 'social_profiles' in data:
            html += ReportGenerator._generate_social_section(data['social_profiles'])
            
        html += """
        </body>
        </html>
        """
        
        return html
        
    @staticmethod
    def _generate_username_section(data: Dict) -> str:
        """Gera seção de username"""
        profiles = data.get('profiles_found', [])
        
        html = f"""
        <div class="section">
            <h2>👤 Análise de Username</h2>
            <div class="info">
                <strong>Username:</strong> {data.get('username', 'N/A')}<br>
                <strong>Perfis Encontrados:</strong> {len(profiles)}<br>
            </div>
            
            <table>
                <tr>
                    <th>Plataforma</th>
                    <th>URL</th>
                    <th>Categoria</th>
                    <th>Status</th>
                </tr>
        """
        
        for profile in profiles:
            html += f"""
                <tr>
                    <td>{profile.get('platform', 'N/A')}</td>
                    <td><a href="{profile.get('url', '#')}" target="_blank">{profile.get('url', 'N/A')}</a></td>
                    <td>{profile.get('category', 'N/A')}</td>
                    <td>{'✅ Ativo' if profile.get('exists') else '❌ Inativo'}</td>
                </tr>
            """
            
        html += """
            </table>
        </div>
        """
        
        return html
        
    @staticmethod
    def _generate_email_section(data: Dict) -> str:
        """Gera seção de email"""
        return f"""
        <div class="section">
            <h2>📧 Análise de Email</h2>
            <div class="info {'warning' if data.get('breaches') else 'success'}">
                <strong>Email:</strong> {data.get('email', 'N/A')}<br>
                <strong>Domínio:</strong> {data.get('domain', 'N/A')}<br>
                <strong>MX Válido:</strong> {'✅ Sim' if data.get('mx_records', {}).get('valid') else '❌ Não'}<br>
                <strong>Vazamentos:</strong> {len(data.get('breaches', []))} encontrados<br>
                <strong>Score de Risco:</strong> {data.get('risk_score', {}).get('score', 0)}/100
            </div>
        </div>
        """
        
    @staticmethod
    def _generate_phone_section(data: Dict) -> str:
        """Gera seção de telefone"""
        return f"""
        <div class="section">
            <h2>📱 Análise de Telefone</h2>
            <div class="info">
                <strong>Número:</strong> {data.get('normalized', 'N/A')}<br>
                <strong>País:</strong> {data.get('location', {}).get('country', 'N/A')}<br>
                <strong>Região:</strong> {data.get('location', {}).get('region', 'N/A')}<br>
                <strong>Operadora:</strong> {data.get('carrier', {}).get('name', 'N/A')}<br>
                <strong>Tipo:</strong> {data.get('carrier', {}).get('type', 'N/A')}
            </div>
        </div>
        """
        
    @staticmethod
    def _generate_social_section(data: List[Dict]) -> str:
        """Gera seção de redes sociais"""
        html = """
        <div class="section">
            <h2>🌐 Perfis em Redes Sociais</h2>
        """
        
        for profile in data:
            html += f"""
            <div class="info">
                <strong>{profile.get('platform', 'N/A')}:</strong><br>
                Username: {profile.get('username', 'N/A')}<br>
                Seguidores: {profile.get('followers', 'N/A')}<br>
                Posts: {profile.get('posts', 'N/A')}<br>
            </div>
            """
            
        html += "</div>"
        return html
        
    @staticmethod
    def generate_json_report(data: Dict[str, Any]) -> str:
        """Gera relatório em JSON"""
        report = {
            "report_type": "OSINT_INVESTIGATION",
            "generated_at": datetime.utcnow().isoformat(),
            "project": "Vértice SSP-GO",
            "version": "1.0.0",
            "data": data
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
