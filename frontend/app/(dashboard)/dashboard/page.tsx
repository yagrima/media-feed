'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { Upload, Film } from 'lucide-react'

export default function DashboardPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Meine Mediathek</h1>
          <p className="text-muted-foreground mt-1">
            Verfolge deine Medienkonsumtion und erhalte Fortsetzungs-Benachrichtigungen
          </p>
        </div>
        <Link href="/import">
          <Button>
            <Upload className="mr-2 h-4 w-4" />
            CSV importieren
          </Button>
        </Link>
      </div>

      {/* Empty State */}
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-16">
          <Film className="h-16 w-16 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">Noch keine Medien vorhanden</h3>
          <p className="text-muted-foreground text-center max-w-md">
            Verwende den Button "CSV importieren" oben, um deine Netflix Verlaufs-CSV-Datei hochzuladen und deine Medienkonsumtion zu verfolgen.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
