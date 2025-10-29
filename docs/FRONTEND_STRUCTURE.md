# Frontend Structure Documentation

**Framework**: React 18 + TypeScript + Vite
**State Management**: RTK Query (Redux Toolkit)
**Styling**: CSS Modules + SCSS
**Routing**: React Router v6

## Directory Structure

```
client/src/
├── main.tsx                    # App entry point
├── App.tsx                     # Root component with routing
├── components/
│   ├── layout/
│   │   └── Layout.tsx          # Main layout wrapper
│   └── ui/                     # Reusable UI components
│       ├── Badge/
│       ├── Button/
│       ├── Card/
│       ├── ConfirmModal/
│       ├── Input/
│       ├── Modal/
│       ├── ThemeToggle/
│       ├── Toast/
│       └── Toggle/
├── contexts/
│   ├── ModalContext.tsx        # Global modal management
│   └── ThemeContext.tsx        # Theme (light/dark) management
├── features/                   # Feature-based organization
│   ├── auth/
│   │   └── components/
│   │       ├── AuthModal.tsx   # Login/register modal
│   │       └── AuthGate.tsx    # Protected route wrapper
│   ├── checks/
│   │   └── components/
│   │       └── CheckDetailModal.tsx
│   ├── config/
│   │   └── components/
│   │       ├── PageTypeSettingsModal.tsx
│   │       └── PageTypesTable.tsx
│   ├── projects/
│   │   ├── pages/
│   │   │   ├── ProjectsPage.tsx
│   │   │   └── ProjectDetailPage.tsx
│   │   └── components/
│   │       └── CreateProjectModal.tsx
│   └── urls/
│       └── components/
│           ├── AddURLModal.tsx
│           ├── EditURLModal.tsx
│           └── URLList.tsx
├── pages/
│   ├── ConfigPage.tsx          # Main config page with tabs
│   └── Config/                 # Config page tab components
│       └── tabs/
│           ├── PageTypesTab.tsx    # (default tab, from features/config)
│           ├── StatesTab.tsx
│           ├── RulesTab.tsx
│           ├── PreamblesTab.tsx
│           ├── LLMTab.tsx          # LLM usage tracking and model config
│           └── OtherTab.tsx
│       └── components/
│           ├── AddStateModal.tsx
│           ├── StateConfigModal.tsx
│           ├── AddLegislationModal.tsx
│           ├── LegislationDetailsModal.tsx
│           ├── RuleDetailModal.tsx
│           ├── CreatePreambleModal.tsx
│           └── CreateVersionModal.tsx
├── services/
│   └── api.ts                  # API client configuration
└── store/
    └── api/
        ├── apiSlice.ts         # RTK Query base configuration
        └── statesApi.ts        # State/legislation API endpoints

<system-reminder>
The TodoWrite tool hasn't been used recently. If you're working on tasks that would benefit from tracking progress, consider using the TodoWrite tool to track progress. Also consider cleaning up the todo list if has become stale and no longer matches what you are working on. Only use it if it's relevant to the current work. This is just a gentle reminder - ignore if not applicable.


Here are the existing contents of your todo list:

[1. [completed] Analyze codebase structure and migration system
2. [completed] Document database schema and current state
3. [completed] Find and document external migration system
4. [completed] Document API structure
5. [in_progress] Document frontend structure and data flow
6. [pending] Create CLAUDE.md master index with all subdocs]
</system-reminder>```

## Key Pages & Routes

### Main Routes (App.tsx)
- `/` - ProjectsPage (list of all projects)
- `/projects/:id` - ProjectDetailPage (single project with URLs)
- `/config` - ConfigPage (system configuration tabs)

### ConfigPage Tabs (Updated 2025-10-28)
- **Page Types** - Manage dealership page type definitions (default tab)
- **States** - Manage states and legislation sources
- **Preambles** - Manage preamble templates and versions
- **Rules** - View and approve compliance rules
- **Other** - Demo utilities (delete data, etc.)
- **LLM Usage** - View LLM usage stats, logs, and configure models per operation

