'use client'

import React, { createContext, useContext, useState, ReactNode } from 'react'

interface ImportContextType {
  currentJobId: string | null
  setCurrentJobId: (jobId: string | null) => void
}

const ImportContext = createContext<ImportContextType | undefined>(undefined)

export function ImportProvider({ children }: { children: ReactNode }) {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)

  return (
    <ImportContext.Provider value={{ currentJobId, setCurrentJobId }}>
      {children}
    </ImportContext.Provider>
  )
}

export function useImport() {
  const context = useContext(ImportContext)
  if (context === undefined) {
    throw new Error('useImport must be used within an ImportProvider')
  }
  return context
}
