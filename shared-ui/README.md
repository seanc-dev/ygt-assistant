# YGT Assistant Design System

The `@ygt-assistant/ui` package exposes the shared design language used across the product. It provides a typed set of design tokens along with primitive components that compose consistent surfaces inside the web app.

## Tokens

Tokens live under `shared-ui/src/tokens` and mirror the primitives exposed at runtime. Every token is exported via `@ygt-assistant/ui`:

- `colors` – semantic colors for surfaces, text, borders, brand accents, and status tones. The theme provider writes these into CSS custom properties for light/dark parity.
- `spacing` – a compact spacing scale (`quark`, `nano`, `xs`, …) used by the layout primitives.
- `typography` – font family, line heights, and size presets for text and headings.
- `radius` and `shadows` – rounded corners and elevation affordances used for panels and action bars.

Consumers can import the `tokens` object for direct values, or rely on the primitives which already map to those tokens.

## Primitives

The primitives are designed to compose quickly without re-implementing Tailwind snippets:

- `Box`, `Stack` – layout primitives for spacing, alignment, and flex direction.
- `Heading`, `Text` – typography helpers that lock fonts, sizes, and tone.
- `Panel` – the foundational surface used for cards, dashboards, and contextual panes. Supports tone variations (`default`, `soft`, `calm`) plus header/footers.
- `ActionBar` – fixed bar with a single primary action and optional secondary affordances, built to keep the main call-to-action visually dominant.
- `Button`, `Badge` – action and status primitives wired to the token palette.

All primitives are exported via `@ygt-assistant/ui` so pages can import a consistent toolkit:

```tsx
import { Panel, ActionBar, Button } from "@ygt-assistant/ui";
```

## Workflow surfaces

The web application now composes these primitives across its core flows:

- **Home dashboard** shows priority approvals, focus blocks, and Microsoft Graph health using calm, status-rich panels.
- **Review focus pane** highlights a single approval with contextual metadata, queue overview, and keyboard guidance surfaced in an `ActionBar`.
- **Copilot timeline** blends conversation messages, inline approvals, drafts, and undo toasts into a single calm surface.
- **Drafts workspace** replaces channel-specific UI with Outlook/Teams affordances while keeping creation inside a panel + action bar combo.
- **History timeline** groups activity by layer and exposes undo/replay affordances per event.
- **Connections & Automations** surfaces now share the same status badges, sync history panels, and guided CTAs built on the new primitives.

When authoring new surfaces prefer these primitives first. They encode spacing, typography, and theming decisions so new screens stay consistent with the design system.
