'use client'

import { NotificationPreferences } from '@/components/notifications/notification-preferences'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'

export default function NotificationPreferencesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <Link href="/dashboard/notifications">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Notifications
            </Button>
          </Link>
        </div>

        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Notification Preferences</h1>
          <p className="text-muted-foreground">
            Manage how you receive notifications
          </p>
        </div>

        <NotificationPreferences />
      </div>
    </div>
  )
}
