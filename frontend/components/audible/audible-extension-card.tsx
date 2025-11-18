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
import { Loader2, Puzzle, BookOpen, CheckCircle2, Clock, AlertCircle, Download, ExternalLink } from 'lucide-react'
import { audibleApi, AudibleApiError, type AudibleStatusResponse } from '@/lib/audible-api'
import { formatDistanceToNow } from 'date-fns'

export function AudibleExtensionCard() {
  const [status, setStatus] = useState<AudibleStatusResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDisconnecting, setIsDisconnecting] = useState(false)
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
              <Puzzle className="h-5 w-5 text-muted-foreground" />
              <div>
                <CardTitle>Audible Sync (Browser Extension)</CardTitle>
                <CardDescription>
                  {status?.connected
                    ? 'Synced via browser extension'
                    : 'Install the extension to sync your Audible library'}
                </CardDescription>
              </div>
            </div>
            {status?.connected ? (
              <Badge variant="default" className="gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Connected
              </Badge>
            ) : (
              <Badge variant="secondary">Not Setup</Badge>
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

          {status?.connected ? (
            <>
              {/* Connection Details */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Marketplace</p>
                  <p className="text-sm">
                    {status.marketplace?.toUpperCase() || 'Detected by Extension'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Sync Method</p>
                  <p className="text-sm">Browser Extension</p>
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

              <div className="bg-muted/50 rounded-md p-3 text-sm text-muted-foreground flex items-start gap-2">
                <BookOpen className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>
                  To update your library, simply visit your Audible Library page in your browser. The extension will auto-sync changes.
                </span>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-2 justify-end">
                <Button
                  onClick={() => setShowDisconnectDialog(true)}
                  disabled={isDisconnecting}
                  variant="outline"
                  size="sm"
                  className="text-destructive hover:text-destructive"
                >
                  Reset Connection
                </Button>
              </div>
            </>
          ) : (
            <>
              {/* Not Connected State */}
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-900 flex items-center gap-2 mb-2">
                    <Download className="h-4 w-4" />
                    How to setup
                  </h4>
                  <ol className="list-decimal list-inside space-y-2 text-sm text-blue-800">
                    <li>Download/Load the <strong>Me Feed Extension</strong> in your browser.</li>
                    <li>The extension will automatically detect your login token.</li>
                    <li>Visit <strong>audible.com/library</strong> (or your region).</li>
                    <li>The extension will automatically scrape and import your books!</li>
                  </ol>
                </div>

                <div className="flex justify-center gap-4">
                  <Button variant="outline" className="gap-2" asChild>
                    <a href="/extension-guide" target="_blank">
                      <BookOpen className="h-4 w-4" />
                      View Installation Guide
                    </a>
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Disconnect Confirmation Dialog */}
      <AlertDialog open={showDisconnectDialog} onOpenChange={setShowDisconnectDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reset Connection?</AlertDialogTitle>
            <AlertDialogDescription>
              This will clear the connection status from Me Feed.
              <br/><br/>
              To fully disconnect, you should also <strong>remove the extension</strong> from your browser.
              <br/><br/>
              Your imported audiobooks will <strong>not</strong> be deleted.
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
              {isDisconnecting ? 'Resetting...' : 'Reset'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
