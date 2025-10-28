# Cockpit Híbrido – Guia de Integração UX

## Componentes Principais
1. **Pulse Bar** – barra superior com arousal, dopamina, ESGT (cores degradê).
2. **Safety Sentinel** – widget com estado do kill switch, violações ativas, botão “ver incident report”.
3. **Skill Matrix** – tabela responsiva mostrando habilidades ativas (MAXIMUS skill learning).
4. **Event Timeline** – feed unificado (CLI + MAXIMUS), filtrável por severity/context.

## Estados & Feedback
| Estado | Comportamento | Ação do usuário |
|--------|---------------|-----------------|
| Normal | Atualização contínua, verdes | Nenhuma |
| Aviso | Laranja, tooltip explicando | Abrir detalhes, avaliar contexto |
| Crítico | Vermelho, banner + som opcional | Revisar Safety Sentinel, acionar playbook |
| Streaming off | Indicador cinza/“Offline” | Oferecer botão “Tentar novamente” |

## Regras Visuais
- Usar a paleta cyberpunk (ciano, magenta, neon green) com contrastes > 4.5.
- Animar transições (300ms) para evitar “tremores”.
- Mostrar timestamps em formato humano + UTC (hover).
- Incluir tooltips com `context.trigger` (ex.: “HSAS alerta #12345”).

## Interações do CLI
- Comandos disponíveis:
  - `/stream status` → mostra clientes conectados.
  - `/stream pause` / `/stream resume`.
  - `/stream tail --severity=high` → filtra localmente.
- CLI apresenta visual similar (Sparkline ASCII + badges de severity).

## Fallback
- Se streaming indisponível:
  - Frontend: usar polling (REST `/maximus/v1/events`) com badge “Modo degr. gracioso”.
  - CLI: mensagem “stream offline” + opção de replay de backlog.

## Checklist UX
1. Widgets autocontidas (pode remover sem quebrar layout).
2. Responsividade testada (desktop, 1280x720, 1920x1080).
3. Acessibilidade: atalhos de teclado para mudar filtros, aria-labels.
4. Documentar stories no design system / Storybook (se aplicável).
