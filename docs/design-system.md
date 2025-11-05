# LucidWork Design System

**Product:** LucidWork  
**Tagline:** "Work with clarity and calm."  
**Design Tone:** Calm intelligence. Quiet confidence. Productivity without stress.

## Core Brand Essence

LucidWork's design system embodies four guiding principles:

1. **Clarity** — Every pixel intentional.
2. **Calm** — Never noisy or over-animated.
3. **Flow** — Transitions guide attention naturally.
4. **Professionalism** — Subtle rounding, balanced typography, neutral palette.

## Design Quality Target

The experience should feel:
- **As calm as Apple Notes**
- **As professional as Microsoft Teams**
- **As fluid as Linear**

The user should subconsciously experience clarity and control; nothing flashes, everything glides.

---

## Typography

### Font Families

| Type | Font | Weight | Usage |
|------|------|--------|--------|
| **Primary** | Inter | 400 / 500 / 700 | All body text, labels, system text |
| **Secondary** | Space Grotesk | 500 / 700 | Headings, wordmark, section headers |

**Letter spacing:** +0.02em for uppercase headings.  
**Line height:** 1.45 for text blocks; 1.2 for headings.  
**Fallbacks:** system-ui, Segoe UI, sans-serif.

### CSS Variables

```css
--lw-font-body: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
--lw-font-heading: 'Space Grotesk', 'Inter', system-ui, -apple-system, sans-serif;
--lw-line-height-text: 1.45;
--lw-line-height-heading: 1.2;
--lw-letter-spacing-heading: 0.02em;
```

### Usage

```tsx
import { Text, Heading } from "@lucid-work/ui";

// Body text
<Text variant="body">Regular body text</Text>
<Text variant="muted">Secondary text</Text>

// Headings
<Heading variant="display">Display Heading</Heading>
<Heading variant="title">Section Title</Heading>
<Heading variant="subtitle">Subtitle</Heading>
```

---

## Shape, Depth, and Motion

### Corner Radius

- **Small UI elements:** 4px (`radius.sm`)
- **Cards/Panels:** 6px (`radius.md`)

### Shadows

Single soft shadow: **8% opacity black, y-offset = 2px, blur = 8px**

```css
--lw-shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
```

### Motion

**Core principle:** Animations should feel *barely faster than calm*—slowest possible while still feeling responsive.

#### Motion Curves

- **Easing:** `ease-in-out`
- **UI navigation:** 150–200ms
- **Inline interactions:** 180–240ms

#### Micro-motions

| Pattern | Duration | Easing | Effect |
|---------|----------|--------|--------|
| Queue card transitions | 180ms | ease-in-out | Fade + 8px slide up |
| Card expansion | 200ms | ease-in-out | Scale 1 → 1.02, then fade content in |
| Context panel | 220ms | ease-in-out | Opacity + width transition |
| Card hover | 150ms | ease-in-out | translateY -2px |

#### Reduced Motion

All animations respect `prefers-reduced-motion`. When enabled, animations are disabled or reduced to minimal durations.

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Color Systems

### Light Mode

| Token | Hex | Use |
|--------|------|------|
| primary | #2563EB | Core actions, links |
| secondary | #0EA5E9 | Highlights, active states |
| base | #F9FAFB | Background |
| neutral-text | #1E293B | Primary text |
| neutral-muted | #64748B | Secondary text, borders |
| success | #10B981 | Confirmations |
| warning | #FBBF24 | Caution |
| surface | #FFFFFF | Cards, panels |
| error | #DC2626 | Errors |

### Dark Mode

| Token | Hex | Use |
|--------|------|------|
| base | #0F172A | Canvas background |
| surface | #1E293B | Panels/cards |
| primary | #3B82F6 | Actions |
| secondary | #06B6D4 | Highlights |
| text-primary | #F1F5F9 | Body text |
| text-muted | #94A3B8 | Secondary text |
| success | #34D399 | Confirmations |
| warning | #FACC15 | Alerts |
| error | #F87171 | Errors |

### High-Contrast Mode

| Token | Hex | Use |
|--------|------|------|
| base | #FFFFFF | Background |
| text-primary | #000000 | Text |
| accent-1 | #0000FF | Primary actions |
| accent-2 | #00AEEF | Secondary highlights |
| error | #FF0000 | Alerts |
| success | #007E33 | Confirmations |

