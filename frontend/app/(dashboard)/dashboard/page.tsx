'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/lib/api/dashboard'
import MediaDetailModal from '@/components/library/media-detail-modal'
import { Upload, Film, Tv, BookOpen, Headphones, TrendingUp, Clock, Loader2 } from 'lucide-react'

const MEDIA_TYPE_CONFIG = {
  movie: {
    label: 'Movies',
    icon: Film,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-100 dark:bg-blue-900/20',
  },
  tv_series: {
    label: 'TV Series',
    icon: Tv,
    color: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-100 dark:bg-purple-900/20',
  },
  book: {
    label: 'Books',
    icon: BookOpen,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900/20',
  },
  audiobook: {
    label: 'Audiobooks',
    icon: Headphones,
    color: 'text-orange-600 dark:text-orange-400',
    bgColor: 'bg-orange-100 dark:bg-orange-900/20',
  },
} as const

export default function DashboardPage() {
  const router = useRouter()
  const [selectedMediaId, setSelectedMediaId] = useState<string | null>(null)
  const [selectedMediaTitle, setSelectedMediaTitle] = useState<string>('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-statistics'],
    queryFn: () => dashboardApi.getStatistics(),
  })

  const handleMediaClick = (mediaId: string, mediaType: string, title: string) => {
    if (mediaType === 'tv_series') {
      setSelectedMediaId(mediaId)
      setSelectedMediaTitle(title)
      setIsModalOpen(true)
    } else {
      // For movies or other types, navigate to library with filter
      router.push(`/library?type=${mediaType}`)
    }
  }

  const handleTypeCardClick = (type: string) => {
    router.push(`/library?type=${type}`)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading your dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card className="border-destructive">
          <CardContent className="py-16 text-center">
            <p className="text-destructive">Failed to load dashboard. Please try again.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const isEmpty = !stats || stats.total_items === 0

  if (isEmpty) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Welcome to Me Feed</h1>
            <p className="text-muted-foreground mt-1">
              Track your media consumption and get sequel notifications
            </p>
          </div>
          <div className="flex gap-3">
            <Link href="/import">
              <Button size="lg">
                <Upload className="mr-2 h-4 w-4" />
                Import CSV
              </Button>
            </Link>
            <Link href="/import">
              <Button size="lg" variant="outline">
                <Headphones className="mr-2 h-4 w-4" />
                Import Audible
              </Button>
            </Link>
          </div>
        </div>

        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Film className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No media yet</h3>
            <p className="text-muted-foreground text-center max-w-md">
              Use the "Import CSV" button above to upload your Netflix viewing history and start tracking your media consumption.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Overview of your media consumption
          </p>
        </div>
        <Link href="/import">
          <Button>
            <Upload className="mr-2 h-4 w-4" />
            Import More
          </Button>
        </Link>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Object.entries(MEDIA_TYPE_CONFIG).map(([type, config]) => {
          const typeStats = stats?.statistics[type as keyof typeof stats.statistics]
          const Icon = config.icon
          
          if (!typeStats || typeStats.total_count === 0) return null
          
          return (
            <Card 
              key={type} 
              className="cursor-pointer hover:border-primary/50 transition-colors"
              onClick={() => handleTypeCardClick(type)}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {config.label}
                </CardTitle>
                <div className={`p-2 rounded-lg ${config.bgColor}`}>
                  <Icon className={`h-4 w-4 ${config.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{typeStats.unique_count}</div>
                <p className="text-xs text-muted-foreground">
                  {type === 'tv_series' 
                    ? `${typeStats.total_count} episodes watched`
                    : `${typeStats.total_count} items`}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Activity Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* This Week */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Week</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.this_week_count || 0}</div>
            <p className="text-xs text-muted-foreground">
              Items watched in the last 7 days
            </p>
          </CardContent>
        </Card>

        {/* Total Items */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Items</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_items || 0}</div>
            <p className="text-xs text-muted-foreground">
              All time media consumption
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest watched content</CardDescription>
        </CardHeader>
        <CardContent>
          {!stats?.recent_activity || stats.recent_activity.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No recent activity</p>
          ) : (
            <div className="space-y-3">
              {stats.recent_activity.map((item) => {
                const config = MEDIA_TYPE_CONFIG[item.type as keyof typeof MEDIA_TYPE_CONFIG]
                const Icon = config?.icon || Film
                
                return (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                    onClick={() => handleMediaClick(item.media_id, item.type, item.title)}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className={`p-2 rounded-lg ${config?.bgColor || 'bg-gray-100'}`}>
                        <Icon className={`h-4 w-4 ${config?.color || 'text-gray-600'}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{item.title}</p>
                        {item.season_number && item.episode_title && (
                          <p className="text-sm text-muted-foreground truncate">
                            S{item.season_number}: {item.episode_title}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {item.platform && (
                        <Badge variant="outline" className="text-xs">
                          {item.platform}
                        </Badge>
                      )}
                      {item.consumed_at && (
                        <p className="text-xs text-muted-foreground">
                          {new Date(item.consumed_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Modal */}
      {selectedMediaId && (
        <MediaDetailModal
          mediaId={selectedMediaId}
          mediaTitle={selectedMediaTitle}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false)
            setSelectedMediaId(null)
            setSelectedMediaTitle('')
          }}
        />
      )}
    </div>
  )
}
