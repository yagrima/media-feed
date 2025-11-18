'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { Upload, ArrowLeft, FileText, CheckCircle2 } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { useImport } from '@/lib/import-context'
import { useRouter } from 'next/navigation'
import { AudibleExtensionCard } from '@/components/audible/audible-extension-card'
import { useToast } from '@/hooks/use-toast'

export default function ImportPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { setCurrentJobId } = useImport()
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string; jobId?: string } | null>(null)
  const dropZoneRef = useRef<HTMLDivElement>(null)
  const dragCounterRef = useRef(0)
  // const [showAudibleModal, setShowAudibleModal] = useState(false)  // REMOVED: Backend auth failed

  // File upload handler
  const handleFileUpload = useCallback(async (file: File) => {
    console.log('=== STARTING FILE UPLOAD ===')
    console.log('File:', file.name, file.size, file.type)
    
    setIsUploading(true)
    setUploadProgress(0)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      console.log('Form data created')

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 5, 90))
      }, 500)

      // Get auth token
      const token = localStorage.getItem('access_token')
      console.log('Auth token found:', !!token)
      const headers: Record<string, string> = {}
      if (token) {
        headers.Authorization = `Bearer ${token}`
      }

      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/import/csv`
      console.log('Uploading to:', apiUrl)
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers,
        body: formData,
      })

      clearInterval(progressInterval)
      setUploadProgress(100)
      console.log('Response received:', response.status, response.statusText)

      if (response.ok) {
        const result = await response.json()
        console.log('Upload successful:', result)
        
        // Set job ID for global status tracking
        if (result.id) {
          setCurrentJobId(result.id)
        }
        
        setUploadResult({ 
          success: true, 
          message: `CSV wird verarbeitet...`,
          jobId: result.id
        })
        
        // Redirect to library after 2 seconds
        setTimeout(() => {
          router.push('/library')
        }, 2000)
      } else {
        const error = await response.json()
        console.error('Upload failed:', response.status, error)
        setUploadResult({ 
          success: false, 
          message: error.detail || `Upload fehlgeschlagen (${response.status}). Bitte versuche es erneut.` 
        })
      }
    } catch (error) {
      console.error('Network error:', error)
      setUploadResult({ 
        success: false, 
        message: `Netzwerkfehler: ${error instanceof Error ? error.message : 'Unbekannter Fehler'}` 
      })
    } finally {
      setIsUploading(false)
      console.log('=== FILE UPLOAD ENDED ===')
    }
  }, [])

  // Process drag and drop files
  const processDrop = useCallback((dataTransfer: DataTransfer | null) => {
    if (!dataTransfer) {
      console.log('❌ No dataTransfer available')
      return
    }

    console.log('=== PROCESSING DROP ===')
    console.log('DataTransfer files:', dataTransfer.files)
    console.log('DataTransfer items:', dataTransfer.items)
    
    // Handle both files and items (for better cross-browser support)
    let files: File[] = []
    
    // Try to get files from dataTransfer.files first
    if (dataTransfer.files && dataTransfer.files.length > 0) {
      files = Array.from(dataTransfer.files)
      console.log('Files from dataTransfer.files:', files)
    }
    // Fallback to dataTransfer.items
    else if (dataTransfer.items && dataTransfer.items.length > 0) {
      for (let i = 0; i < dataTransfer.items.length; i++) {
        const item = dataTransfer.items[i]
        if (item.kind === 'file') {
          const file = item.getAsFile()
          if (file) {
            files.push(file)
          }
        }
      }
      console.log('Files from dataTransfer.items:', files)
    }
    
    console.log('Final files array:', files)
    
    const csvFile = files.find(file => 
      file.type === 'text/csv' || 
      file.type === 'application/vnd.ms-excel' ||
      file.name.endsWith('.csv') ||
      file.name.toLowerCase().endsWith('.csv')
    )
    console.log('CSV file found:', csvFile, csvFile ? csvFile.name : 'none')
    
    if (csvFile) {
      console.log('✅ STARTING UPLOAD:', csvFile.name)
      setUploadedFile(csvFile)
      handleFileUpload(csvFile)
    } else {
      console.log('❌ No CSV file found in dropped files')
      const message = files.length > 0 
        ? `Keine CSV-Datei gefunden. Gefunden: ${files.map(f => f.name).join(', ')}`
        : 'Bitte lade eine CSV-Datei hoch'
      
      setUploadResult({ success: false, message })
      setTimeout(() => {
        setUploadResult(null)
      }, 5000)
    }
  }, [handleFileUpload])

  // Global drag event listeners - IMMEDIATELY active on mount
  useEffect(() => {
    console.log('🚀 MOUNTING - Setting up drag listeners IMMEDIATELY')

    const handleGlobalDragEnter = (e: DragEvent) => {
      console.log('⭐ Global drag enter')
      e.preventDefault()
      e.stopPropagation()
      dragCounterRef.current++
      console.log('Drag counter:', dragCounterRef.current)
      
      // Check if files are being dragged
      if (e.dataTransfer?.types?.includes('Files')) {
        console.log('✅ Files detected')
        setIsDragging(true)
      }
    }

    const handleGlobalDragLeave = (e: DragEvent) => {
      console.log('⭐ Global drag leave')
      e.preventDefault()
      e.stopPropagation()
      dragCounterRef.current--
      console.log('Drag counter:', dragCounterRef.current)
      
      if (dragCounterRef.current === 0) {
        console.log('❌ Counter = 0, removing drag state')
        setIsDragging(false)
      }
    }

    const handleGlobalDragOver = (e: DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (e.dataTransfer) {
        e.dataTransfer.dropEffect = 'copy'
      }
    }

    const handleGlobalDrop = (e: DragEvent) => {
      console.log('🎯 Global drop event!')
      e.preventDefault()
      e.stopPropagation()
      dragCounterRef.current = 0
      setIsDragging(false)
      
      // Process the drop
      processDrop(e.dataTransfer)
    }

    // Add listeners IMMEDIATELY
    console.log('Adding event listeners to document...')
    document.addEventListener('dragenter', handleGlobalDragEnter)
    document.addEventListener('dragover', handleGlobalDragOver)
    document.addEventListener('dragleave', handleGlobalDragLeave)
    document.addEventListener('drop', handleGlobalDrop)
    console.log('✅ Event listeners added!')

    return () => {
      console.log('🧹 Cleaning up drag listeners')
      document.removeEventListener('dragenter', handleGlobalDragEnter)
      document.removeEventListener('dragover', handleGlobalDragOver)
      document.removeEventListener('dragleave', handleGlobalDragLeave)
      document.removeEventListener('drop', handleGlobalDrop)
    }
  }, [processDrop])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('File select event', e.target.files)
    const file = e.target.files?.[0]
    if (file) {
      console.log('File selected via click:', file.name)
      setUploadedFile(file)
      handleFileUpload(file)
    } else {
      console.log('No file selected')
    }
  }, [handleFileUpload])

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-4">
        <Link href="/library">
          <Button variant="outline" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Zurück zur Library
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Medien importieren</h1>
          <p className="text-muted-foreground mt-1">
            Lade deine Netflix Verlaufs-CSV-Datei hoch
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>CSV-Datei hochladen</CardTitle>
          <CardDescription>
            Wähle deine Netflix Verlaufs-CSV-Datei aus, um deine Mediathek zu importieren
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          {uploadedFile && !isUploading && uploadResult?.success ? (
            // Success State
            <div className="flex flex-col items-center text-center">
              <CheckCircle2 className="h-16 w-16 text-green-500 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{uploadedFile.name}</h3>
              <p className="text-green-600 mb-6 text-lg">{uploadResult.message}</p>
              <div className="flex gap-4">
                <Link href="/library">
                  <Button>Mediathek ansehen</Button>
                </Link>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setUploadedFile(null)
                    setUploadResult(null)
                    setUploadProgress(0)
                  }}
                >
                  Weitere Datei hochladen
                </Button>
              </div>
            </div>
          ) : isUploading ? (
            // Upload State
            <div className="flex flex-col items-center text-center w-full max-w-sm">
              <Upload className="h-12 w-12 text-primary animate-pulse mb-4" />
              <h3 className="text-lg font-semibold mb-2">Lade {uploadedFile?.name} hoch...</h3>
              <p className="text-muted-foreground mb-4">Verarbeite deine CSV-Datei...</p>
              <Progress value={uploadProgress} className="w-full mb-2" />
              <p className="text-sm text-muted-foreground">{uploadProgress}%</p>
            </div>
          ) : (
            // Upload Area
            <div
              ref={dropZoneRef}
              className={`relative flex flex-col items-center justify-center w-full py-12 px-6 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
                isDragging ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-gray-300 hover:border-primary'
              }`}
              onClick={() => {
                console.log('Upload area clicked')
                document.getElementById('file-upload')?.click()
              }}
              style={{ minHeight: '300px' }}
            >
              <input
                type="file"
                id="file-upload"
                accept=".csv"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              <Upload className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {isDragging ? 'Datei hier loslassen' : 'CSV-Datei hier ablegen oder klicken'}
              </h3>
              <p className="text-muted-foreground text-center mb-6 max-w-md">
                Lade deine Netflix Verlaufs-CSV-Datei hoch (Max. 10MB)
              </p>
              <Button 
                type="button" 
                onClick={(e) => {
                  e.stopPropagation()
                  document.getElementById('file-upload')?.click()
                }}
              >
                Datei auswählen
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Message */}
      {uploadResult && !uploadResult.success && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="text-red-600 text-sm font-medium">{uploadResult.message}</div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setUploadResult(null)}
            >
              Erneut versuchen
            </Button>
          </div>
        </div>
      )}

      {/* File Info */}
      {uploadedFile && !isUploading && !uploadResult?.success && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-blue-600" />
              <div>
                <div className="font-medium text-blue-900">{uploadedFile.name}</div>
                <div className="text-sm text-blue-600">
                  {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                </div>
              </div>
            </div>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => setUploadedFile(null)}
            >
              Entfernen
            </Button>
          </div>
        </div>
      )}



      {/* Audible Import Section */}
      <AudibleExtensionCard />
    </div>
  )
}
