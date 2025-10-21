'use client'

import { NotificationCenter } from '@/components/notifications/notification-center'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Settings } from 'lucide-react'

export default function NotificationsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Notifications</h1>
            <p className="text-muted-foreground">
              Stay updated on new sequels and import status
            </p>
          </div>
          <Link href="/dashboard/notifications/preferences">
            <Button variant="outline">
              <Settings className="h-4 w-4 mr-2" />
              Preferences
            </Button>
          </Link>
        </div>

        <NotificationCenter />
      </div>
    </div>
  )
}
