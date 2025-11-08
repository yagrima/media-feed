'use client'

import { useCallback, useState, useRef, ChangeEvent } from 'react'
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
  const [isDragActive, setIsDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): boolean => {
    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB')
      return false
    }

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      toast.error('Only CSV files are allowed')
      return false
    }

    return true
  }

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file && validateFile(file)) {
      setSelectedFile(file)
    }
  }, [])

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
    multiple: false,
    noClick: true,
    noKeyboard: true,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
    onDropAccepted: () => setIsDragActive(false),
  })

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && validateFile(file)) {
      setSelectedFile(file)
    }
  }

  const handleBrowseClick = () => {
    fileInputRef.current?.click()
  }

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
            'border-2 border-dashed rounded-lg transition-colors bg-card',
            isDragActive && 'border-primary bg-primary/5'
          )}
        >
          <input {...getInputProps()} style={{ display: 'none' }} />
          {/* Separate file input for button click - NOT controlled by dropzone */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
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
            <p className="text-sm text-muted-foreground text-center mb-4">
              Drag and drop your Netflix viewing history CSV file here
            </p>
            <Button onClick={handleBrowseClick} variant="outline" type="button">
              Datei auswählen
            </Button>
            <p className="text-xs text-muted-foreground mt-4">Max file size: 10MB</p>
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
