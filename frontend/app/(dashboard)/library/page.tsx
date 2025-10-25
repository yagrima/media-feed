'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { MediaGrid } from '@/components/library/media-grid'
import Link from 'next/link'
import { Upload } from 'lucide-react'

export default function LibraryPage() {
  const [filter, setFilter] = useState<'all' | 'movie' | 'tv_series'>('all')

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

      {/* Filter Buttons */}
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

      {/* Media Grid */}
      <MediaGrid filters={{ type: filter }} />
    </div>
  )
}
