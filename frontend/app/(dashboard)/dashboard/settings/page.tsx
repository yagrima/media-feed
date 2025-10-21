'use client'

import { useQuery } from '@tanstack/react-query'
import { authApi } from '@/lib/api/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { User, Mail, Calendar, Shield, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function SettingsPage() {
  const { data: user, isLoading } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => authApi.me(),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account settings and preferences
        </p>
      </div>

      {/* User Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Profile Information
          </CardTitle>
          <CardDescription>
            Your account details and status
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <Mail className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Email</p>
              <p className="font-medium">{user?.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Calendar className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Member since</p>
              <p className="font-medium">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Account Status</p>
              <Badge variant="default" className="mt-1">Active</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Notification Preferences</CardTitle>
          <CardDescription>
            Configure how you receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/dashboard/notifications/preferences">
            <Button variant="outline">
              Manage Notification Settings
            </Button>
          </Link>
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <CardTitle>Security</CardTitle>
          <CardDescription>
            Manage your account security settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">Password</p>
            <Button variant="outline" disabled>
              Change Password (Coming Soon)
            </Button>
          </div>
          <div>
            <p className="text-sm font-medium mb-2">Two-Factor Authentication</p>
            <Button variant="outline" disabled>
              Enable 2FA (Coming Soon)
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Data & Privacy */}
      <Card>
        <CardHeader>
          <CardTitle>Data & Privacy</CardTitle>
          <CardDescription>
            Manage your data and privacy settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">Export Your Data</p>
            <p className="text-sm text-muted-foreground mb-2">
              Download a copy of all your data
            </p>
            <Button variant="outline" disabled>
              Export Data (Coming Soon)
            </Button>
          </div>
          <div className="border-t pt-4">
            <p className="text-sm font-medium mb-2 text-destructive">Delete Account</p>
            <p className="text-sm text-muted-foreground mb-2">
              Permanently delete your account and all associated data
            </p>
            <Button variant="destructive" disabled>
              Delete Account (Coming Soon)
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
