'use client'

import * as Sentry from "@sentry/nextjs"
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { authApi } from '@/lib/api/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { User, Mail, Calendar, Shield, Loader2, Bell, Bug, BookOpen, Key, Copy, Check } from 'lucide-react'
import Link from 'next/link'
import { ConnectAudibleModal } from '@/components/audible/connect-audible-modal'
import { AudibleStatusCard } from '@/components/audible/audible-status-card'
import { useToast } from '@/hooks/use-toast'

export default function SettingsPage() {
  const { toast } = useToast()
  const [showAudibleModal, setShowAudibleModal] = useState(false)
  const [showToken, setShowToken] = useState(false)
  const [tokenCopied, setTokenCopied] = useState(false)
  const { data: user, isLoading } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => authApi.me(),
  })

  const getAuthToken = () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('access_token') || ''
    }
    return ''
  }

  const copyToken = () => {
    const token = getAuthToken()
    if (token) {
      navigator.clipboard.writeText(token)
      setTokenCopied(true)
      toast({
        title: "✅ Token kopiert!",
        description: "Jetzt in der Browser-Extension einfügen.",
        duration: 4000,
      })
      setTimeout(() => setTokenCopied(false), 2000)
    } else {
      toast({
        title: "❌ Fehler",
        description: "Kein Token gefunden. Bitte erneut einloggen.",
        variant: "destructive",
      })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Einstellungen</h1>
        <p className="text-muted-foreground mt-1">
          Verwalte deine Account-Einstellungen und Präferenzen
        </p>
      </div>

      {/* User Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Profil-Informationen
          </CardTitle>
          <CardDescription>
            Deine Account-Details und Status
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <Mail className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">E-Mail</p>
              <p className="font-medium">{user?.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Calendar className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Mitglied seit</p>
              <p className="font-medium">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString('de-DE') : 'N/A'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Account-Status</p>
              <Badge variant="default" className="mt-1">Aktiv</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Benachrichtigungs-Einstellungen
          </CardTitle>
          <CardDescription>
            Konfiguriere, wie du Benachrichtigungen erhältst
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/notifications/preferences">
            <Button variant="outline">
              Benachrichtigungs-Einstellungen verwalten
            </Button>
          </Link>
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <CardTitle>Sicherheit</CardTitle>
          <CardDescription>
            Verwalte deine Account-Sicherheitseinstellungen
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">Passwort</p>
            <Button variant="outline" disabled>
              Passwort ändern (Demnächst verfügbar)
            </Button>
          </div>
          <div>
            <p className="text-sm font-medium mb-2">Zwei-Faktor-Authentifizierung</p>
            <Button variant="outline" disabled>
              2FA aktivieren (Demnächst verfügbar)
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Data & Privacy */}
      <Card>
        <CardHeader>
          <CardTitle>Daten & Datenschutz</CardTitle>
          <CardDescription>
            Verwalte deine Daten und Datenschutzeinstellungen
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">Daten exportieren</p>
            <p className="text-sm text-muted-foreground mb-2">
              Lade eine Kopie all deiner Daten herunter
            </p>
            <Button variant="outline" disabled>
              Daten exportieren (Demnächst verfügbar)
            </Button>
          </div>
          <div className="border-t pt-4">
            <p className="text-sm font-medium mb-2 text-destructive">Account löschen</p>
            <p className="text-sm text-muted-foreground mb-2">
              Lösche deinen Account und alle zugehörigen Daten dauerhaft
            </p>
            <Button variant="destructive" disabled>
              Account löschen (Demnächst verfügbar)
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Developer Tools */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Entwickler-Tools
          </CardTitle>
          <CardDescription>
            API-Token für Browser-Extension und Integrationen
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">Authentifizierungs-Token</p>
            <p className="text-sm text-muted-foreground mb-3">
              Nutze diesen Token für die Audible Browser-Extension
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setShowToken(!showToken)}
              >
                {showToken ? 'Token verbergen' : 'Token anzeigen'}
              </Button>
              {showToken && (
                <Button
                  variant="outline"
                  onClick={copyToken}
                  className="gap-2"
                >
                  {tokenCopied ? (
                    <>
                      <Check className="h-4 w-4" />
                      Kopiert!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Token kopieren
                    </>
                  )}
                </Button>
              )}
            </div>
            {showToken && (
              <div className="mt-3 p-3 bg-muted rounded-lg border">
                <code className="text-xs break-all font-mono">
                  {getAuthToken()}
                </code>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Audible Connection Modal */}
      <ConnectAudibleModal
        open={showAudibleModal}
        onClose={() => setShowAudibleModal(false)}
        onSuccess={(data) => {
          toast({
            title: "Erfolgreich verbunden!",
            description: `${data.books_imported} Hörbücher von Audible importiert.`,
          })
          setShowAudibleModal(false)
        }}
      />

      {/* Debug Section (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-900">
              <Bug className="h-5 w-5" />
              Debug Tools (Development Only)
            </CardTitle>
            <CardDescription className="text-orange-700">
              Test error tracking and monitoring
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium mb-2 text-orange-900">Test Sentry Error Tracking</p>
              <p className="text-sm text-orange-700 mb-2">
                Click to trigger a test error and verify Sentry integration
              </p>
              <Button 
                variant="destructive"
                onClick={() => {
                  Sentry.captureMessage("Test error from Settings page!")
                  throw new Error("This is a test error for Sentry! Check your Sentry dashboard.")
                }}
              >
                <Bug className="h-4 w-4 mr-2" />
                Trigger Test Error
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
