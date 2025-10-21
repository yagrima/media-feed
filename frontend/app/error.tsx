'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('App error:', error)
  }, [error])

  return (
    <div className="flex items-center justify-center min-h-screen p-4 bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-red-600">Application Error</CardTitle>
          <CardDescription>
            Something went wrong while loading the page.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm font-mono text-red-800">
              {error.message || 'An unexpected error occurred'}
            </p>
            {error.digest && (
              <p className="text-xs text-red-600 mt-2">
                Error ID: {error.digest}
              </p>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button onClick={reset} variant="default">
            Try Again
          </Button>
          <Button
            onClick={() => window.location.href = '/dashboard'}
            variant="outline"
          >
            Go to Dashboard
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
