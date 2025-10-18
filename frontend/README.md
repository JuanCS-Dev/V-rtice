# FRONTEND VÉRTICE

> Plataforma modular para inteligência cibernética, operações OSINT e analytics em tempo real.

[![React](https://img.shields.io/badge/React-18.2-61DAFB?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite)](https://vitejs.dev)
[![Zustand](https://img.shields.io/badge/Zustand-5.0-orange)](https://github.com/pmndrs/zustand)
[![TanStack Query](https://img.shields.io/badge/TanStack_Query-5.x-FF4154)](https://tanstack.com/query/latest)
[![Vitest](https://img.shields.io/badge/Vitest-3.x-6E9F18)](https://vitest.dev)
[![Node](https://img.shields.io/badge/Node.js-18%2B-339933?logo=node.js)](https://nodejs.org)

---

## Visão Geral

- Arquitetura React 18 + Vite com módulos dedicados a OSINT, Cyber Defense e Analytics.
- Estado global com Zustand 5 e cache assíncrono via TanStack Query 5.x.
- Design System proprietário documentado (`docs/design-system-reference.md`, `DESIGN_SYSTEM_v2.0.txt`).
- Internacionalização (pt-BR/en-US) e acessibilidade mapeadas em [I18N_IMPLEMENTATION.md](I18N_IMPLEMENTATION.md) e [ACCESSIBILITY_IMPLEMENTATION.md](ACCESSIBILITY_IMPLEMENTATION.md).

---

## Documentação Essencial

- **Fundamentos**
  - [FRONTEND_MANIFESTO.md](FRONTEND_MANIFESTO.md) — arquitetura, metas e padrões obrigatórios.
  - [REFACTORING_PLAN.md](REFACTORING_PLAN.md) & [REFACTORING_STATUS.md](REFACTORING_STATUS.md) — roadmap e progresso da refatoração.
  - [CONTRIBUTING.md](CONTRIBUTING.md) — fluxo de contribuição, checklist de PR e convenções de commits.
  - [CHANGELOG.md](CHANGELOG.md) — histórico de alterações.
- **Qualidade & Auditorias**
  - [FRONTEND_FINAL_REPORT.md](FRONTEND_FINAL_REPORT.md) — panorama geral da entrega.
  - [FRONTEND_SECURITY_REPORT.md](FRONTEND_SECURITY_REPORT.md) — hardening, controles e gaps.
  - [FRONTEND_TEST_COVERAGE_REPORT.md](FRONTEND_TEST_COVERAGE_REPORT.md) — inventário de suites e cobertura planejada.
  - [FRONTEND_VALIDATION_REPORT.md](FRONTEND_VALIDATION_REPORT.md) & [HITL_FRONTEND_VALIDATION_REPORT.md](HITL_FRONTEND_VALIDATION_REPORT.md) — validações automatizadas e HITL.
  - [TESTING_REPORT.md](TESTING_REPORT.md) & [TESTING_REPORT_FINAL.md](TESTING_REPORT_FINAL.md) — evolução das estratégias de teste.
  - [DOUBLE_CHECK_REPORT.md](DOUBLE_CHECK_REPORT.md) — revisão independente.
- **Guias de Implementação**
  - [COMPONENTS_API.md](COMPONENTS_API.md) & [WIDGET_LIBRARY_GUIDE.md](WIDGET_LIBRARY_GUIDE.md) — padrões de componentes e widgets.
  - [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) — troubleshooting avançado.
  - [TESTING_GUIDE.md](TESTING_GUIDE.md) — como estruturar e executar testes.
  - [docs/design-system-reference.md](docs/design-system-reference.md) & [docs/STYLE-GUIDE.md](docs/STYLE-GUIDE.md) — tokens, tipografia e linguagem visual.
  - [DESIGN_SYSTEM_v2.0.txt](DESIGN_SYSTEM_v2.0.txt) — referência rápida de cores e espaçamento.
  - [MAPA_DEBUG.md](MAPA_DEBUG.md) — mapa de debugging multi-equipe.
  - [LANDING_PAGE_REDESIGN.md](LANDING_PAGE_REDESIGN.md) & [MAXIMUS_VISUAL_IMPROVEMENTS.md](MAXIMUS_VISUAL_IMPROVEMENTS.md) — estudos visuais e experiências guiadas.
  - [DASHBOARD_ENTERPRISE_STANDARD.md](DASHBOARD_ENTERPRISE_STANDARD.md) — baseline para dashboards corporativos.

---

## Início Rápido

### Pré-requisitos

```bash
Node.js >= 18
npm >= 9
```

### Instalação

```bash
git clone <repo-url>
cd vertice-dev/frontend
npm install

# Opcional: copiar variáveis de ambiente base
cp .env.example .env

npm run dev
```

> Configure `API` e endpoints WebSocket no `.env` conforme a infraestrutura disponível.

---

## Scripts npm

```bash
npm run dev           # Servidor de desenvolvimento (Vite + HMR)
npm run build         # Build de produção
npm run preview       # Preview do build localmente
npm run lint          # ESLint com configurações do projeto
npm run test          # Vitest em modo interativo
npm run test:run      # Vitest em modo CI
npm run test:ui       # Interface web do Vitest
npm run test:coverage # Relatório de cobertura (v8)
```

---

## Estrutura do Projeto

```text
frontend/
├── docs/                   # Guias complementares e relatórios
├── public/                 # Assets estáticos servidos pelo Vite
├── scripts/                # Utilitários de automação
├── src/
│   ├── api/                # Clientes HTTP/WebSocket
│   ├── app/                # Layouts, rotas e wrappers
│   ├── components/         # Componentes compartilhados e módulos de domínio
│   ├── config/             # Configuração de serviços, query clients, etc.
│   ├── contexts/           # Providers globais
│   ├── hooks/              # Hooks customizados (state, a11y, segurança)
│   ├── i18n/               # Setup e traduções
│   ├── stores/             # Stores Zustand
│   ├── styles/             # Tokens, temas e utilitários de estilo
│   ├── utils/              # Funções auxiliares (segurança, formatação, etc.)
│   ├── __tests__/          # Suites focadas em regressão
│   └── tests/              # Fixtures e utilidades de teste
├── .env.example            # Template de variáveis de ambiente
├── vite.config.js          # Configuração Vite/Plugins
└── vitest.config.js        # Configuração de testes
```

---

## Pilares de Qualidade

- **Testes e Cobertura** — ver [FRONTEND_TEST_COVERAGE_REPORT.md](FRONTEND_TEST_COVERAGE_REPORT.md) e [TESTING_GUIDE.md](TESTING_GUIDE.md) para cenários e metas por módulo.
- **Segurança** — políticas e controles detalhados em [FRONTEND_SECURITY_REPORT.md](FRONTEND_SECURITY_REPORT.md) e utilities em `src/utils/security`.
- **Acessibilidade** — checklist WCAG 2.1 AA consolidado em [ACCESSIBILITY_IMPLEMENTATION.md](ACCESSIBILITY_IMPLEMENTATION.md) e componentes `shared/`.
- **Internacionalização** — fluxo completo de tradução em [I18N_IMPLEMENTATION.md](I18N_IMPLEMENTATION.md) e recursos em `src/i18n`.
- **Observabilidade & Debug** — práticas e tooling descritos em [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) e no [MAPA_DEBUG.md](MAPA_DEBUG.md).

---

## Fluxo de Trabalho & Contribuição

- Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para checklist de PR, convenções e padrões de branch.
- Acompanhe prioridades e entregas em [REFACTORING_STATUS.md](REFACTORING_STATUS.md) e [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md).
- Utilize [REFACTORING_PLAN.md](REFACTORING_PLAN.md) como referência ao iniciar refatorações.
- Registre alterações relevantes no [CHANGELOG.md](CHANGELOG.md) e mantenha relatórios em `docs/`.
- Para suporte rápido, veja o fluxo recomendado em [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) e no [FRONTEND_FINAL_REPORT.md](FRONTEND_FINAL_REPORT.md).

---

## Recursos Adicionais

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [TanStack Query](https://tanstack.com/query/latest)
- [Vitest](https://vitest.dev)
- [Zustand](https://docs.pmnd.rs/zustand/getting-started/introduction)
