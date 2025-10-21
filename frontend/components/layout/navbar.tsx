'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { authApi } from '@/lib/api/auth'
import { notificationsApi } from '@/lib/api/notifications'
import { tokenManager } from '@/lib/auth/token-manager'
import { toast } from 'sonner'
import { Film, Upload, Library, LogOut, Bell, Settings } from 'lucide-react'

const navItems = [
  { href: '/dashboard', label: 'Library', icon: Library },
  { href: '/dashboard/import', label: 'Import', icon: Upload },
  { href: '/dashboard/notifications', label: 'Notifications', icon: Bell },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
]

export function Navbar() {
  const pathname = usePathname()
  const router = useRouter()

  // Fetch unread notification count
  const { data: unreadNotifications } = useQuery({
    queryKey: ['unread-count'],
    queryFn: async () => {
      const notifications = await notificationsApi.getUnread()
      return notifications.length
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      // Continue with logout even if API call fails
    } finally {
      tokenManager.clearTokens()
      toast.success('Logged out successfully')
      router.push('/login')
    }
  }

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center space-x-2">
            <Film className="h-6 w-6" />
            <span className="text-xl font-bold">Me Feed</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              const showBadge = item.href === '/dashboard/notifications' && unreadNotifications && unreadNotifications > 0
              return (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant={isActive ? 'secondary' : 'ghost'}
                    className={cn('flex items-center space-x-2 relative')}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                    {showBadge && (
                      <Badge variant="destructive" className="ml-2 px-1.5 py-0 text-xs">
                        {unreadNotifications > 99 ? '99+' : unreadNotifications}
                      </Badge>
                    )}
                  </Button>
                </Link>
              )
            })}
          </div>

          {/* Logout Button */}
          <Button variant="ghost" onClick={handleLogout} className="flex items-center space-x-2">
            <LogOut className="h-4 w-4" />
            <span>Logout</span>
          </Button>
        </div>
      </div>
    </nav>
  )
}
