'use client'

import { NotificationPreferences } from '@/components/notifications/notification-preferences'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'

export default function NotificationPreferencesPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <Link href="/notifications">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Zurück zu Benachrichtigungen
          </Button>
        </Link>
        
        <h1 className="text-3xl font-bold">Benachrichtigungs-Einstellungen</h1>
        <p className="text-muted-foreground mt-1">
          Verwalte, wie du Benachrichtigungen erhältst
        </p>
      </div>

      <NotificationPreferences />
    </div>
  )
}