### Color-Blind Safe Palette

Designed to be distinguishable for protanopia, deuteranopia, and tritanopia.

| Role | Color | Notes |
|------|--------|-------|
| Primary | #1F77B4 | Blue, safe across types |
| Success | #2CA02C | Green, balanced contrast |
| Warning | #FF7F0E | Orange-amber |
| Info | #17BECF | Cyan variant |
| Error | #D62728 | Deep red, still separable |
| Background | #F8F9FA | Neutral |

**Usage:** Optional color-blind toggle in accessibility settings.

---

## Spacing & Layout

### Grid System

- **Base:** 8px spacing system
- **Density:** Comfortable by default; compact toggle available
- **Whitespace:** Vertical rhythm between sections 32px minimum

### Spacing Scale

| Token | Value | Use |
|-------|-------|-----|
| xs | 0.5rem (8px) | Base unit |
| sm | 0.75rem (12px) | Tight spacing |
| md | 1rem (16px) | Standard spacing |
| lg | 1.5rem (24px) | Section spacing |
| xl | 2rem (32px) | Vertical rhythm minimum |

### CSS Variables

```css
--lw-spacing-xs: 0.5rem; /* 8px */
--lw-spacing-md: 1rem; /* 16px */
--lw-spacing-lg: 1.5rem; /* 24px */
--lw-spacing-xl: 2rem; /* 32px */
```

---

## UI/UX Layout Principles

### Hierarchy

- Top-down visual clarity
- Never more than three visual weights per screen

### Cards

- Flat by default
- Subtle elevation on hover (translateY −2px, 150ms)
- Radius: 6px

### Modal Behavior

- Center-fade animation
- Backdrop blur: 6px
- Duration: 200ms ease-in-out

### Grid

- 8px spacing base
- Comfortable density by default
- Compact toggle available

---

## Components

### Button

**Variants:**
- `solid` (primary): Core actions
- `outline` (secondary): Secondary actions
- `ghost` (tertiary): Tertiary actions

**Sizes:** `sm`, `md`, `lg`

**Design:**
- Rounded 4px
- Focus glow @ 40% opacity
- Calm transitions (180ms)

```tsx
import { Button } from "@lucid-work/ui";

<Button variant="solid" size="md">Primary Action</Button>
<Button variant="outline">Secondary</Button>
<Button variant="ghost">Tertiary</Button>
```

### Card/Panel

**Tones:**
- `default`: Standard surface
- `soft`: Muted background
- `calm`: Accent-tinted background

**Features:**
- Hoverable: Subtle elevation on hover
- Expandable: Scale animation for inline expansion
- Radius: 6px

```tsx
import { Panel } from "@lucid-work/ui";

<Panel title="Card Title" hoverable expandable>
  Content here
</Panel>
```

### Modal

**Features:**
- Center-fade animation
- Backdrop blur (6px)
- Close on backdrop click (optional)
- Close on Escape key (optional)

```tsx
import { Modal } from "@lucid-work/ui";

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Modal Title"
  size="md"
>
  Content here
</Modal>
```

### Tooltip

**Features:**
- Appears on hover + focus
- Delay: 200ms
- Accessible with ARIA attributes
- Positions: top, bottom, left, right

```tsx
import { Tooltip } from "@lucid-work/ui";

<Tooltip content="Helpful tip" position="top">
  <button>Hover me</button>
</Tooltip>
```

### Inputs

**Design:**
- Rounded 4px
- Focus glow: primary @ 40% opacity
- Accessible focus states

### Tables

- Fixed header (optional)
- Zebra row optional for focus view
- Accessible markup

---

## Accessibility

### Contrast Ratio

- **Minimum:** ≥ 4.5:1 for text
- **Enhanced:** ≥ 7:1 for high-contrast mode

### Keyboard Focus

- Visible outline: primary color @ 70% opacity
- Clear focus indicators on all interactive elements

### Animations

- Respects `prefers-reduced-motion`
- Essential animations can be disabled
- No auto-playing animations

### ARIA

- Roles applied for queue cards, chat threads, defer actions
- Proper labeling for screen readers
- Semantic HTML structure

### Tooltips

- Appear on hover + focus
- Delay: 200ms
- Accessible with ARIA tooltip role

---

## Verbal Identity & Microcopy

