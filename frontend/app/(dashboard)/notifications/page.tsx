'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { NotificationCenter } from '@/components/notifications/notification-center'

export default function NotificationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Benachrichtigungen</h1>
        <p className="text-muted-foreground mt-1">
          Bleibe über neue Folgen und Fortsetzungen deiner Lieblingsfilme informiert
        </p>
      </div>

      <NotificationCenter />
    </div>
  )
}
