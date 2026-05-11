# Frontend Reference

## Design System
- `design-tokens.md` — Colors, spacing, typography, shadows, breakpoints
- `component-library.md` — Shared component catalog and usage guidelines
- `icons.md` — Icon set reference and usage

## Components
- `components/` — Per-component specifications
- `patterns/` — Recurring UI patterns (forms, modals, data tables)

## Accessibility (a11y)
- WCAG 2.2 AA compliance required
- Keyboard navigation for all interactive elements
- Screen reader testing with VoiceOver and NVDA
- Color contrast: 4.5:1 minimum for text, 3:1 for large text
- Focus indicators visible on all interactive elements

## Performance Budget
| Metric | Target |
|--------|--------|
| FCP (First Contentful Paint) | < 1.5s |
| LCP (Largest Contentful Paint) | < 2.5s |
| TBT (Total Blocking Time) | < 200ms |
| CLS (Cumulative Layout Shift) | < 0.1 |
| Bundle size (initial route) | < 150KB gzipped |

## File Naming
- Components: PascalCase (`UserProfile.tsx`)
- Hooks: camelCase with `use` prefix (`useAuth.ts`)
- Utilities: camelCase (`formatDate.ts`)
- Types: PascalCase with suffix (`UserProfile.types.ts`)
