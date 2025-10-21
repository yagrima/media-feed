import { ProtectedRoute } from '@/components/auth/protected-route'
import { Navbar } from '@/components/layout/navbar'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  )
}
