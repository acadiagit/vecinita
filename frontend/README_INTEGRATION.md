# Vecinita Frontend

Modern TypeScript + React + Vite 6 + Tailwind CSS v4 frontend for the Vecinita environmental Q&A assistant.

## Quick Start

### Prerequisites
- Node.js 18+ ([download](https://nodejs.org/))
- npm or yarn package manager

### Local Development

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Create environment file**
   ```bash
   cp .env.local.example .env.local
   ```

3. **Start backend** (in another terminal)
   ```bash
   # From root vecinita directory
   docker-compose up vecinita-agent embedding-service
   ```

4. **Start dev server**
   ```bash
   npm run dev
   ```
   
   Open http://localhost:5173 (Vite default) or the URL shown in terminal.

### Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

## Architecture

### Component Structure
```
src/
├── api/
│   └── client.ts          # Backend API integration
├── app/
│   ├── App.tsx            # Main chat interface
│   ├── components/        # UI components
│   │   ├── ChatMessage.tsx
│   │   ├── SourceCard.tsx
│   │   ├── ThemeToggle.tsx
│   │   ├── LanguageSelector.tsx
│   │   └── AccessibilityPanel.tsx
│   ├── context/           # React Context providers
│   │   ├── LanguageContext.tsx
│   │   └── AccessibilityContext.tsx
│   └── components/ui/     # Radix UI component library (50+ components)
├── main.tsx               # Entry point
└── styles/                # CSS and Tailwind configuration
```

### Key Technologies

| Tech | Purpose | Version |
|------|---------|---------|
| React | UI framework | 18.3 |
| TypeScript | Type safety | Latest |
| Vite | Build tool | 6.3 |
| Tailwind CSS | Styling | 4.1 |
| Radix UI | Component primitives | Latest |
| Material UI | Icons & components | 7.3 |

## Backend Integration

### API Endpoints

The frontend communicates with the Vecinita backend at `http://localhost:8000` (configurable via `VITE_BACKEND_URL`).

#### `GET /config`
Fetch available LLM providers and models.

**Response:**
```json
{
  "providers": [
    {
      "id": "groq",
      "name": "Groq",
      "description": "Fast LLM provider"
    }
  ],
  "models": [
    {
      "id": "llama3.1-8b",
      "provider": "groq",
      "name": "Llama 3.1 8B",
      "description": "Fast, capable open model"
    }
  ]
}
```

#### `GET /ask-stream`
Stream a question to the backend using Server-Sent Events (SSE).

**Query Parameters:**
- `query` (string): User's question
- `lang` (string): Language code ('en', 'es', etc.)
- `provider` (string): LLM provider ID
- `model` (string): Model ID
- `thread_id` (string, optional): Conversation thread ID

**Response (SSE):**
```
data: {"type": "thinking", "data": "Analyzing question..."}
data: {"type": "complete", "data": "{\"answer\": \"...\", \"sources\": [...]}"}
data: {"type": "error", "data": "Error message"}
```

### Environment Variables

Create `.env.local` with:
```env
# Backend URL (local dev)
VITE_BACKEND_URL=http://localhost:8000

# Enable debug logging
VITE_DEBUG=false
```

**Important:** Build-time environment variables are injected during `npm run build`. Runtime changes require a rebuild.

## Development Workflow

### Add a New Component

1. Create component in `src/app/components/MyComponent.tsx`
2. Use Tailwind classes for styling
3. Import and use in `App.tsx`

Example:
```typescript
// src/app/components/MyComponent.tsx
export function MyComponent({ prop }: { prop: string }) {
  return <div className="p-4 rounded-lg bg-card">{prop}</div>;
}
```

### Add UI Components from Radix UI

The project includes 50+ Radix UI components in `src/app/components/ui/`. Import and use directly:

```typescript
import { Button } from '@/components/ui/button';

<Button onClick={handleClick}>Click me</Button>
```

### Styling with Tailwind v4

Tailwind v4 uses CSS variables for theming:

```css
/* src/styles/index.css */
@import "tailwindcss";

@theme {
  --color-primary: #007bff;
  --color-success: #28a745;
}
```

Dark mode is automatically handled via the `dark` class on `document.documentElement`:

```typescript
// Light mode
document.documentElement.classList.remove('dark');

// Dark mode
document.documentElement.classList.add('dark');
```

## Testing

### Prerequisites
```bash
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
npm install --save-dev @playwright/test
```

### Run Tests

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

### Example Unit Test

```typescript
// src/app/components/__tests__/ChatMessage.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChatMessage } from '../ChatMessage';

describe('ChatMessage', () => {
  it('renders user message', () => {
    const message = {
      id: '1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date(),
    };
    render(<ChatMessage message={message} />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

## Docker Deployment

### Build Docker Image

```bash
# From root directory
docker build -f frontend/Dockerfile -t vecinita-frontend:latest \
  --build-arg VITE_BACKEND_URL=http://vecinita-agent:8000 \
  frontend/
```

### Run with Docker Compose

```bash
docker-compose up frontend
```

The frontend will be available at `http://localhost:3000`.

## Accessibility

The frontend includes built-in accessibility features:

- ✅ ARIA labels and roles
- ✅ Semantic HTML
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Screen reader support
- ✅ High contrast mode
- ✅ Font scaling options
- ✅ Adjustable colors and contrast

Access these via the Settings button (⚙️) in the header.

## Performance Optimization

### Bundle Size

Current bundle size: ~200KB (gzipped ~60KB)

To optimize:

```bash
# Analyze bundle
npm run build -- --analyze

# Tree-shake unused dependencies
npm prune --production
```

### Code Splitting

Vite automatically code-splits at route boundaries. For manual splitting:

```typescript
import { lazy, Suspense } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HeavyComponent />
    </Suspense>
  );
}
```

## Troubleshooting

### Backend Connection Error

**Symptom:** "Backend connection error. Check that it's running at..."

**Fix:**
1. Ensure backend is running: `docker-compose up vecinita-agent`
2. Check `VITE_BACKEND_URL` in `.env.local`
3. Verify backend is accessible: `curl http://localhost:8000/health`

### TypeScript Errors

**Symptom:** "Type is not assignable to..."

**Fix:**
```bash
# Regenerate type definitions
npm run build
# or
npm run tsc -- --noEmit
```

### Slow Dev Server

**Fix:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Restart dev server
npm run dev
```

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit: `git commit -m "feat: add feature"`
3. Push to GitHub: `git push origin feature/my-feature`
4. Create a Pull Request

### Code Style

- Use TypeScript for all new code
- Follow existing component patterns
- Run `npm run lint` before committing (if configured)
- Add accessibility attributes (aria-label, aria-hidden, etc.)

## License

Part of the Vecinita project. See root LICENSE file.

## Support

- 📧 Email: [support contact]
- 🐛 Issues: [GitHub Issues link]
- 💬 Discussions: [GitHub Discussions link]

---

**Last Updated:** January 2026  
**Vecinita Version:** Next Gen (TypeScript/Vite 6/Tailwind v4)
