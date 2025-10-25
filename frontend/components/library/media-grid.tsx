'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { mediaApi, UserMedia, MediaFilters } from '@/lib/api/media'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Pagination } from '@/components/ui/pagination'
import { Film, Tv, Loader2 } from 'lucide-react'

interface MediaGridProps {
  filters: MediaFilters
}

const ITEMS_PER_PAGE = 20

export function MediaGrid({ filters }: MediaGridProps) {
  const [currentPage, setCurrentPage] = useState(1)

  const { data, isLoading, error } = useQuery({
    queryKey: ['user-media', filters, currentPage],
    queryFn: () => mediaApi.getUserMedia({ ...filters, page: currentPage, limit: ITEMS_PER_PAGE }),
    placeholderData: (previousData) => previousData, // Keep showing old data while fetching new page
  })

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading your library...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="py-16 text-center">
          <p className="text-destructive">Failed to load media. Please try again.</p>
        </CardContent>
      </Card>
    )
  }

  if (!data || data.items.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-16">
          <Film className="h-16 w-16 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No media found</h3>
          <p className="text-muted-foreground text-center max-w-md">
            {filters.type && filters.type !== 'all'
              ? `No ${filters.type === 'movie' ? 'movies' : 'TV series'} in your library yet`
              : 'Your library is empty. Upload a CSV to add media!'}
          </p>
        </CardContent>
      </Card>
    )
  }

  const totalPages = Math.ceil(data.total / ITEMS_PER_PAGE)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {data.items.map((userMedia: UserMedia) => (
          <MediaCard key={userMedia.id} userMedia={userMedia} />
        ))}
      </div>

      {data.total > ITEMS_PER_PAGE && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={data.total}
          itemsPerPage={ITEMS_PER_PAGE}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  )
}

function MediaCard({ userMedia }: { userMedia: UserMedia }) {
  const { media } = userMedia
  const Icon = media.type === 'movie' ? Film : Tv

  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <Icon className="h-5 w-5 text-muted-foreground" />
          <Badge variant={media.type === 'movie' ? 'default' : 'secondary'}>
            {media.type === 'movie' ? 'Movie' : 'TV Series'}
          </Badge>
        </div>

        <h3 className="font-semibold mb-1 line-clamp-2">{media.title}</h3>

        {media.season_number && (
          <p className="text-sm text-muted-foreground mb-2">Season {media.season_number}</p>
        )}

        <div className="flex items-center justify-between mt-3 pt-3 border-t">
          <Badge variant="outline" className="text-xs">
            {media.platform}
          </Badge>
          <p className="text-xs text-muted-foreground">
            {new Date(userMedia.consumed_at).toLocaleDateString()}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
