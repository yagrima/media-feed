'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { useState } from 'react'
import { ErrorBoundary } from './error-boundary'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            retry: 1,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: 0,
          },
        },
      })
  )

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster position="top-right" richColors expand={true} />
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
