'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { Upload, Film } from 'lucide-react'

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">My Library</h1>
          <p className="text-muted-foreground mt-1">
            Track your media consumption and get sequel notifications
          </p>
        </div>
        <Link href="/dashboard/import">
          <Button>
            <Upload className="mr-2 h-4 w-4" />
            Import CSV
          </Button>
        </Link>
      </div>

      {/* Empty State */}
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-16">
          <Film className="h-16 w-16 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No media yet</h3>
          <p className="text-muted-foreground text-center mb-6 max-w-md">
            Upload your Netflix viewing history CSV to get started tracking your media consumption
          </p>
          <Link href="/dashboard/import">
            <Button>
              <Upload className="mr-2 h-4 w-4" />
              Upload your first CSV
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  )
}
