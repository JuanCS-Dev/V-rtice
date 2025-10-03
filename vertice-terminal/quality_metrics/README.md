
# 📊 Métricas de Qualidade de Código

Este diretório é destinado a armazenar os relatórios gerados pelas ferramentas de análise de qualidade de código.

## Relatórios

- **Relatório de Cobertura de Testes (`coverage.xml` / `htmlcov/`):**
  - Gerado pelo `pytest-cov`.
  - Mostra a porcentagem de código que é coberta pelos testes automatizados.
  - Para gerar: `pytest --cov=vertice --cov-report=xml --cov-report=html`

- **Relatório de Complexidade (`complexity.txt`):**
  - Gerado pelo `radon`.
  - Analisa a complexidade ciclomática do código. Funções com alta complexidade são difíceis de testar e manter.
  - Para gerar: `radon cc vertice -a -s > quality_metrics/complexity.txt`

- **Relatório de Manutenibilidade (`maintainability.txt`):**
  - Gerado pelo `radon`.
  - Calcula o Índice de Manutenibilidade, que é uma métrica que combina complexidade, linhas de código e outras heurísticas.
  - Para gerar: `radon mi vertice -s > quality_metrics/maintainability.txt`

Estes relatórios são gerados automaticamente pelo pipeline de CI/CD e podem ser usados para rastrear a evolução da qualidade do código ao longo do tempo.
