'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi, Notification } from '@/lib/api/notifications'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Pagination } from '@/components/ui/pagination'
import { Bell, Check, CheckCheck, Film, Upload, AlertCircle, Trash2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { useState } from 'react'

export function NotificationCenter() {
  const [page, setPage] = useState(1)
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['notifications', page],
    queryFn: () => notificationsApi.getNotifications(page, 20),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    refetchOnWindowFocus: true, // Refresh when user returns to tab
  })

  const markAsReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['unread-count'] })
    },
    onError: () => {
      toast.error('Failed to mark notification as read')
    },
  })

  const markAllAsReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['unread-count'] })
      toast.success('All notifications marked as read')
    },
    onError: () => {
      toast.error('Failed to mark all as read')
    },
  })

  const deleteNotificationMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.deleteNotification(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['unread-count'] })
      toast.success('Notification deleted')
    },
    onError: () => {
      toast.error('Failed to delete notification')
    },
  })

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'sequel_detected':
        return <Film className="h-5 w-5 text-primary" />
      case 'import_complete':
        return <Upload className="h-5 w-5 text-green-500" />
      case 'import_failed':
        return <AlertCircle className="h-5 w-5 text-destructive" />
      case 'system':
        return <Bell className="h-5 w-5 text-muted-foreground" />
      default:
        return <Bell className="h-5 w-5" />
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-16 text-center">
          <Bell className="h-12 w-12 animate-pulse text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">Loading notifications...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="py-16 text-center">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <p className="text-destructive">Failed to load notifications</p>
        </CardContent>
      </Card>
    )
  }

  const hasUnread = data && data.unread_count > 0

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
    queryClient.invalidateQueries({ queryKey: ['unread-count'] })
    toast.success('Notifications refreshed')
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bell className="h-6 w-6" />
              <CardTitle>Notifications</CardTitle>
              {hasUnread && (
                <Badge variant="default">{data.unread_count} unread</Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                title="Refresh notifications"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              {hasUnread && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => markAllAsReadMutation.mutate()}
                  disabled={markAllAsReadMutation.isPending}
                >
                  <CheckCheck className="h-4 w-4 mr-2" />
                  Mark all read
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {!data || data.items.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Bell className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No notifications</h3>
            <p className="text-muted-foreground text-center max-w-md">
              You&apos;re all caught up! New notifications will appear here.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {data.items.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onMarkAsRead={() => markAsReadMutation.mutate(notification.id)}
              onDelete={() => deleteNotificationMutation.mutate(notification.id)}
              isMarkingRead={markAsReadMutation.isPending}
              isDeleting={deleteNotificationMutation.isPending}
              getIcon={getNotificationIcon}
            />
          ))}

          {data.total > data.limit && (
            <Pagination
              currentPage={page}
              totalPages={Math.ceil(data.total / data.limit)}
              totalItems={data.total}
              itemsPerPage={data.limit}
              onPageChange={(newPage) => {
                setPage(newPage)
                window.scrollTo({ top: 0, behavior: 'smooth' })
              }}
            />
          )}
        </div>
      )}
    </div>
  )
}

interface NotificationItemProps {
  notification: Notification
  onMarkAsRead: () => void
  onDelete: () => void
  isMarkingRead: boolean
  isDeleting: boolean
  getIcon: (type: Notification['type']) => JSX.Element
}

function NotificationItem({
  notification,
  onMarkAsRead,
  onDelete,
  isMarkingRead,
  isDeleting,
  getIcon,
}: NotificationItemProps) {
  return (
    <Card className={notification.read ? 'bg-muted/30' : 'border-primary/50'}>
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <div className="mt-1">{getIcon(notification.type)}</div>

          <div className="flex-1 space-y-1">
            <div className="flex items-start justify-between gap-2">
              <h4 className="font-semibold leading-tight">{notification.title}</h4>
              {!notification.read && (
                <Badge variant="default" className="text-xs">
                  New
                </Badge>
              )}
            </div>

            <p className="text-sm text-muted-foreground">{notification.message}</p>

            {notification.data && Object.keys(notification.data).length > 0 && (
              <div className="text-xs text-muted-foreground pt-2">
                {notification.data.media_title && (
                  <span className="font-medium">{notification.data.media_title}</span>
                )}
                {notification.data.sequel_title && (
                  <span> → {notification.data.sequel_title}</span>
                )}
              </div>
            )}

            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-muted-foreground">
                {new Date(notification.created_at).toLocaleString()}
              </span>

              <div className="flex items-center gap-2">
                {!notification.read && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onMarkAsRead}
                    disabled={isMarkingRead}
                  >
                    <Check className="h-4 w-4 mr-1" />
                    Mark read
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onDelete}
                  disabled={isDeleting}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
