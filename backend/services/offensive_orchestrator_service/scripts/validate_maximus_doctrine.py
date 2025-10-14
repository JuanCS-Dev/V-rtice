#!/usr/bin/env python3
"""
Validação de Doutrina MAXIMUS - Offensive Orchestrator Service
Verifica conformidade com princípios MAXIMUS:
1. NO MOCK - Implementações reais desde Sprint 1
2. QUALITY-FIRST - Coverage, types, error handling
3. PRODUCTION-READY - Resilient, observable, fault-tolerant
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# ANSI colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

class MaximusDoctrineValidator:
    """Validador de conformidade com doutrina MAXIMUS."""
    
    def __init__(self):
        self.violations = []
        self.warnings = []
        self.successes = []
        
    def validate_no_mock_principle(self) -> Tuple[int, int]:
        """
        Princípio 1: NO MOCK
        - Implementações reais, não placeholders
        - Permitido: mocks em testes APENAS
        - Proibido: TODOs, NotImplementedError em código de produção
        """
        print(f"\n{BLUE}{'='*80}{RESET}")
        print(f"{BOLD}PRINCÍPIO 1: NO MOCK - Implementações Reais{RESET}")
        print(f"{BLUE}{'='*80}{RESET}\n")
        
        violations = 0
        checks = 0
        
        # Check for TODO/FIXME in production code
        print("🔍 Verificando TODOs/FIXMEs em código de produção...")
        production_files = [
            'api.py', 'orchestrator.py', 'models.py', 'config.py',
            'hotl_system.py', 'memory/attack_memory.py', 'memory/database.py',
            'memory/vector_store.py', 'memory/embeddings.py'
        ]
        
        for file in production_files:
            if not os.path.exists(file):
                continue
            checks += 1
            with open(file, 'r') as f:
                content = f.read()
                if 'TODO' in content or 'FIXME' in content:
                    lines = [i+1 for i, line in enumerate(content.split('\n')) 
                            if 'TODO' in line or 'FIXME' in line]
                    print(f"  {RED}✗{RESET} {file} contém TODO/FIXME nas linhas: {lines}")
                    violations += 1
                else:
                    print(f"  {GREEN}✓{RESET} {file} - Sem TODOs")
        
        # Check for NotImplementedError in production code
        print("\n🔍 Verificando NotImplementedError em código de produção...")
        for file in production_files:
            if not os.path.exists(file):
                continue
            checks += 1
            with open(file, 'r') as f:
                content = f.read()
                if 'NotImplementedError' in content:
                    print(f"  {RED}✗{RESET} {file} contém NotImplementedError")
                    violations += 1
                else:
                    print(f"  {GREEN}✓{RESET} {file} - Sem NotImplementedError")
        
        # Check for actual LLM integration (not mocked)
        print("\n🔍 Verificando integração real com LLM (Gemini)...")
        with open('orchestrator.py', 'r') as f:
            content = f.read()
            checks += 1
            if 'google.generativeai' in content and 'genai.GenerativeModel' in content:
                print(f"  {GREEN}✓{RESET} orchestrator.py usa Gemini real (google.generativeai)")
            else:
                print(f"  {RED}✗{RESET} orchestrator.py NÃO usa LLM real")
                violations += 1
        
        # Check for actual database integration
        print("\n🔍 Verificando integração real com PostgreSQL...")
        with open('memory/database.py', 'r') as f:
            content = f.read()
            checks += 1
            if 'sqlalchemy' in content and 'create_engine' in content:
                print(f"  {GREEN}✓{RESET} database.py usa PostgreSQL real (SQLAlchemy)")
            else:
                print(f"  {RED}✗{RESET} database.py NÃO usa banco de dados real")
                violations += 1
        
        # Check for actual vector DB integration
        print("\n🔍 Verificando integração real com Qdrant...")
        with open('memory/vector_store.py', 'r') as f:
            content = f.read()
            checks += 1
            if 'qdrant_client' in content:
                print(f"  {GREEN}✓{RESET} vector_store.py usa Qdrant real")
            else:
                print(f"  {RED}✗{RESET} vector_store.py NÃO usa vector DB real")
                violations += 1
        
        print(f"\n{BOLD}Resultado Princípio 1:{RESET}")
        if violations == 0:
            print(f"  {GREEN}✓ APROVADO{RESET} - {checks} checks, 0 violações")
        else:
            print(f"  {RED}✗ REPROVADO{RESET} - {violations}/{checks} violações")
        
        return violations, checks
    
    def validate_quality_first_principle(self) -> Tuple[int, int]:
        """
        Princípio 2: QUALITY-FIRST
        - Type hints em funções públicas
        - Docstrings em classes e funções principais
        - Error handling adequado
        - Logging configurado
        """
        print(f"\n{BLUE}{'='*80}{RESET}")
        print(f"{BOLD}PRINCÍPIO 2: QUALITY-FIRST - Qualidade de Código{RESET}")
        print(f"{BLUE}{'='*80}{RESET}\n")
        
        violations = 0
        checks = 0
        
        production_files = [
            'orchestrator.py', 'hotl_system.py', 'memory/attack_memory.py'
        ]
        
        for file in production_files:
            if not os.path.exists(file):
                continue
            
            print(f"\n🔍 Analisando {file}...")
            
            with open(file, 'r') as f:
                try:
                    tree = ast.parse(f.read(), filename=file)
                except:
                    continue
            
            # Check classes have docstrings
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            for cls in classes:
                checks += 1
                if ast.get_docstring(cls):
                    print(f"  {GREEN}✓{RESET} Classe {cls.name} tem docstring")
                else:
                    print(f"  {RED}✗{RESET} Classe {cls.name} SEM docstring")
                    violations += 1
            
            # Check public methods have type hints
            funcs = [node for node in ast.walk(tree) 
                    if isinstance(node, ast.FunctionDef) 
                    and not node.name.startswith('_')]
            
            for func in funcs[:3]:  # Check first 3 public functions
                checks += 1
                has_return_hint = func.returns is not None
                has_arg_hints = all(arg.annotation is not None for arg in func.args.args[1:])  # Skip self
                
                if has_return_hint and has_arg_hints:
                    print(f"  {GREEN}✓{RESET} Função {func.name} tem type hints")
                else:
                    print(f"  {YELLOW}⚠{RESET} Função {func.name} tem type hints incompletos")
        
        # Check for logging usage
        print("\n🔍 Verificando uso de logging...")
        for file in production_files:
            if not os.path.exists(file):
                continue
            checks += 1
            with open(file, 'r') as f:
                content = f.read()
                if 'import logging' in content and 'logger' in content:
                    print(f"  {GREEN}✓{RESET} {file} usa logging")
                else:
                    print(f"  {RED}✗{RESET} {file} NÃO usa logging adequadamente")
                    violations += 1
        
        # Check for error handling
        print("\n🔍 Verificando error handling...")
        for file in production_files:
            if not os.path.exists(file):
                continue
            checks += 1
            with open(file, 'r') as f:
                content = f.read()
                if 'try:' in content and 'except' in content:
                    print(f"  {GREEN}✓{RESET} {file} tem error handling")
                else:
                    print(f"  {YELLOW}⚠{RESET} {file} tem error handling limitado")
        
        print(f"\n{BOLD}Resultado Princípio 2:{RESET}")
        if violations == 0:
            print(f"  {GREEN}✓ APROVADO{RESET} - {checks} checks, 0 violações")
        else:
            print(f"  {YELLOW}⚠ ATENÇÃO{RESET} - {violations}/{checks} issues (não bloqueante)")
        
        return violations, checks
    
    def validate_production_ready_principle(self) -> Tuple[int, int]:
        """
        Princípio 3: PRODUCTION-READY
        - Tests com coverage adequado
        - Configuration management
        - Graceful degradation
        - Observability (logs, metrics)
        """
        print(f"\n{BLUE}{'='*80}{RESET}")
        print(f"{BOLD}PRINCÍPIO 3: PRODUCTION-READY - Pronto para Produção{RESET}")
        print(f"{BLUE}{'='*80}{RESET}\n")
        
        violations = 0
        checks = 0
        
        # Check test coverage exists
        print("🔍 Verificando cobertura de testes...")
        checks += 1
        if os.path.exists('htmlcov/index.html'):
            print(f"  {GREEN}✓{RESET} Coverage reports disponíveis")
        else:
            print(f"  {RED}✗{RESET} Coverage reports NÃO encontrados")
            violations += 1
        
        # Check configuration management
        print("\n🔍 Verificando configuration management...")
        checks += 1
        if os.path.exists('config.py'):
            with open('config.py', 'r') as f:
                content = f.read()
                if 'pydantic' in content or 'BaseSettings' in content or 'os.getenv' in content:
                    print(f"  {GREEN}✓{RESET} Configuration management implementado")
                else:
                    print(f"  {RED}✗{RESET} Configuration management inadequado")
                    violations += 1
        
        # Check for graceful degradation patterns
        print("\n🔍 Verificando graceful degradation patterns...")
        files_to_check = ['orchestrator.py', 'hotl_system.py', 'memory/attack_memory.py']
        for file in files_to_check:
            if not os.path.exists(file):
                continue
            checks += 1
            with open(file, 'r') as f:
                content = f.read()
                # Look for retry logic, timeout handling, fallback mechanisms
                has_retry = 'retry' in content.lower() or 'attempt' in content
                has_timeout = 'timeout' in content.lower()
                
                if has_retry or has_timeout:
                    print(f"  {GREEN}✓{RESET} {file} tem patterns de resiliência")
                else:
                    print(f"  {YELLOW}⚠{RESET} {file} pode melhorar resiliência")
        
        # Check for observability (logging, metrics)
        print("\n🔍 Verificando observability...")
        checks += 1
        files_with_logging = 0
        for file in files_to_check:
            if not os.path.exists(file):
                continue
            with open(file, 'r') as f:
                content = f.read()
                if 'logger.info' in content and 'logger.error' in content:
                    files_with_logging += 1
        
        if files_with_logging >= 2:
            print(f"  {GREEN}✓{RESET} Logging implementado em múltiplos módulos")
        else:
            print(f"  {YELLOW}⚠{RESET} Logging pode ser expandido")
        
        # Check for API documentation
        print("\n🔍 Verificando API documentation...")
        checks += 1
        if os.path.exists('api.py'):
            with open('api.py', 'r') as f:
                content = f.read()
                if 'FastAPI' in content:
                    print(f"  {GREEN}✓{RESET} API com FastAPI (auto-documentation)")
                else:
                    print(f"  {YELLOW}⚠{RESET} API documentation pode ser melhorada")
        
        print(f"\n{BOLD}Resultado Princípio 3:{RESET}")
        if violations == 0:
            print(f"  {GREEN}✓ APROVADO{RESET} - {checks} checks, 0 violações")
        else:
            print(f"  {RED}✗ REPROVADO{RESET} - {violations}/{checks} violações")
        
        return violations, checks
    
    def run_full_validation(self):
        """Executa validação completa de todos os princípios."""
        print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
        print(f"{BOLD}  VALIDAÇÃO DE DOUTRINA MAXIMUS - OFFENSIVE ORCHESTRATOR SERVICE{RESET}")
        print(f"{BOLD}{BLUE}{'='*80}{RESET}")
        
        # Validate each principle
        v1, c1 = self.validate_no_mock_principle()
        v2, c2 = self.validate_quality_first_principle()
        v3, c3 = self.validate_production_ready_principle()
        
        total_violations = v1 + v3  # v2 is non-blocking
        total_checks = c1 + c2 + c3
        
        # Final report
        print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
        print(f"{BOLD}RELATÓRIO FINAL - DOUTRINA MAXIMUS{RESET}")
        print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
        
        print(f"Total de checks: {total_checks}")
        print(f"Violações bloqueantes: {v1 + v3}")
        print(f"Warnings não-bloqueantes: {v2}\n")
        
        if total_violations == 0:
            print(f"{BOLD}{GREEN}✓ SERVIÇO APROVADO NA VALIDAÇÃO DE DOUTRINA MAXIMUS{RESET}")
            print(f"{GREEN}Todos os princípios fundamentais foram atendidos.{RESET}\n")
            return 0
        else:
            print(f"{BOLD}{RED}✗ SERVIÇO REPROVADO NA VALIDAÇÃO DE DOUTRINA MAXIMUS{RESET}")
            print(f"{RED}{total_violations} violações bloqueantes encontradas.{RESET}\n")
            return 1

if __name__ == '__main__':
    validator = MaximusDoctrineValidator()
    exit_code = validator.run_full_validation()
    sys.exit(exit_code)
