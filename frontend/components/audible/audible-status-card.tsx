'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Loader2, RefreshCw, Unplug, BookOpen, CheckCircle2, Clock, AlertCircle } from 'lucide-react'
import { audibleApi, AudibleApiError, type AudibleStatusResponse } from '@/lib/audible-api'
import { formatDistanceToNow } from 'date-fns'

interface AudibleStatusCardProps {
  onConnect: () => void
}

export function AudibleStatusCard({ onConnect }: AudibleStatusCardProps) {
  const [status, setStatus] = useState<AudibleStatusResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSyncing, setIsSyncing] = useState(false)
  const [isDisconnecting, setIsDisconnecting] = useState(false)
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [syncMessage, setSyncMessage] = useState<string | null>(null)

  const fetchStatus = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const statusData = await audibleApi.getStatus()
      setStatus(statusData)
    } catch (err) {
      if (err instanceof AudibleApiError) {
        setError(err.message)
      } else {
        setError('Failed to load Audible status')
      }
      console.error('Error fetching Audible status:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  const handleSync = async () => {
    setIsSyncing(true)
    setError(null)
    setSyncMessage(null)

    try {
      const result = await audibleApi.sync()
      
      setSyncMessage(
        `Synced successfully! Imported: ${result.imported}, Updated: ${result.updated}, Total: ${result.total}`
      )
      
      // Refresh status to get updated last_sync_at
      await fetchStatus()
    } catch (err) {
      if (err instanceof AudibleApiError) {
        setError(err.message)
        
        // If token expired, suggest reconnection
        if (err.errorType === 'token_expired') {
          setError('Authentication expired. Please disconnect and reconnect your account.')
        }
      } else {
        setError('Sync failed. Please try again.')
      }
      console.error('Sync error:', err)
    } finally {
      setIsSyncing(false)
    }
  }

  const handleDisconnect = async () => {
    setIsDisconnecting(true)
    setError(null)

    try {
      await audibleApi.disconnect()
      
      // Refresh status to show disconnected state
      await fetchStatus()
      setShowDisconnectDialog(false)
    } catch (err) {
      if (err instanceof AudibleApiError) {
        setError(err.message)
      } else {
        setError('Disconnect failed. Please try again.')
      }
      console.error('Disconnect error:', err)
    } finally {
      setIsDisconnecting(false)
    }
  }

  const formatLastSync = (lastSyncAt: string | null) => {
    if (!lastSyncAt) return 'Never'
    
    try {
      return formatDistanceToNow(new Date(lastSyncAt), { addSuffix: true })
    } catch {
      return 'Unknown'
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BookOpen className="h-5 w-5 text-muted-foreground" />
              <div>
                <CardTitle>Audible Connection</CardTitle>
                <CardDescription>
                  {status?.connected
                    ? 'Your Audible account is connected'
                    : 'Connect your Audible account to import audiobooks'}
                </CardDescription>
              </div>
            </div>
            {status?.connected ? (
              <Badge variant="default" className="gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Connected
              </Badge>
            ) : (
              <Badge variant="secondary">Not Connected</Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Sync Success Message */}
          {syncMessage && (
            <Alert className="border-green-500 bg-green-50">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">{syncMessage}</AlertDescription>
            </Alert>
          )}

          {status?.connected ? (
            <>
              {/* Connection Details */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Marketplace</p>
                  <p className="text-sm">
                    {status.marketplace?.toUpperCase() || 'Unknown'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Device</p>
                  <p className="text-sm truncate" title={status.device_name || undefined}>
                    {status.device_name || 'Me Feed - Web'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Last Synced
                  </p>
                  <p className="text-sm">{formatLastSync(status.last_sync_at)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Audiobooks</p>
                  <p className="text-sm">
                    {status.books_count !== null ? status.books_count : '—'}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-2">
                <Button
                  onClick={handleSync}
                  disabled={isSyncing}
                  variant="default"
                  className="flex-1"
                >
                  {isSyncing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Syncing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Sync Now
                    </>
                  )}
                </Button>
                <Button
                  onClick={() => setShowDisconnectDialog(true)}
                  disabled={isSyncing || isDisconnecting}
                  variant="outline"
                >
                  <Unplug className="mr-2 h-4 w-4" />
                  Disconnect
                </Button>
              </div>

              <p className="text-xs text-muted-foreground">
                Syncing imports new purchases and updates metadata. 
                Disconnecting removes stored credentials but keeps your audiobooks.
              </p>
            </>
          ) : (
            <>
              {/* Not Connected State */}
              <div className="text-center py-6">
                <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground mb-4">
                  Connect your Audible account to automatically import your audiobook library
                </p>
                <Button onClick={onConnect}>Connect Audible Account</Button>
              </div>

              <div className="bg-muted rounded-md p-3 text-sm text-muted-foreground">
                <ul className="list-disc list-inside space-y-1">
                  <li>One-click import of your entire library</li>
                  <li>Secure credential storage (encrypted)</li>
                  <li>Sync new purchases automatically</li>
                  <li>Rich metadata (authors, narrators, duration)</li>
                </ul>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Disconnect Confirmation Dialog */}
      <AlertDialog open={showDisconnectDialog} onOpenChange={setShowDisconnectDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disconnect Audible Account?</AlertDialogTitle>
            <AlertDialogDescription>
              This will:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Remove the virtual device from your Amazon account</li>
                <li>Delete stored authentication credentials</li>
                <li><strong>Keep</strong> all imported audiobooks in your library</li>
              </ul>
              <p className="mt-3">You can reconnect at any time to sync updates.</p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDisconnecting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDisconnect}
              disabled={isDisconnecting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDisconnecting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
