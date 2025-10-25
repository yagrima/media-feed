'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { authApi } from '@/lib/api/auth'
import { tokenManager } from '@/lib/auth/token-manager'
import toast from 'react-hot-toast'
import { Film, Upload, Library, LogOut, Bell, Settings } from 'lucide-react'

const navItems = [
  { href: '/library', label: 'Library', icon: Library },
  { href: '/import', label: 'Import', icon: Upload },
  { href: '/notifications', label: 'Notifications', icon: Bell },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function Navbar() {
  const pathname = usePathname()
  const router = useRouter()

  // Simple badge state (can be enhanced later)
  const unreadNotifications = 0

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
          <Link href="/library" className="flex items-center space-x-2">
            <Film className="h-6 w-6" />
            <span className="text-xl font-bold">Me Feed</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              const showBadge = item.href === '/notifications' && unreadNotifications && unreadNotifications > 0
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
