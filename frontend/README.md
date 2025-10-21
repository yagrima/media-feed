# Me Feed Frontend

Modern Next.js 14 frontend for the Me Feed media tracking application.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Custom components with shadcn/ui patterns
- **State Management**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios with automatic token refresh
- **Notifications**: Sonner

## Project Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── (auth)/                # Auth pages group (login, register)
│   │   ├── layout.tsx         # Auth layout (centered)
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/           # Protected dashboard pages
│   │   ├── layout.tsx         # Dashboard layout (with navbar)
│   │   └── dashboard/
│   │       ├── page.tsx       # Library page
│   │       ├── import/        # CSV import page
│   │       └── library/       # Media library page
│   ├── globals.css            # Global styles
│   ├── layout.tsx             # Root layout
│   └── page.tsx               # Root redirect
├── components/
│   ├── auth/                  # Auth components
│   │   └── protected-route.tsx
│   ├── import/                # CSV import components
│   │   ├── csv-uploader.tsx
│   │   ├── import-status.tsx
│   │   └── import-history.tsx
│   ├── library/               # Media library components
│   │   ├── media-grid.tsx
│   │   └── media-filters.tsx
│   ├── layout/                # Layout components
│   │   └── navbar.tsx
│   ├── ui/                    # Reusable UI components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   ├── label.tsx
│   │   ├── badge.tsx
│   │   └── progress.tsx
│   └── providers.tsx          # React Query + Toaster providers
└── lib/
    ├── api/                   # API client
    │   ├── client.ts          # Axios instance with interceptors
    │   ├── auth.ts            # Auth endpoints
    │   ├── import.ts          # Import endpoints
    │   └── media.ts           # Media endpoints
    ├── auth/
    │   └── token-manager.ts   # JWT storage and refresh logic
    └── utils.ts               # Utility functions

```

## Features Implemented

### Authentication
- ✅ Login page with form validation
- ✅ Registration page with password confirmation
- ✅ JWT token management (access + refresh)
- ✅ Automatic token refresh on 401
- ✅ Protected routes with redirect
- ✅ Logout functionality

### CSV Import
- ✅ Drag-and-drop file upload
- ✅ File validation (type, size)
- ✅ Real-time import progress tracking
- ✅ Import status polling (every 2 seconds)
- ✅ Import history with status badges
- ✅ Error display for failed imports

### Media Library
- ✅ Grid view of user's media
- ✅ Media cards with title, type, platform, date
- ✅ Filtering (All / Movies / TV Series)
- ✅ Empty state for new users
- ✅ Responsive design (mobile-friendly)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
npm run build
npm start
```

### Type Checking

```bash
npm run type-check
```

## API Integration

The frontend communicates with the backend via axios with automatic authentication:

### Endpoints Used

**Authentication**:
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

**CSV Import**:
- `POST /api/import/csv` - Upload CSV file
- `GET /api/import/status/{job_id}` - Get import status
- `GET /api/import/history` - Get import history
- `DELETE /api/import/job/{job_id}` - Cancel import

**Media**:
- `GET /api/user/media` - Get user's media library
- `DELETE /api/user/media/{id}` - Delete media

### Authentication Flow

1. User logs in → receives access + refresh tokens
2. Tokens stored in localStorage
3. Axios adds `Authorization: Bearer {token}` to all requests
4. On 401 error → automatically refreshes token and retries request
5. If refresh fails → redirects to /login

## Component Patterns

### Protected Pages

```tsx
// Wrap dashboard pages in protected route
<ProtectedRoute>
  <YourPage />
</ProtectedRoute>
```

### API Calls with React Query

```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ['key'],
  queryFn: () => apiFunction(),
})
```

### Form Validation

```tsx
const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(schema),
})
```

## Styling

- **Tailwind CSS** for utility-first styling
- **CSS Variables** for theme colors (defined in globals.css)
- **Dark mode ready** (class-based dark mode)

### Color Tokens

```css
--background
--foreground
--primary / --primary-foreground
--secondary / --secondary-foreground
--muted / --muted-foreground
--accent / --accent-foreground
--destructive / --destructive-foreground
--border
--input
--ring
```

## Next Steps (Week 4+)

### Planned Features

1. **Sequel Detection UI**
   - Notification center component
   - Sequel cards with metadata
   - Mark as read functionality

2. **Email Notification Preferences**
   - Settings page
   - Toggle email notifications
   - Set frequency (instant/daily/weekly)

3. **Manual Media Management**
   - Add media form with TMDB search
   - Edit/delete media
   - Bulk actions

4. **Enhanced Library**
   - Search functionality
   - Advanced filters (platform, date range)
   - Sort options
   - Pagination
   - Media detail modal

## Developer Notes

### Code Standards

- Use TypeScript strict mode
- Use functional components with hooks
- Use server components where possible (default in App Router)
- Mark client components with `'use client'` directive
- Prefer composition over prop drilling
- Use React Query for server state
- Use form validation with Zod schemas

### Performance

- Images optimized with Next.js `<Image>` component
- Code splitting with dynamic imports
- API responses cached with React Query (1 min stale time)
- Minimal client-side JavaScript (Server Components)

### Security

- No tokens in URL or localStorage (httpOnly would be better for refresh tokens in production)
- Input validation on client and server
- CORS headers properly configured
- No sensitive data logged

## Troubleshooting

### CORS Errors

Ensure backend has frontend URL in `ALLOWED_ORIGINS`:

```env
# backend/.env
ALLOWED_ORIGINS=http://localhost:3000
```

### Token Refresh Loops

Check that refresh token endpoint doesn't require authentication.

### Build Errors

Run type checking to find issues:

```bash
npm run type-check
```

## License

Same as main project
