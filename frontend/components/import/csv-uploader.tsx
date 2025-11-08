'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { toast } from 'sonner'
import { Upload, File, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { importApi } from '@/lib/api/import'

interface CSVUploaderProps {
  onUploadSuccess: (jobId: string) => void
}

export function CSVUploader({ onUploadSuccess }: CSVUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File size must be less than 10MB')
        return
      }

      // Validate file type
      if (!file.name.endsWith('.csv')) {
        toast.error('Only CSV files are allowed')
        return
      }

      setSelectedFile(file)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
    multiple: false,
  })

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    try {
      const job = await importApi.uploadCSV(selectedFile)
      toast.success('CSV uploaded successfully! Processing...')
      onUploadSuccess(job.id)
      setSelectedFile(null)
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Upload failed. Please try again.'
      toast.error(message)
    } finally {
      setIsUploading(false)
    }
  }

  const removeFile = () => {
    setSelectedFile(null)
  }

  return (
    <div className="space-y-4">
      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-lg cursor-pointer transition-colors hover:border-primary/50 bg-card',
            isDragActive && 'border-primary bg-primary/5'
          )}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center py-12 px-4">
            <Upload
              className={cn(
                'h-12 w-12 mb-4 text-muted-foreground',
                isDragActive && 'text-primary'
              )}
            />
            <p className="text-lg font-medium mb-2">
              {isDragActive ? 'Drop your CSV file here' : 'Upload Netflix CSV'}
            </p>
            <p className="text-sm text-muted-foreground text-center">
              Drag and drop your Netflix viewing history CSV file here, or click to browse
            </p>
            <p className="text-xs text-muted-foreground mt-2">Max file size: 10MB</p>
          </div>
        </div>
      ) : (
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <File className="h-8 w-8 text-primary" />
              <div>
                <p className="font-medium">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                onClick={handleUpload}
                disabled={isUploading}
                size="sm"
              >
                {isUploading ? 'Uploading...' : 'Upload'}
              </Button>
              <Button
                onClick={removeFile}
                disabled={isUploading}
                variant="ghost"
                size="icon"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
