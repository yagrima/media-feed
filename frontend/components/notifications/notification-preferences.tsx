'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi, type NotificationPreferences } from '@/lib/api/notifications'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { toast } from 'sonner'
import { Loader2, Save } from 'lucide-react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'

const preferencesSchema = z.object({
  email_enabled: z.boolean(),
  sequel_notifications: z.boolean(),
  import_notifications: z.boolean(),
  system_notifications: z.boolean(),
})

type PreferencesForm = z.infer<typeof preferencesSchema>

export function NotificationPreferences() {
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: () => notificationsApi.getPreferences(),
  })

  const updateMutation = useMutation({
    mutationFn: (preferences: Partial<NotificationPreferences>) =>
      notificationsApi.updatePreferences(preferences),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] })
      toast.success('Preferences updated successfully')
    },
    onError: () => {
      toast.error('Failed to update preferences')
    },
  })

  const {
    control,
    handleSubmit,
    formState: { isDirty },
  } = useForm<PreferencesForm>({
    resolver: zodResolver(preferencesSchema),
    values: data || {
      email_enabled: true,
      sequel_notifications: true,
      import_notifications: true,
      system_notifications: true,
    },
  })

  const onSubmit = (formData: PreferencesForm) => {
    updateMutation.mutate(formData)
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-16 text-center">
          <Loader2 className="h-12 w-12 animate-spin text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">Loading preferences...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="py-16 text-center">
          <p className="text-destructive">Failed to load preferences</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Card>
        <CardHeader>
          <CardTitle>Notification Preferences</CardTitle>
          <CardDescription>
            Customize how and when you receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Email Notifications */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5 flex-1">
                <Label htmlFor="email_enabled" className="text-base font-semibold cursor-pointer">
                  Email Notifications
                </Label>
                <p className="text-sm text-muted-foreground">
                  Receive notifications via email
                </p>
              </div>
              <Controller
                name="email_enabled"
                control={control}
                render={({ field }) => (
                  <Switch
                    id="email_enabled"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    aria-label="Enable email notifications"
                    aria-describedby="email_enabled_description"
                  />
                )}
              />
            </div>
          </div>

          <div className="border-t pt-6 space-y-4">
            <h3 className="font-semibold">Notification Types</h3>

            {/* Sequel Notifications */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5 flex-1">
                <Label htmlFor="sequel_notifications" className="text-base cursor-pointer">
                  Sequel Detected
                </Label>
                <p className="text-sm text-muted-foreground" id="sequel_notifications_description">
                  Get notified when a sequel is released for media you&apos;ve watched
                </p>
              </div>
              <Controller
                name="sequel_notifications"
                control={control}
                render={({ field }) => (
                  <Switch
                    id="sequel_notifications"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    aria-label="Enable sequel notifications"
                    aria-describedby="sequel_notifications_description"
                  />
                )}
              />
            </div>

            {/* Import Notifications */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5 flex-1">
                <Label htmlFor="import_notifications" className="text-base cursor-pointer">
                  Import Status
                </Label>
                <p className="text-sm text-muted-foreground" id="import_notifications_description">
                  Get notified about CSV import completion and failures
                </p>
              </div>
              <Controller
                name="import_notifications"
                control={control}
                render={({ field }) => (
                  <Switch
                    id="import_notifications"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    aria-label="Enable import notifications"
                    aria-describedby="import_notifications_description"
                  />
                )}
              />
            </div>

            {/* System Notifications */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5 flex-1">
                <Label htmlFor="system_notifications" className="text-base cursor-pointer">
                  System Updates
                </Label>
                <p className="text-sm text-muted-foreground" id="system_notifications_description">
                  Receive important system announcements and updates
                </p>
              </div>
              <Controller
                name="system_notifications"
                control={control}
                render={({ field }) => (
                  <Switch
                    id="system_notifications"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    aria-label="Enable system notifications"
                    aria-describedby="system_notifications_description"
                  />
                )}
              />
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <Button
              type="submit"
              disabled={!isDirty || updateMutation.isPending}
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Preferences
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </form>
  )
}
