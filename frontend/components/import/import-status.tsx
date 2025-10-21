'use client'

import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { importApi, ImportJob } from '@/lib/api/import'
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ImportStatusProps {
  jobId: string
  onComplete?: () => void
}

export function ImportStatus({ jobId, onComplete }: ImportStatusProps) {
  const [pollingInterval, setPollingInterval] = useState<number | false>(2000)

  const { data: job, isLoading } = useQuery({
    queryKey: ['import-status', jobId],
    queryFn: () => importApi.getStatus(jobId),
    refetchInterval: pollingInterval,
    enabled: !!jobId,
  })

  useEffect(() => {
    if (job && (job.status === 'completed' || job.status === 'failed')) {
      setPollingInterval(false)
      if (job.status === 'completed' && onComplete) {
        onComplete()
      }
    }
  }, [job, onComplete])

  if (isLoading || !job) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  const progress = job.total_rows > 0 ? (job.processed_rows / job.total_rows) * 100 : 0

  const getStatusIcon = () => {
    switch (job.status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-destructive" />
      case 'processing':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />
    }
  }

  const getStatusText = () => {
    switch (job.status) {
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      case 'processing':
        return 'Processing'
      default:
        return 'Pending'
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Import Status</span>
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <span className="text-sm font-normal">{getStatusText()}</span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">
              {job.processed_rows} / {job.total_rows} rows
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-green-600">{job.successful_rows}</p>
            <p className="text-xs text-muted-foreground">Successful</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-destructive">{job.failed_rows}</p>
            <p className="text-xs text-muted-foreground">Failed</p>
          </div>
          <div>
            <p className="text-2xl font-bold">{job.total_rows - job.processed_rows}</p>
            <p className="text-xs text-muted-foreground">Remaining</p>
          </div>
        </div>

        {job.error_log && job.error_log.length > 0 && (
          <div className="mt-4">
            <p className="text-sm font-medium mb-2">Errors:</p>
            <div className="bg-destructive/10 rounded-md p-3 max-h-32 overflow-y-auto">
              {job.error_log.slice(0, 5).map((error, index) => (
                <p key={index} className="text-xs text-destructive">
                  Row {error.row}: {error.error}
                </p>
              ))}
              {job.error_log.length > 5 && (
                <p className="text-xs text-muted-foreground mt-1">
                  ...and {job.error_log.length - 5} more errors
                </p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