**Tone:** Precise, calm, and efficient. Avoid metaphors, emojis, or excessive personality.

### Key Messages

| Context | Copy |
|----------|------|
| Greeting | "Your day is ready." |
| Completion | "All clear for now." |
| Reminder | "Next up, one quick thing." |
| Success | "Done with clarity." |
| Loading | "Preparing your workspace…" |
| Support | "Need context? I can summarize it." |

### Usage

```tsx
import microcopy from "../copy/microcopy.json";

<span>{microcopy.greeting}</span>
<span>{microcopy.success}</span>
```

---

## Theme System

The design system supports four theme modes:

1. **Light** (default)
2. **Dark**
3. **High-Contrast**
4. **Color-Blind Safe**

### Theme Provider

```tsx
import { ThemeProvider, useTheme } from "@lucid-work/ui";

function App() {
  return (
    <ThemeProvider defaultTheme="system">
      <YourApp />
    </ThemeProvider>
  );
}

function YourComponent() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  
  return (
    <select value={theme} onChange={(e) => setTheme(e.target.value)}>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
      <option value="high-contrast">High Contrast</option>
      <option value="color-blind">Color Blind Safe</option>
      <option value="system">System</option>
    </select>
  );
}
```

---

## CSS Variables Reference

All design tokens are available as CSS variables:

### Colors
```css
--lw-primary
--lw-secondary
--lw-base
--lw-neutral-text
--lw-neutral-muted
--lw-success
--lw-warning
--lw-error
--lw-surface
--lw-border
```

### Spacing
```css
--lw-spacing-xs
--lw-spacing-md
--lw-spacing-lg
--lw-spacing-xl
```

### Typography
```css
--lw-font-body
--lw-font-heading
--lw-line-height-text
--lw-line-height-heading
--lw-letter-spacing-heading
```

### Radius
```css
--lw-radius-sm (4px)
--lw-radius-md (6px)
```

### Shadows
```css
--lw-shadow-sm
```

### Motion
```css
--lw-duration-fast (150ms)
--lw-duration-normal (180ms)
--lw-duration-slow (200ms)
--lw-easing (ease-in-out)
```

---

## Implementation Notes

### Importing Components

```tsx
import {
  Button,
  Panel,
  Modal,
  Tooltip,
  Text,
  Heading,
  ThemeProvider,
} from "@lucid-work/ui";
```

### Using Design Tokens

```tsx
import { tokens } from "@lucid-work/ui";

const primaryColor = tokens.colors.light.primary;
const spacing = tokens.spacing.xl;
const radius = tokens.radius.md;
```

### Tailwind Integration

The design system is integrated with Tailwind CSS. Use Tailwind classes or CSS variables:

```tsx
// Using Tailwind classes
<div className="bg-primary text-text-primary rounded-md p-xl">

// Using CSS variables
<div className="bg-[var(--lw-primary)] text-[var(--lw-neutral-text)] rounded-md p-[var(--lw-spacing-xl)]">
```

---

## Resources

- **Design Tokens:** `shared-ui/src/tokens/`
- **Components:** `shared-ui/src/primitives/`
- **Theme CSS:** `web/src/styles/theme.css`
- **Microcopy:** `web/src/copy/microcopy.json`
- **Tailwind Config:** `web/tailwind.config.js`

---

## Design Rationale

### Why These Choices?

1. **Calm Colors:** Neutral palette reduces visual noise, allowing users to focus on content and actions.
2. **Slow Animations:** Longer durations (150-240ms) feel intentional and calm, not rushed.
3. **Subtle Depth:** Minimal shadows and elevation create hierarchy without overwhelming.
4. **Accessible by Default:** High-contrast and color-blind modes ensure everyone can use the product.
5. **Clear Typography:** Inter for body (readability) + Space Grotesk for headings (personality).

### Comparison to Other Products

- **Apple Notes:** Calm, minimal, focused
- **Microsoft Teams:** Professional, accessible, structured
- **Linear:** Fluid, fast, delightful

LucidWork combines the best of all three: calm minimalism, professional accessibility, and fluid interactions.

---

## Changelog

### v1.0.0 (Current)
- Initial design system implementation
- Light/Dark/High-Contrast/Color-Blind themes
- Button, Panel, Modal, Tooltip components
- Complete token system
- Typography system with Inter + Space Grotesk
- Motion system with calm animations
- Accessibility features
