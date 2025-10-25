# AutoAudit Client

Modern React + TypeScript frontend for the AutoAudit compliance checking system.

## Tech Stack

- **Vite** - Lightning-fast build tool
- **React 18** - UI framework
- **TypeScript** - Type safety
- **SCSS Modules** - Scoped styling
- **TanStack Query** - Server state management
- **Framer Motion** - Animations (ready to use)
- **Lucide React** - Icons
- **Recharts** - Charts (ready to use)

## Project Structure

```
client/
├── src/
│   ├── components/
│   │   ├── ui/               # Reusable UI components
│   │   │   ├── Button/
│   │   │   ├── Card/
│   │   │   └── Badge/
│   │   ├── layout/           # Layout components
│   │   │   └── Layout.tsx
│   │   ├── charts/           # Chart components (TBD)
│   │   └── tables/           # Table components (TBD)
│   │
│   ├── pages/                # Page components
│   │   └── Dashboard.tsx
│   │
│   ├── lib/
│   │   ├── api/              # API client
│   │   │   └── client.ts
│   │   └── hooks/            # Custom React hooks (TBD)
│   │
│   ├── styles/               # Global styles
│   │   ├── variables.scss    # SCSS variables
│   │   └── global.scss       # Global styles
│   │
│   ├── types/                # TypeScript types
│   │
│   └── App.tsx               # Root component
│
├── .env                      # Environment variables
└── vite.config.ts            # Vite configuration
```

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env` (already done):

```bash
VITE_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Components

### UI Components (SCSS Modules)

#### Button

```tsx
import { Button } from './components/ui/Button';

<Button variant="primary" size="medium">
  Run Check
</Button>

<Button variant="secondary" size="small" fullWidth>
  Cancel
</Button>
```

**Variants:** `primary`, `secondary`, `success`, `danger`, `ghost`
**Sizes:** `small`, `medium`, `large`

#### Card

```tsx
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './components/ui/Card';

<Card hover>
  <CardHeader>
    <CardTitle>Compliance Score</CardTitle>
  </CardHeader>
  <CardContent>
    <p>Your content here</p>
  </CardContent>
  <CardFooter>
    <Button>View Details</Button>
  </CardFooter>
</Card>
```

#### Badge

```tsx
import { Badge } from './components/ui/Badge';

<Badge variant="success">Compliant</Badge>
<Badge variant="warning">Needs Review</Badge>
<Badge variant="error">Non-Compliant</Badge>
```

**Variants:** `success`, `warning`, `error`, `info`, `neutral`

### Layout

```tsx
import { Layout, PageHeader } from './components/layout';

<Layout>
  <PageHeader
    title="Dashboard"
    description="Overview of your compliance monitoring"
  />
  {/* Your page content */}
</Layout>
```

## API Client

The API client is fully typed and uses the FastAPI backend:

```tsx
import { projects, checks, urls, templates } from './lib/api/client';

// List projects
const projectList = await projects.list();

// Run a compliance check
const check = await checks.run({
  url: 'https://example.com/vehicle.htm',
  state_code: 'OK',
  skip_visual: false,
});

// Get check details
const checkDetails = await checks.get(checkId);
```

### Using with React Query

```tsx
import { useQuery, useMutation } from '@tanstack/react-query';
import { checks } from './lib/api/client';

function MyComponent() {
  // Fetch data
  const { data, isLoading, error } = useQuery({
    queryKey: ['checks', 'recent'],
    queryFn: () => checks.list({ limit: 10 }),
  });

  // Mutation
  const runCheck = useMutation({
    mutationFn: (data: CheckRequest) => checks.run(data),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['checks'] });
    },
  });

  return <div>{/* Your UI */}</div>;
}
```

## SCSS Modules

### Using Variables

```scss
@import '../../styles/variables.scss';

.myComponent {
  padding: $spacing-lg;
  background-color: $color-background;
  border-radius: $radius-md;
  box-shadow: $shadow-md;

  &:hover {
    box-shadow: $shadow-lg;
  }
}
```

### Available Variables

**Colors:**
- `$color-primary`, `$color-primary-dark`, `$color-primary-light`
- `$color-success`, `$color-warning`, `$color-error`, `$color-info`
- `$color-background`, `$color-surface`, `$color-border`
- `$color-text-primary`, `$color-text-secondary`, `$color-text-muted`

**Spacing:**
- `$spacing-xs` (0.25rem)
- `$spacing-sm` (0.5rem)
- `$spacing-md` (1rem)
- `$spacing-lg` (1.5rem)
- `$spacing-xl` (2rem)
- `$spacing-2xl` (3rem)

**Border Radius:**
- `$radius-sm`, `$radius-md`, `$radius-lg`, `$radius-xl`

**Shadows:**
- `$shadow-sm`, `$shadow-md`, `$shadow-lg`, `$shadow-xl`

**Transitions:**
- `$transition-fast` (150ms)
- `$transition-base` (200ms)
- `$transition-slow` (300ms)

## Real-Time Updates (WebSocket)

For live check progress updates:

```tsx
import { connectCheckStream } from './lib/api/client';
import { useState, useEffect } from 'react';

function CheckMonitor({ checkId }: { checkId: number }) {
  const [progress, setProgress] = useState({ status: 'pending', progress: 0 });

  useEffect(() => {
    const ws = connectCheckStream(checkId, (data) => {
      setProgress(data);
    });

    return () => ws.close();
  }, [checkId]);

  return (
    <div>
      <p>Status: {progress.status}</p>
      <progress value={progress.progress} max={100} />
    </div>
  );
}
```

## Adding Animations

Framer Motion is already installed:

```tsx
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, x: -20 }}
>
  <Card>...</Card>
</motion.div>
```

## Building for Production

```bash
npm run build
```

The optimized build will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Next Steps

### Components to Build

1. **RunCheckForm** - Form to initiate new compliance checks
2. **CheckProgress** - Real-time progress indicator with WebSocket
3. **ViolationsTable** - Data table for violations
4. **ComplianceTrendChart** - Chart showing compliance over time
5. **ProjectSelector** - Dropdown for switching projects
6. **URLManager** - CRUD interface for URLs

### Pages to Build

1. **Projects** - List and manage projects
2. **URLs** - Manage URLs to monitor
3. **Checks** - View all compliance checks with filters
4. **CheckDetail** - Detailed view of a single check
5. **Settings** - Configuration and preferences

### Features to Add

1. **Routing** - React Router for multi-page navigation
2. **Forms** - React Hook Form integration
3. **Data Tables** - TanStack Table for complex tables
4. **Error Boundaries** - Error handling
5. **Loading States** - Skeleton loaders
6. **Toast Notifications** - Success/error notifications
7. **Dark Mode** - Theme switcher

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Environment Variables

- `VITE_API_URL` - FastAPI backend URL (default: `http://localhost:8000`)

## TypeScript

All API responses are fully typed. The types are defined in `src/lib/api/client.ts` and match the OpenAPI specification from the backend.

## Contributing

1. Create a new component in `src/components/`
2. Use SCSS modules for styling
3. Export from an `index.ts` file
4. Add to this README

## Notes

- **No Tailwind** - Using SCSS modules for styling
- **No Next.js** - Using Vite for faster builds
- **Type-safe API** - All API calls are fully typed
- **React Query** - For efficient server state management

---

**Status:** ✅ Ready for Development
**Port:** 5173 (default Vite dev server)
