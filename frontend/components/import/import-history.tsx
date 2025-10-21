'use client'

import { useQuery } from '@tanstack/react-query'
import { importApi, ImportHistoryItem } from '@/lib/api/import'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

export function ImportHistory() {
  const { data, isLoading } = useQuery({
    queryKey: ['import-history'],
    queryFn: () => importApi.getHistory(1, 10),
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <Badge variant="default" className="bg-green-500">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Completed
          </Badge>
        )
      case 'failed':
        return (
          <Badge variant="destructive">
            <XCircle className="h-3 w-3 mr-1" />
            Failed
          </Badge>
        )
      case 'processing':
        return (
          <Badge variant="default" className="bg-blue-500">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            Processing
          </Badge>
        )
      default:
        return (
          <Badge variant="secondary">
            <Clock className="h-3 w-3 mr-1" />
            Pending
          </Badge>
        )
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (!data || !data.imports || data.imports.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Import History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-muted-foreground py-8">
            No import history yet. Upload your first CSV to get started!
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Import History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {data.imports.map((job: ImportHistoryItem) => (
            <div
              key={job.job_id}
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent/50 transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <div>
                    <p className="font-medium">{job.source}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(job.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm font-medium">
                    {job.successful_rows} / {job.total_rows}
                  </p>
                  <p className="text-xs text-muted-foreground">rows imported</p>
                </div>
                {getStatusBadge(job.status)}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
