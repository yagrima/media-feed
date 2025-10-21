'use client'

import { useState } from 'react'
import { MediaGrid } from '@/components/library/media-grid'
import { MediaFilters } from '@/components/library/media-filters'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { Upload } from 'lucide-react'

export default function LibraryPage() {
  const [filter, setFilter] = useState<'all' | 'movie' | 'tv_series'>('all')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">My Library</h1>
          <p className="text-muted-foreground mt-1">
            View and manage your media collection
          </p>
        </div>
        <Link href="/dashboard/import">
          <Button>
            <Upload className="mr-2 h-4 w-4" />
            Import CSV
          </Button>
        </Link>
      </div>

      <MediaFilters activeFilter={filter} onFilterChange={setFilter} />

      <MediaGrid filters={{ type: filter }} />
    </div>
  )
}
