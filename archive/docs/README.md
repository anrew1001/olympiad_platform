# 🎯 Tactical Mission Briefing System

## Design Concept

A military-grade tactical interface that transforms the task catalog into a **high-tech mission deployment system**.

### Visual Language

**Cyberpunk Military HUD**
- Tactical corner brackets and targeting reticles
- Holographic scan lines and data streams
- Terminal-inspired monospace typography
- Electric energy pulses and glows
- CRT scanline overlay for authenticity

### Color Coding

**Threat Level System** (Difficulty 1-5):
```
LEVEL-1 █░░░░  GREEN   (#22c55e) - МИНИМАЛЬНАЯ
LEVEL-2 ██░░░  CYAN    (#06b6d4) - ПОНИЖЕННАЯ
LEVEL-3 ███░░  YELLOW  (#eab308) - СРЕДНЯЯ
LEVEL-4 ████░  ORANGE  (#f97316) - ПОВЫШЕННАЯ
LEVEL-5 █████  RED     (#ef4444) - КРИТИЧЕСКАЯ
```

## Component Architecture

### 1. **DifficultyBadge** - Threat Level Indicator
- Military-style threat bars (progressive fill)
- Animated scan line overlay
- Corner notch tactical element
- Glowing border matching threat level

### 2. **TopicBadge** - Mission Category Tag
- Holographic shimmer effect
- Angled corners (clip-path)
- Cyan indicator dot with glow
- Uppercase tracking for military feel

### 3. **TaskCard** - Mission Briefing Card
- **HUD Elements:**
  - 4 animated corner brackets (pulsing)
  - Scanning effect on hover
  - Energy pulse on activation
  - Holographic glow layer

- **Content Structure:**
  - Subject department tag
  - Mission ID (4-digit padded)
  - Threat level badge
  - Mission title (changes color on hover)
  - Category badge
  - "РАЗВЕРНУТЬ" deploy indicator

- **Interactions:**
  - Hover: Border color matches threat level
  - Hover: Glow shadow and scanning overlay
  - Hover: Corner brackets pulse faster
  - Click/Enter: Navigate to mission detail

### 4. **TaskFilters** - Mission Parameters Control
- **Container:**
  - Angled top-right corner notch
  - Scanning line animation
  - Bottom edge glow

- **Filter Inputs:**
  - Custom styled `<select>` dropdowns
  - Blue arrow indicators
  - Charging line animation on change
  - Active filter indicator with pulsing dot

### 5. **TaskGrid** - Mission Grid Display
- **Responsive Layout:**
  - Desktop: 3 columns
  - Tablet: 2 columns
  - Mobile: 1 column
  - 24px gap between cards

- **Loading State:** Tactical skeleton loaders
  - Vertical scanning animation
  - Corner brackets
  - Pulsing content blocks
  - Staggered appearance delay

- **Empty State:**
  - Rotating holographic icon (📡)
  - Expanding scan rings
  - Animated data stream bars
  - Helpful message in monospace

### 6. **TaskPagination** - Grid Coordinate Navigation
- **Container:**
  - Angled bottom-right corner
  - Cyan corner notches with glow
  - Scanning line overlay

- **Elements:**
  - Grid coordinates display (items X–Y / total)
  - Pulsing status indicator
  - Previous/Next buttons with arrows
  - Page number buttons:
    - Active: Blue glow with pulsing background
    - Hover: Cyan border and color
    - Ellipsis for page ranges

### 7. **Main Page** - Tactical Mission System
- **Background Layers:**
  - Animated tactical grid (60px cells)
  - Horizontal scan line (4s loop)
  - 15 vertical data stream particles
  - CRT scanline overlay

- **Header:**
  - Pulsing green status indicator
  - "TACTICAL MISSION SYSTEM" label
  - Large "БАЗА МИССИЙ" title with glow
  - Mission count display (top right)

- **Error Display:**
  - Red border with angled corners
  - Pulsing alert indicator
  - System error message in monospace

- **Footer:**
  - Online status indicator
  - System version label

## Animation Details

### Entrance Animations
- **Stagger:** Cards appear with 50ms delay between each
- **Duration:** 400ms with ease-out curve
- **Transform:** opacity 0→1, y 20px→0

### Hover Effects
- **Border:** Transition to threat-level color (300ms)
- **Glow:** Box shadow with matching color
- **Scan:** Vertical gradient overlay
- **Pulse:** Expanding border ring

### Loading Animations
- **Scan lines:** 2s vertical sweep per skeleton
- **Shimmer:** Pulse animation on gray blocks
- **Delay:** Staggered by index × 200ms

### Background Effects
- **Grid:** 30s diagonal movement
- **Scan line:** 4s vertical sweep
- **Particles:** 10-20s vertical float
- **Status dots:** 1.5s pulse loop

## Typography

- **Headers:** Sora Bold (existing design system)
- **Body:** Sora Regular
- **Technical:** JetBrains Mono
- **Labels:** UPPERCASE with 0.2–0.3em letter-spacing

## Accessibility

✅ **Keyboard Navigation:**
- All cards: `tabIndex={0}`
- Enter/Space: Activate card
- Tab: Focus next element

✅ **ARIA Labels:**
- Cards: `aria-label="Развернуть миссию: {title}"`
- Pagination: `aria-label="Страница {N}"`, `aria-current="page"`
- Filters: `<label htmlFor>` associations

✅ **Focus States:**
- Blue ring on focus-visible
- High contrast indicators

## Performance

**Optimizations:**
- CSS-only animations where possible
- Framer Motion for complex sequences
- `will-change: transform` on animated elements
- Stagger delays capped at 50ms × 6 cards max
- AnimatePresence for mount/unmount

**Bundle Impact:**
- Framer Motion: Already included in design system
- No additional dependencies
- Tailwind purge removes unused classes

## Usage Example

```tsx
import TasksPage from '@/app/tasks/page'

// URL patterns:
// /tasks
// /tasks?subject=informatics
// /tasks?subject=mathematics&difficulty=3
// /tasks?subject=informatics&difficulty=5&page=2
```

## Implementation Notes

### Required API
- `GET /api/tasks?subject={}&difficulty={}&page={}&per_page=20`
- Response: `PaginatedTaskResponse`

### Environment
- Next.js 16 App Router
- Client Component (`'use client'`)
- TypeScript strict mode
- Tailwind CSS v4

### Files Created
```
frontend/
├── lib/
│   ├── types/task.ts
│   ├── constants/tasks.ts
│   └── api/tasks.ts
├── components/tasks/
│   ├── DifficultyBadge.tsx
│   ├── TopicBadge.tsx
│   ├── TaskCard.tsx
│   ├── TaskFilters.tsx
│   ├── TaskGrid.tsx
│   └── TaskPagination.tsx
└── app/tasks/
    └── page.tsx
```

## Design Differentiation

**What makes this UNFORGETTABLE:**

1. **Military HUD Aesthetic** - Not just dark mode, but tactical interface
2. **Threat Level System** - Difficulty becomes a security classification
3. **Data Stream Background** - Living, breathing environment
4. **Corner Bracket Language** - Consistent tactical motif throughout
5. **Holographic Effects** - Layered transparency and glows
6. **Terminal Typography** - Uppercase monospace labels everywhere
7. **Mission Briefing Metaphor** - You're selecting ops, not browsing tasks

This is a **maximalist cyberpunk execution** with:
- 7+ animated background layers
- Per-card hover states with 4 effects
- Staggered entrance choreography
- Pulsing status indicators everywhere
- Custom clip-paths on every container
- Threat-level color theming system

The result: Users feel like they're in a **classified intelligence terminal**, not a course catalog.
