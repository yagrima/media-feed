'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, AlertCircle, CheckCircle2, BookOpen } from 'lucide-react'
import { audibleApi, AudibleApiError, type AudibleConnectResponse } from '@/lib/audible-api'

interface ConnectAudibleModalProps {
  open: boolean
  onClose: () => void
  onSuccess: (data: AudibleConnectResponse) => void
}

const MARKETPLACES = [
  { value: 'us', label: 'United States' },
  { value: 'uk', label: 'United Kingdom' },
  { value: 'de', label: 'Germany' },
  { value: 'fr', label: 'France' },
  { value: 'ca', label: 'Canada' },
  { value: 'au', label: 'Australia' },
  { value: 'in', label: 'India' },
  { value: 'it', label: 'Italy' },
  { value: 'jp', label: 'Japan' },
  { value: 'es', label: 'Spain' },
]

export function ConnectAudibleModal({ open, onClose, onSuccess }: ConnectAudibleModalProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [marketplace, setMarketplace] = useState('us')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorType, setErrorType] = useState<string | null>(null)
  const [success, setSuccess] = useState<AudibleConnectResponse | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setErrorType(null)
    setSuccess(null)

    try {
      const result = await audibleApi.connect({
        email,
        password,
        marketplace
      })

      setSuccess(result)
      
      // Call onSuccess after short delay to show success message
      setTimeout(() => {
        onSuccess(result)
        handleClose()
      }, 2000)

    } catch (err) {
      if (err instanceof AudibleApiError) {
        setError(err.message)
        setErrorType(err.errorType || null)
        
        // Log detailed error for debugging
        console.error('Audible connection error:', {
          message: err.message,
          statusCode: err.statusCode,
          errorType: err.errorType,
          detail: err.detail
        })
      } else {
        setError('An unexpected error occurred. Please try again.')
        console.error('Unexpected error:', err)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    if (!isLoading) {
      setEmail('')
      setPassword('')
      setMarketplace('us')
      setError(null)
      setErrorType(null)
      setSuccess(null)
      onClose()
    }
  }

  const getErrorHelperText = () => {
    if (!errorType) return null

    switch (errorType) {
      case 'captcha_required':
        return 'Audible has detected unusual activity. Please try again in 30-60 minutes, or use manual import as an alternative.'
      
      case '2fa_required':
        return 'Append your 2FA code to your password. For example, if your password is "MyPass123" and your 2FA code is "456789", enter "MyPass123456789".'
      
      case 'auth_failed':
        return 'Double-check your email and password. Make sure you\'re using your Amazon/Audible credentials.'
      
      case 'token_expired':
        return 'Your session has expired. Please disconnect and reconnect your account.'
      
      default:
        return null
    }
  }

  const helperText = getErrorHelperText()

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Connect Audible Account
          </DialogTitle>
          <DialogDescription>
            Enter your Audible credentials to import your audiobook library.
            Your password is never stored—only an encrypted token.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Success Message */}
          {success && (
            <Alert className="border-green-500 bg-green-50">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                <strong>Success!</strong> Imported {success.books_imported} audiobooks from Audible.
                Redirecting...
              </AlertDescription>
            </Alert>
          )}

          {/* Error Message */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>Error:</strong> {error}
                {helperText && (
                  <div className="mt-2 text-sm">
                    <strong>Tip:</strong> {helperText}
                  </div>
                )}
              </AlertDescription>
            </Alert>
          )}

          {/* Email Input */}
          <div className="space-y-2">
            <Label htmlFor="email">Audible Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading || !!success}
              autoComplete="off"
              data-form-type="other"
            />
          </div>

          {/* Password Input */}
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your Audible password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading || !!success}
              autoComplete="off"
              data-form-type="other"
            />
            <p className="text-xs text-muted-foreground">
              If you have 2FA enabled, append your 2FA code to your password
            </p>
          </div>

          {/* Marketplace Selector */}
          <div className="space-y-2">
            <Label htmlFor="marketplace">Audible Marketplace</Label>
            <Select
              value={marketplace}
              onValueChange={setMarketplace}
              disabled={isLoading || !!success}
            >
              <SelectTrigger id="marketplace">
                <SelectValue placeholder="Select marketplace" />
              </SelectTrigger>
              <SelectContent>
                {MARKETPLACES.map((mkt) => (
                  <SelectItem key={mkt.value} value={mkt.value}>
                    {mkt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Select the Audible store where you have your account
            </p>
          </div>

          {/* Authorization Notice */}
          <div className="rounded-md bg-muted p-3 text-sm">
            <p className="text-muted-foreground">
              By connecting, you authorize Me Feed to access your Audible library.
              This will register a virtual device (visible in your Amazon device list).
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isLoading || !!success}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !!success}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isLoading ? 'Connecting...' : success ? 'Connected!' : 'Connect & Import'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