## State Management (RTK Query)

### API Slices
Located in `client/src/store/api/`

**apiSlice.ts** - Base configuration
- baseUrl: `http://localhost:8000/api`
- Tag types: Projects, URLs, Checks, PageTypes, States, Legislation, Digests, Rules, Preambles, LLMLogs, LLMStats, ModelConfigs
- Auth: JWT token from localStorage

**statesApi.ts** - States & Legislation endpoints
- `useGetStatesQuery()` - Fetch all states
- `useGetStateByCodeQuery(code)` - Fetch single state
- `useUploadLegislationMutation()` - Upload PDF legislation
- `useGetLegislationSourcesQuery()` - Fetch legislation sources
- `useDeleteLegislationSourceMutation()` - Delete source + cascade
- `useGetLegislationDigestsQuery(sourceId)` - Fetch digests for source
- Plus: Create/update/delete for all entities

**llmApi.ts** - LLM tracking & configuration endpoints (Added 2025-10-28)
- `useGetLLMLogsQuery()` - Fetch LLM logs with filtering
- `useGetLLMStatsQuery()` - Fetch aggregate statistics
- `useGetAvailableModelsQuery()` - Fetch available OpenAI models
- `useGetModelConfigsQuery()` - Fetch model configurations
- `useUpdateModelConfigMutation()` - Update model for operation type

### Cache Invalidation Strategy
RTK Query uses tag-based invalidation:
```typescript
// Example from statesApi
provideTags: (result) =>
  result
    ? [
        ...result.items.map(({ id }) => ({ type: 'States' as const, id })),
        { type: 'States', id: 'LIST' }
      ]
    : [{ type: 'States', id: 'LIST' }],

invalidatesTags: [{ type: 'States', id: 'LIST' }]
```

## Context Providers

### ModalContext
**Purpose**: Global modal state management
**Usage**:
```tsx
const { openModal, closeModal } = useModal();

openModal(<MyModalComponent onClose={closeModal} />);
```

**Implementation**:
- Single modal rendered at app root
- Stack-based for nested modals (not yet implemented)
- Escape key to close

### ThemeContext
**Purpose**: Light/dark theme management
**Usage**:
```tsx
const { theme, toggleTheme } = useTheme();
```

**Implementation**:
- Persisted to localStorage
- CSS variables in `:root` and `[data-theme="dark"]`
- Theme toggle button in layout header

## Component Patterns

### UI Components (components/ui/)
All use CSS Modules with TypeScript:

```tsx
// Button.tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  ...
}) => (
  <button className={styles[variant]} {...props}>
    {children}
  </button>
);
```

### Modal Components
Standard modal pattern:

```tsx
interface MyModalProps {
  isOpen: boolean;
  onClose: () => void;
  // ... other props
}

export const MyModal: React.FC<MyModalProps> = ({ isOpen, onClose }) => {
  const [createThing] = useCreateThingMutation();

  const handleSubmit = async () => {
    await createThing(data);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="...">
      {/* Form content */}
    </Modal>
  );
};
```

## Key Workflows

### Upload & Parse Legislation Flow
1. User clicks "Add Legislation" in StatesTab
2. Opens AddLegislationModal
3. User uploads PDF file
4. Calls `uploadLegislation` mutation:
   ```tsx
   const [uploadLegislation] = useUploadLegislationMutation();
   await uploadLegislation({
     file: pdfFile,
     state_code: 'OK',
     statute_number: '...',
     title: '...'
   });
   ```
5. Backend parses PDF, creates digests
6. Modal shows success screen with next steps
7. Invalidates 'Legislation' cache, UI updates

