'use client'

import { useState } from 'react'
import { CSVUploader } from '@/components/import/csv-uploader'
import { ImportStatus } from '@/components/import/import-status'
import { ImportHistory } from '@/components/import/import-history'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function ImportPage() {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleUploadSuccess = (jobId: string) => {
    setCurrentJobId(jobId)
  }

  const handleImportComplete = () => {
    // Refresh import history
    setRefreshKey((prev) => prev + 1)
    setTimeout(() => {
      setCurrentJobId(null)
    }, 3000) // Show completed status for 3 seconds
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Import Media</h1>
        <p className="text-muted-foreground mt-1">
          Upload your Netflix viewing history CSV file
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Upload CSV File</CardTitle>
              <CardDescription>
                Download your viewing history from Netflix and upload it here
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CSVUploader onUploadSuccess={handleUploadSuccess} />
            </CardContent>
          </Card>

          {currentJobId && (
            <ImportStatus jobId={currentJobId} onComplete={handleImportComplete} />
          )}
        </div>

        <div>
          <ImportHistory key={refreshKey} />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>How to get your Netflix viewing history</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
            <li>Log in to your Netflix account on a web browser</li>
            <li>Go to Account → Profile & Parental Controls</li>
            <li>Click on your profile → Viewing Activity</li>
            <li>Scroll to the bottom and click "Download all"</li>
            <li>Wait for the email with your CSV file</li>
            <li>Upload the CSV file here</li>
          </ol>
        </CardContent>
      </Card>
    </div>
  )
}
