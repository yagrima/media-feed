'use client'

import { useState, useEffect, useRef } from 'react'
import { useQuery, useInfiniteQuery } from '@tanstack/react-query'
import { mediaApi, UserMedia, MediaFilters } from '@/lib/api/media'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Pagination } from '@/components/ui/pagination'
import { Film, Tv, Loader2 } from 'lucide-react'

interface MediaGridProps {
  filters: MediaFilters
  viewMode: 'pagination' | 'infinite'
}

const ITEMS_PER_PAGE = 20

export function MediaGrid({ filters, viewMode }: MediaGridProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const observerTarget = useRef<HTMLDivElement>(null)

  // Pagination mode query
  const { data: paginatedData, isLoading: isPaginationLoading, error: paginationError } = useQuery({
    queryKey: ['user-media', filters, currentPage],
    queryFn: () => mediaApi.getUserMedia({ ...filters, page: currentPage, limit: ITEMS_PER_PAGE }),
    placeholderData: (previousData) => previousData,
    enabled: viewMode === 'pagination',
  })

  // Infinite scroll mode query
  const {
    data: infiniteData,
    isLoading: isInfiniteLoading,
    error: infiniteError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['user-media-infinite', filters],
    queryFn: ({ pageParam = 1 }) => mediaApi.getUserMedia({ ...filters, page: pageParam, limit: ITEMS_PER_PAGE }),
    getNextPageParam: (lastPage) => {
      const nextPage = lastPage.page + 1
      const totalPages = Math.ceil(lastPage.total / ITEMS_PER_PAGE)
      return nextPage <= totalPages ? nextPage : undefined
    },
    initialPageParam: 1,
    enabled: viewMode === 'infinite',
  })

  // Intersection Observer for infinite scroll
  useEffect(() => {
    if (viewMode !== 'infinite') return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage()
        }
      },
      { threshold: 0.1 }
    )

    const currentTarget = observerTarget.current
    if (currentTarget) {
      observer.observe(currentTarget)
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget)
      }
    }
  }, [viewMode, hasNextPage, isFetchingNextPage, fetchNextPage])

  // Use appropriate data based on mode
  const data = viewMode === 'pagination' ? paginatedData : undefined
  const isLoading = viewMode === 'pagination' ? isPaginationLoading : isInfiniteLoading
  const error = viewMode === 'pagination' ? paginationError : infiniteError

  // Flatten infinite data
  const allItems = viewMode === 'infinite' && infiniteData
    ? infiniteData.pages.flatMap((page) => page.items)
    : data?.items || []

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

  if (allItems.length === 0 && !isLoading) {
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

  const totalPages = data ? Math.ceil(data.total / ITEMS_PER_PAGE) : 0
  const totalItems = viewMode === 'pagination' && data ? data.total : infiniteData?.pages[0]?.total || 0

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {allItems.map((userMedia: UserMedia) => (
          <MediaCard key={userMedia.id} userMedia={userMedia} />
        ))}
      </div>

      {/* Pagination mode */}
      {viewMode === 'pagination' && data && data.total > ITEMS_PER_PAGE && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={data.total}
          itemsPerPage={ITEMS_PER_PAGE}
          onPageChange={handlePageChange}
        />
      )}

      {/* Infinite scroll observer target */}
      {viewMode === 'infinite' && (
        <div ref={observerTarget} className="flex items-center justify-center py-8">
          {isFetchingNextPage && (
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">Loading more...</p>
            </div>
          )}
          {!hasNextPage && allItems.length > 0 && (
            <p className="text-sm text-muted-foreground">You've reached the end of your library ({totalItems} items)</p>
          )}
        </div>
      )}
    </div>
  )
}

function MediaCard({ userMedia }: { userMedia: UserMedia }) {
  const { media } = userMedia
  const Icon = media.type === 'movie' ? Film : Tv

  // Show episode count only for TV series
  // Use nullish coalescing to handle 0 and undefined cases
  const episodeCount = media.type === 'tv_series' && media.watched_episodes_count != null
    ? `${media.watched_episodes_count}/XX`
    : media.type === 'tv_series'
    ? '?/XX' // Fallback if count not available yet (no extra parentheses)
    : null

  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <Icon className="h-5 w-5 text-muted-foreground" />
          <Badge variant={media.type === 'movie' ? 'default' : 'secondary'}>
            {media.type === 'movie' ? 'Movie' : 'TV Series'}
          </Badge>
        </div>

        <div className="mb-1">
          <h3 className="font-semibold line-clamp-2 inline">{media.title}</h3>
          {episodeCount && (
            <span className="text-sm text-muted-foreground ml-2">({episodeCount})</span>
          )}
        </div>

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
