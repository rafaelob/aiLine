# Sprint 37: Mega Front-End Soft Clay UX & Emotional Safety Core

**Status:** Planned
**Owner:** @frontend-team
**Dates:** TBD

## Objetivo (Goal)
Transformar a experiência bruta e funcional do MVP em uma experiência original, acessível, tátil e imersiva. Esta "Mega Sprint" varre a base de código e consolida o Sprint 29 (Soft Clay Design System) com o pilar de Segurança Emocional (Sprint 34), criando um frontend com personalidade única. Substitui elementos HTML nativos pulverizados por uma biblioteca de componentes Atômica (cva, tailwind-variants) focada em acessibilidade (A11y AAA) e micro-interações ("Soft Clay 2.5D").

## Motivação (Por que falta isso no código atual?)
Atualmente, `frontend/src/components/ui/` contém apenas componentes isolados (`toast`, `skeleton`, `page-transition`). Não há uma base de botões, inputs, cards e layouts compartilhados.
- **Design com Personalidade:** O aplicativo funciona, mas parece uma interface padrão sem alma. Precisamos de bordas de 20px, sombras suaves, texturas ("Clay"), e animações orquestradas.
- **Acessibilidade Emocional:** Interfaces normais punem com "Verde" (Sucesso) e "Vermelho" (Erro). Crianças neurodivergentes e usuários do AiLine precisam de tons encorajadores (ex: Âmbar e Azul), feedback que preserva a dignidade, e adaptações nativas nos componentes base.
- **Ilustrações Nativas:** Faltam SVGs procedurais e orgânicos integrados nos estados vazios (empty states) e on-boarding, que respondam ao modo escuro e de alto contraste.

## Escopo Consolidado (Stories & Tasks)

### Fase 1: Fundação do Design System Atômico "Soft Clay"
- [ ] **F-MEGA-01: Globals & Tokens.** Migrar `globals.css` para um sistema de tokens semântico CSS variáveis (Azure #1E4ED8 / Sage #10B981 / Amber #F59E0B). Adicionar paleta "Feedback Seguro" (sem vermelhos agressivos).
- [ ] **F-MEGA-02: Tipografia Orgânica.** Implementar tipografia Inter + Plus Jakarta Sans com escala fluida (`clamp()`).
- [ ] **F-MEGA-03: Primitivos UI base (cva).** Criar os arquivos em `src/components/ui/`: `Button`, `Input`, `Card`, `Badge`, `Dialog`. Todos com estados Soft Clay (sombra em camadas, hover flutuante, focus-visible WCAG offset).
- [ ] **F-MEGA-04: Transições e MotionKit.** Componente `MotionConfig` global (respeitando `prefers-reduced-motion`) com animações de mola (`spring`) que parecem elásticas e divertidas, mas desligáveis para usuários autistas (Quiet Mode).

### Fase 2: Sistema de Ilustração em SVG Orgânico
- [ ] **F-MEGA-05: IllustrationBase e Filtros Clay.** Framework para SVGs 2.5D reagirem a cores do tema, inserindo ruído e textura CSS (`<filter id="clay-texture">`).
- [ ] **F-MEGA-06: Kit de Empty States e Mascotes.** Desenhar (via SVGs codificados) as ilustrações: `TutorEmptyState`, `NotFoundPlanet`, `LoadingClouds`.
- [ ] **F-MEGA-07: Avatares Inclusivos e Ícones.** Remover `<svg>` inline do projeto inteiro e unificar sob componentes iconográficos (`LucideReact` customizados e combinados com SVGs autorais).

### Fase 3: Layouts Acessíveis (Bento Grids & Cockpits)
- [ ] **F-MEGA-08: Layout Bento Grid do Dashboard.** Refatorar `DashboardView` de uma lista linear para um grid em blocos "Bento", tátil, responsivo (CSS Grid `auto-fit`).
- [ ] **F-MEGA-09: Master-Detail (Tablet/Mobile).** Sistema de navegação de contexto duplo para o painel de tutor, mantendo o usuário seguro sem mudanças bruscas de tela (Painel de navegação fixo).
- [ ] **F-MEGA-10: Modo Escuro & Alto Contraste Nativo.** Habilitar o toggle nativo em todo componente, assegurando WCAG AAA text/bg ratio no modo noturno e em telas High Contrast do Windows.

### Fase 4: Componentes de Segurança Emocional
- [ ] **F-MEGA-11: Timer Pie-Chart Visual (Não numérico).** Substituto de relógios digitais estressantes por um disco preenchendo suavemente para TDAH.
- [ ] **F-MEGA-12: The Parking Lot (Estacionamento de Ideias).** Sidebar flutuante para a criança guardar pensamentos distratores, preservando o foco.
- [ ] **F-MEGA-13: Stepping Stones (Path de Tarefas SVG).** Em vez de checklist massivas de texto, tarefas mostradas como "pedras num rio" usando um SVG animado para indicar progresso (aria-current="step").
- [ ] **F-MEGA-14: Quiet Mode Toggle (Modo Foco).** Um único botão no topo que torna todas as cores tons de cinza com um toque de azul, e remove todas as animações e estímulos sociais (Sensory Processing).

### Fase 5: Micro-interações, Som & Refinamento Sensorial (State of the Art)
- [ ] **F-MEGA-15: Feedback Sonoro Não-Intrusivo (Sound Design).** Hooks de áudio (`useSound`) com sons orgânicos (marimbas, bolhas de água) para success/error, totalmente mutáveis via configurações de acessibilidade.
- [ ] **F-MEGA-16: Temas Sensoriais por Persona.** Além de claro/escuro, criar presets como "Oceano Calmo" (baixo contraste p/ autismo) e "Foco Absoluto" (alto contraste + monocromático para Baixa Visão/TDAH severo).
- [ ] **F-MEGA-17: Scroll-telling & Parallax Suave.** Garantir que a Landing Page e o Onboarding contenham revelações ao scroll usando a biblioteca de animação (Framer Motion/Tailwind anims), elevando o app ao padrão de aplicativos premiados ("Wow Factor").
- [ ] **F-MEGA-18: Feedback Tátil (Haptic Feedback).** Conectar botões críticos à API `navigator.vibrate` (para PWA mobile), reforçando ações físicas quando o usuário completa tarefas.

## Critérios de Aceite (DoD)
- O terminal relata `0 lint errors`, TypeScript 100% forte para todos os novos SVGs e componentes UI.
- Auditados no Lighthouse/Axe: Nenhuma falha AAA, Focus outlines não rompem visibilidade.
- Visualmente: O aplicativo aparenta ser de nível de investimento Serie A, lembrando apps lúdicos premium como Duolingo, mas com maturidade educacional de Khan Academy.
- Nenhum código implementado de lógica backend, APENAS design system, layouts estruturais, e ilustrações.

## Arquivos Desenhados como "Esqueletos" Nesta Mega-Sprint:
- `frontend/src/components/ui/button.tsx` (Esqueleto CVA)
- `frontend/src/components/ui/card.tsx` (Esqueleto Bento)
- `frontend/src/components/ui/illustrations/base-clay-svg.tsx` (Filtro e textura base)
- `frontend/src/components/ui/illustrations/empty-state.tsx` (Cena SVG)
- `frontend/src/components/layout/bento-dashboard.tsx` (A11y grid skeleton)
