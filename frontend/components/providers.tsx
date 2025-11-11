'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useState } from 'react'
import { ErrorBoundary } from './error-boundary'
import { AuthProvider } from '@/lib/auth-context'
import { ImportProvider, useImport } from '@/lib/import-context'
import { ImportStatusBanner } from './import/import-status-banner'

function ImportBannerWrapper() {
  const { currentJobId, setCurrentJobId } = useImport()
  
  return (
    <ImportStatusBanner
      jobId={currentJobId}
      onComplete={() => {
        // Keep showing banner for 5 seconds after completion
      }}
      onDismiss={() => {
        setCurrentJobId(null)
      }}
    />
  )
}

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
        <AuthProvider>
          <ImportProvider>
            <ImportBannerWrapper />
            {children}
          </ImportProvider>
        </AuthProvider>
        <Toaster 
          position="bottom-left"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
              fontSize: '14px',
              maxWidth: '400px',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#4aed88',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ff6b6b',
                secondary: '#fff',
              },
            },
            loading: {
              duration: Infinity,
            }
          }}
        />
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
