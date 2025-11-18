'use client'

import { useState, useEffect, useRef, useMemo } from 'react'
import { useQuery, useInfiniteQuery } from '@tanstack/react-query'
import { mediaApi, UserMedia, MediaFilters } from '@/lib/api/media'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Pagination } from '@/components/ui/pagination'
import { Film, Tv, Loader2, BookOpen, Layers } from 'lucide-react'
import MediaDetailModal from './media-detail-modal'
import SeriesDetailModal from './series-detail-modal'

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
  const rawItems = useMemo(() => {
    return viewMode === 'infinite' && infiniteData
      ? infiniteData.pages.flatMap((page) => page.items)
      : data?.items || []
  }, [viewMode, infiniteData, data])

  // Group items by series (for audiobooks)
  const groupedItems = useMemo(() => {
    const grouped: any[] = []
    const seriesMap = new Map<string, UserMedia[]>()

    // First pass: Identify series and standalone items
    rawItems.forEach(item => {
      // Check if it's an audiobook part of a series
      if (item.media.type === 'audiobook') {
        let seriesTitle = item.media.media_metadata?.series?.title;
        
        // Fallback: Regex matching for common patterns if metadata is missing
        if (!seriesTitle) {
          const title = item.media.title;
          // Match: "Title: Series Name, Book X" or "Title (Series Name X)"
          // Heuristic: Look for content after colon or in parenthesis
          const colonMatch = title.match(/^(.*?):\s+(.*?),?\s+Book\s+\d+$/i);
          if (colonMatch) {
             // This is risky, usually "Series: Title, Book X" or "Title: Series, Book X"
             // Let's look for explicit "Book X" pattern
             // Example: "Harry Potter and the Stone: Harry Potter, Book 1" -> Series: Harry Potter
             // Example: "Survival Quest: Way of the Shaman 1" -> Series: Way of the Shaman
             const bookMatch = title.match(/:\s+(.*?)[\s,]+(?:Book|Vol|Volume|Part)\.?\s*\d+/i);
             if (bookMatch) seriesTitle = bookMatch[1].trim();
          }
          
          if (!seriesTitle) {
             // Example: "Title (Series Name 1)"
             const parenMatch = title.match(/\(([^)]+?)\s+\d+\)/);
             if (parenMatch) seriesTitle = parenMatch[1].trim();
          }
        }

        if (seriesTitle) {
          if (!seriesMap.has(seriesTitle)) {
            seriesMap.set(seriesTitle, [])
          }
          seriesMap.get(seriesTitle)?.push(item)
        } else {
          grouped.push({ type: 'item', data: item })
        }
      } else {
        // Standalone item (movies, TV)
        grouped.push({ type: 'item', data: item })
      }
    })

    // Second pass: Add series groups
    seriesMap.forEach((items, seriesTitle) => {
      // Sort by sequence/purchase date if needed
      // For now, just group them
      grouped.push({
        type: 'series_group',
        seriesTitle: seriesTitle,
        items: items,
        // Use the first item as representative for cover/metadata
        representative: items[0]
      })
    })

    return grouped
  }, [rawItems])

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

  if (rawItems.length === 0 && !isLoading) {
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
        {groupedItems.map((entry: any, index) => (
          entry.type === 'series_group' ? (
            <SeriesCard key={`series-${entry.seriesTitle}`} group={entry} />
          ) : (
            <MediaCard key={entry.data.id} userMedia={entry.data} />
          )
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
          {!hasNextPage && rawItems.length > 0 && (
            <p className="text-sm text-muted-foreground">You've reached the end of your library ({totalItems} items)</p>
          )}
        </div>
      )}
    </div>
  )
}

function SeriesCard({ group }: { group: any }) {
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const count = group.items.length
  const { representative } = group
  
  return (
    <>
      <Card 
        className="hover:shadow-lg transition-shadow cursor-pointer border-l-4 border-l-primary"
        onClick={() => setIsDetailOpen(true)}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <Layers className="h-5 w-5 text-primary" />
            <Badge variant="default" className="bg-primary/10 text-primary hover:bg-primary/20">
              Audiobook Series
            </Badge>
          </div>

          <div className="mb-1">
            <h3 className="font-semibold line-clamp-2 inline">{group.seriesTitle}</h3>
            <span className="text-sm text-muted-foreground ml-2">({count} Books)</span>
          </div>

          <p className="text-sm text-muted-foreground mb-2 line-clamp-1">
            {representative.media.media_metadata?.authors?.join(', ') || 'Unknown Author'}
          </p>

          <div className="flex items-center justify-between mt-3 pt-3 border-t">
            <Badge variant="outline" className="text-xs">
              Audible
            </Badge>
            <p className="text-xs text-muted-foreground">
              Series
            </p>
          </div>
        </CardContent>
      </Card>

      <SeriesDetailModal
        seriesTitle={group.seriesTitle}
        books={group.items}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
      />
    </>
  )
}

function MediaCard({ userMedia }: { userMedia: UserMedia }) {
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const { media } = userMedia
  
  let Icon = Film
  if (media.type === 'tv_series') Icon = Tv
  if (media.type === 'audiobook') Icon = BookOpen

  // Show episode count only for TV series
  const episodeCount = media.type === 'tv_series' && media.watched_episodes_count != null
    ? media.total_episodes
      ? `${media.watched_episodes_count}/${media.total_episodes} episodes` // With TMDB data
      : `${media.watched_episodes_count} episodes` // Without TMDB data
    : media.type === 'tv_series'
    ? '? episodes' // Fallback if count not available yet
    : null

  const handleClick = () => {
    // Only open detail modal for TV series
    if (media.type === 'tv_series') {
      setIsDetailOpen(true)
    }
  }
  
  // Format date display
  const dateLabel = media.type === 'audiobook' ? 'Last Heard' : 'Watched'
  const displayDate = new Date(userMedia.consumed_at).toLocaleDateString()

  return (
    <>
      <Card 
        className="hover:shadow-lg transition-shadow cursor-pointer" 
        onClick={handleClick}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <Icon className="h-5 w-5 text-muted-foreground" />
            <Badge variant={media.type === 'movie' ? 'default' : media.type === 'audiobook' ? 'outline' : 'secondary'}>
              {media.type === 'movie' ? 'Movie' : media.type === 'audiobook' ? 'Audiobook' : 'TV Series'}
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
          
          {media.type === 'audiobook' && media.media_metadata?.authors && (
             <p className="text-sm text-muted-foreground mb-2 line-clamp-1">
               {media.media_metadata.authors.join(', ')}
             </p>
          )}

          <div className="flex items-center justify-between mt-3 pt-3 border-t">
            <Badge variant="outline" className="text-xs">
              {media.platform}
            </Badge>
            <div className="text-right">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{dateLabel}</p>
              <p className="text-xs text-muted-foreground">{displayDate}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detail Modal for TV Series */}
      {media.type === 'tv_series' && (
        <MediaDetailModal
          mediaId={media.id}
          mediaTitle={media.title}
          isOpen={isDetailOpen}
          onClose={() => setIsDetailOpen(false)}
        />
      )}
    </>
  )
}
