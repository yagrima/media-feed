import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

export default function NotFound() {
  return (
    <div className="flex items-center justify-center min-h-screen p-4 bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-4xl font-bold">404</CardTitle>
          <CardDescription className="text-lg">
            Page Not Found
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button asChild variant="default">
            <Link href="/dashboard">Go to Dashboard</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/login">Go to Login</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
