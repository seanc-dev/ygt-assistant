# LucidWork UI Structure

## Overview

LucidWork is a Microsoft-first web MVP focused on unified action items, schedule management, and chat-first workroom collaboration.

## Page Structure

### Hub (`/hub`)
- **Queue** (`/hub/queue`): Action items from Outlook, Teams, and Docs change summaries
- **Schedule** (`/hub/schedule`): Today-first schedule merged with existing calendar events
- **Brief** (`/hub/brief`): Daily orientation with optional weather/news

### Workroom (`/workroom`)
- Chat-first interface with Project → Task → Threads hierarchy
- Kanban toggle (`?kanban=1`) for board view
- Multiple threads per task

### History (`/history`)
- Timeline of all actions and changes

### Settings (`/settings`)
- Work hours configuration
- Translation rules
- Trust levels (training-wheels/standard/autonomous)
- UI preferences

## Design Principles

### Inline Expansion
- Cards expand within the grid, pushing siblings
- No overlays by default
- Height capped at `min(60% column height, 70vh)`
- Inner scroll if content overflows

### Keyboard Shortcuts
- `A`: Approve/Reply
- `E`: Edit
- `D`: Defer
- `T`: Add to Today
- `O`: Open in Workroom
- `Esc`: Collapse
- `⌘K`: Kanban toggle (Workroom)

### Layout Rules
- Grid-based layout with CSS Grid
- Responsive: mobile-first, scales to desktop
- Push layout: expanding cards resize grid, not overlay

