'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
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
        <Toaster 
        position="top-center"
        toastOptions={{
          duration: 30000,
          style: {
            background: '#363636',
            color: '#fff',
            fontSize: '16px',
            maxWidth: '500px',
          },
          success: {
            duration: 5000,
            iconTheme: {
              primary: '#4aed88',
              secondary: '#fff',
            },
          },
          error: {
            duration: 30000,
            iconTheme: {
              primary: '#ff6b6b',
              secondary: '#fff',
            },
          }
        }}
      />
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
