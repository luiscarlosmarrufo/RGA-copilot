# UI Spec

## 1. Identity

**Style: Corporate Luxury.** Bloomberg / Palantir / private bank, not generic SaaS. The UI should feel like a serious analytical instrument that happens to be beautiful — not a friendly assistant cosplay.

Language: **Spanish only** for all user-facing copy. English is forbidden in the UI.

## 2. Palette

| Token | Hex | Use |
|---|---|---|
| `--navy-deep` | `#08153A` | Primary surface, sidebar, header |
| `--charcoal` | `#1A1F2A` | Card surfaces, secondary background |
| `--black` | `#000000` | Backgrounds behind navy on OLED-friendly screens |
| `--silver` | `#C5CCD6` | Borders, divider lines, secondary text |
| `--soft-white` | `#F4F6FA` | Primary text on dark surfaces |
| `--turquoise` | `#1FE0D2` | Accent — top card line, focus rings, semaphore "go" |

Single accent rule: **one turquoise element per visual zone.** Multiple turquoise highlights cheapen the design.

## 3. Typography

- **Display / numbers:** a monospaced display face (target: Berkeley Mono, JetBrains Mono fallback). Financial numbers always monospaced.
- **Body / labels:** a transitional sans (target: Inter, Söhne fallback).
- Numbers are tabular figures, right-aligned.
- Currency uses MXN with `MX$` prefix, e.g. `MX$1,234,567.89`. Margins shown as percentages with one decimal.

## 4. Layout

### 4.1 Fixed sidebar

- Always visible at ≥ 1024 px; collapses to a 72 px rail at smaller widths.
- Background `--navy-deep`. Items in `--soft-white`. Active item has a 2 px `--turquoise` left edge.
- Order: **Dashboard · Reportes · Documentos · Tareas · Roadmap · Perfil**.
- A **circular RGA logo** sits at the top of the sidebar. Circle, not square. White-on-navy.

### 4.2 Main canvas

- Three-column grid on wide screens (12-col CSS grid; cards span 3–6 cols).
- 24 px gutter, 32 px outer padding.
- No drop shadows. Surfaces are flat; depth comes from `--silver` 1 px borders and small tone differences.

## 5. Atomic client cards

- **One insight per card.** Never two.
- Rounded corners, radius `12 px`.
- Border: 1 px `--silver` at 20% opacity.
- **Top accent:** a 2 px horizontal `--turquoise` line, full width, sitting on the top edge.
- Internal padding: `20 px`.
- Card anatomy (top → bottom):
  1. Eyebrow label — uppercase, `--silver`, 11 px, tracking `+0.06em`.
  2. Headline metric — big monospaced number.
  3. Delta / trend — one short line with arrow + colored delta.
  4. Footnote — single-line citation back to the metric source (Spanish, e.g. *"Calculado de 8,101 filas — Periodo ENE–MAR 2026"*).

## 6. Premium financial semaphore

A three-state pill rendered next to alert-bearing cards.

| Estado | Color | Significado |
|---|---|---|
| **Saludable** | `--turquoise` | dentro de banda |
| **Atención** | amber `#E8B341` | desviación moderada |
| **Crítico** | red `#E0533D` | rebasa umbral HIGH |

The semaphore never replaces the number. It annotates it.

## 7. Chat surface

- **Optimistic UI.** The user's bubble appears immediately on submit.
- While waiting: a "Pensando…" indicator beneath the input.
- **Semantic routing chips** stream in above the response: `Analizando margen` → `Consultando memoria` → `Redactando`. Chips appear as small pill outlines in `--silver`; the active one glows in `--turquoise`.
- The chips show *that* routing happened, not *how*. Never expose chain-of-thought or intermediate tokens.
- Each Claude response shows **evidence**: a row of small citation chips (metric, memory, lugar). Clicking a chip opens the cited row/entry in a side panel.

## 8. Empty / error states

- All copy in Spanish.
- "Datos de mercado no disponibles" when Places/Pytrends snapshot absent — never blocks the rest of the dashboard.
- Upload errors show the typed parser code (e.g. *"No se encontró la hoja BD 2026"*) and a remediation hint.

## 9. Accessibility

- Minimum contrast on text: 4.5:1.
- Turquoise is decorative; never the sole carrier of meaning (always paired with text/icon).
- Focus rings: 2 px `--turquoise`, 2 px offset.
- Tab order matches visual order. Sidebar is a single tabstop with arrow-key navigation.

## 10. What we never do

- Emoji in product copy.
- Gradient backgrounds.
- Multiple accent colors.
- "Friendly" microcopy ("¡Hola!" "¡Listo!"). Tone is calm, declarative.
- Showing raw chain-of-thought.
- Showing a number without a citation source.
