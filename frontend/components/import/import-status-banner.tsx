'use client'

import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { importApi } from '@/lib/api/import'
import { Loader2, CheckCircle2, XCircle, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ImportStatusBannerProps {
  jobId: string | null
  onComplete: () => void
  onDismiss: () => void
}

export function ImportStatusBanner({ jobId, onComplete, onDismiss }: ImportStatusBannerProps) {
  const queryClient = useQueryClient()
  const [dismissed, setDismissed] = useState(false)

  // Poll import status
  const { data: job, isLoading } = useQuery({
    queryKey: ['import-status', jobId],
    queryFn: () => importApi.getStatus(jobId!),
    enabled: !!jobId && !dismissed,
    refetchInterval: (query) => {
      // Stop polling if completed or failed
      if (query.state.data?.status === 'completed' || query.state.data?.status === 'failed') {
        return false
      }
      // Poll every 2 seconds while processing
      return 2000
    },
  })

  // Handle completion
  useEffect(() => {
    if (job?.status === 'completed') {
      // Invalidate media queries to trigger refresh
      queryClient.invalidateQueries({ queryKey: ['user-media'] })
      queryClient.invalidateQueries({ queryKey: ['user-media-infinite'] })
      
      // Notify parent
      onComplete()
      
      // Auto-dismiss after 5 seconds
      const timer = setTimeout(() => {
        handleDismiss()
      }, 5000)
      
      return () => clearTimeout(timer)
    }
  }, [job?.status, onComplete, queryClient])

  const handleDismiss = () => {
    setDismissed(true)
    onDismiss()
  }

  if (!jobId || dismissed) return null

  const getStatusColor = () => {
    switch (job?.status) {
      case 'completed':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'failed':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'processing':
      case 'pending':
        return 'bg-blue-50 border-blue-200 text-blue-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const getStatusIcon = () => {
    switch (job?.status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />
      case 'processing':
      case 'pending':
        return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
      default:
        return <Loader2 className="h-5 w-5 animate-spin" />
    }
  }

  const getStatusText = () => {
    if (isLoading) return 'Prüfe Import-Status...'
    
    switch (job?.status) {
      case 'completed':
        return `Import abgeschlossen! ${job.successful_rows} von ${job.total_rows} Einträgen erfolgreich importiert.`
      case 'failed':
        return `Import fehlgeschlagen. ${job.failed_rows} Fehler.`
      case 'processing':
        return `Importiere Medien... ${job.processed_rows} von ${job.total_rows} verarbeitet (${Math.round((job.processed_rows / job.total_rows) * 100)}%)`
      case 'pending':
        return 'Import wird vorbereitet...'
      default:
        return 'Import läuft...'
    }
  }

  return (
    <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 max-w-2xl w-full mx-4 ${getStatusColor()} border rounded-lg shadow-lg p-4 animate-in slide-in-from-top duration-300`}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1">
          {getStatusIcon()}
          <div className="flex-1">
            <p className="font-medium">{getStatusText()}</p>
            {job?.status === 'completed' && (
              <p className="text-sm mt-1">Die Library wurde aktualisiert.</p>
            )}
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleDismiss}
          className="h-6 w-6 rounded-full hover:bg-black/10"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
