'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { MediaGrid } from '@/components/library/media-grid'
import Link from 'next/link'
import { Upload } from 'lucide-react'

export default function LibraryPage() {
  const searchParams = useSearchParams()
  const typeParam = searchParams.get('type') as 'movie' | 'tv_series' | null
  const [filter, setFilter] = useState<'all' | 'movie' | 'tv_series'>('all')
  
  // Set filter from URL parameter on mount
  useEffect(() => {
    if (typeParam === 'movie' || typeParam === 'tv_series') {
      setFilter(typeParam)
    }
  }, [typeParam])
  // true = endless, false = pagination
  const [isEndlessScrolling, setIsEndlessScrolling] = useState(true)
  const viewMode = isEndlessScrolling ? 'infinite' : 'pagination'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Meine Library</h1>
          <p className="text-muted-foreground mt-1">
            Deine gesammelten Medien aus deinen Importen
          </p>
        </div>
        <Link href="/import">
          <Button>
            <Upload className="mr-2 h-4 w-4" />
            CSV importieren
          </Button>
        </Link>
      </div>

      {/* Filter and View Mode Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Type Filters */}
        <div className="flex gap-2">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            onClick={() => setFilter('all')}
          >
            Alle
          </Button>
          <Button
            variant={filter === 'movie' ? 'default' : 'outline'}
            onClick={() => setFilter('movie')}
          >
            Filme
          </Button>
          <Button
            variant={filter === 'tv_series' ? 'default' : 'outline'}
            onClick={() => setFilter('tv_series')}
          >
            Serien
          </Button>
        </div>

        {/* View Mode Toggle Switch */}
        <div className="flex items-center gap-3">
          <Label 
            htmlFor="view-mode" 
            className="text-sm font-medium cursor-pointer"
          >
            Pagination
          </Label>
          <Switch
            id="view-mode"
            checked={isEndlessScrolling}
            onCheckedChange={setIsEndlessScrolling}
            aria-label="Toggle view mode"
          />
          <Label 
            htmlFor="view-mode" 
            className="text-sm font-medium cursor-pointer"
          >
            Endless Scrolling
          </Label>
        </div>
      </div>

      {/* Media Grid */}
      <MediaGrid filters={{ type: filter }} viewMode={viewMode} />
    </div>
  )
}