### Generate Rules from Legislation
1. User clicks "Re-digest" button in StateConfigModal
2. Calls `POST /api/rules/legislation/{source_id}/digest`
3. Backend extracts atomic rules via LLM
4. Returns rules + collision detections
5. UI shows rules in RulesTab for approval

### Create Project Flow
1. User clicks "New Project" in ProjectsPage
2. Opens CreateProjectModal
3. User fills: name, state, base URL
4. Validates state has approved rules:
   ```tsx
   const { data: rulesData } = useGetRulesQuery({
     state_code: selectedState,
     approved: true
   });

   if (!rulesData?.items?.length) {
     setError("No approved rules for this state");
     return;
   }
   ```
5. Creates project
6. Redirects to ProjectDetailPage

## Styling Architecture

### CSS Modules Pattern
Each component has a corresponding `.module.scss` file:

```
Button/
  ├── Button.tsx
  └── Button.module.scss
```

Usage in component:
```tsx
import styles from './Button.module.scss';

<button className={styles.primary}>Click</button>
```

### Global Styles
Located in `client/src/index.css`:
- CSS variables for colors, spacing
- Theme switching via `[data-theme]` attribute
- Typography base styles

### Theme Variables
```css
:root {
  --color-primary: #3b82f6;
  --color-bg: #ffffff;
  --color-text: #1f2937;
}

[data-theme="dark"] {
  --color-bg: #1f2937;
  --color-text: #f9fafb;
}
```

## Authentication Flow

### Login/Register
1. User opens AuthModal (triggered by AuthGate)
2. Submits credentials
3. Backend returns JWT access + refresh tokens
4. Tokens stored in localStorage:
   ```tsx
   localStorage.setItem('access_token', token);
   localStorage.setItem('refresh_token', refreshToken);
   ```
5. Redirect to app

### Protected Routes
Wrapped in AuthGate:
```tsx
<AuthGate>
  <ProjectsPage />
</AuthGate>
```

AuthGate checks for token, shows AuthModal if missing.

### Token Refresh
Handled automatically by RTK Query middleware:
- Intercepts 401 responses
- Calls `/api/auth/refresh`
- Retries original request with new token

## Error Handling

### API Errors
RTK Query provides error state:
```tsx
const { data, error, isLoading } = useGetStatesQuery();

if (error) {
  return <div>Error: {error.message}</div>;
}
```

### Toast Notifications
Global toast system (ToastContainer in App.tsx):
```tsx
import { toast } from './components/ui/Toast/Toast';

toast.success('Legislation uploaded!');
toast.error('Upload failed');
```

## Form Validation

Most forms use basic HTML5 validation:
```tsx
<input
  type="text"
  required
  minLength={3}
  pattern="[A-Z]{2}"
/>
```

Complex validation done in submit handlers:
```tsx
const handleSubmit = (e: FormEvent) => {
  e.preventDefault();

  if (!validateStateCode(stateCode)) {
    setError('Invalid state code');
    return;
  }

  // ... submit
};
```

## Performance Optimizations

### RTK Query Caching
- Automatic caching based on tags
- Refetch on window focus (configurable)
- Optimistic updates for mutations

### React.memo
Used sparingly on expensive components:
```tsx
export const ExpensiveList = React.memo(({ items }) => {
  // ... render
});
```

### Lazy Loading
Route-based code splitting (not yet implemented):
```tsx
const ProjectDetailPage = lazy(() => import('./features/projects/pages/ProjectDetailPage'));
```

## Development Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npm run type-check
```

## Common Issues & Solutions

### CORS Errors
- Backend must allow `http://localhost:5173` in CORS config
- Check `api/main.py` CORS middleware

### Modal Not Closing
- Ensure `onClose` is called in modal submit handler
- Check ModalContext state

### Cache Not Updating
- Verify mutation invalidates correct tags
- Use DevTools to inspect RTK Query cache

### TypeScript Errors
- Run `npm run type-check` to see all errors
- Common issue: Missing types for API responses (add to `apiSlice.ts`)
