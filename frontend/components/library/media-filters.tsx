'use client'

import { Button } from '@/components/ui/button'
import { Film, Tv, Library } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MediaFiltersProps {
  activeFilter: 'all' | 'movie' | 'tv_series'
  onFilterChange: (filter: 'all' | 'movie' | 'tv_series') => void
}

export function MediaFilters({ activeFilter, onFilterChange }: MediaFiltersProps) {
  const filters = [
    { value: 'all' as const, label: 'All', icon: Library },
    { value: 'movie' as const, label: 'Movies', icon: Film },
    { value: 'tv_series' as const, label: 'TV Series', icon: Tv },
  ]

  return (
    <div className="flex items-center space-x-2">
      {filters.map((filter) => {
        const Icon = filter.icon
        const isActive = activeFilter === filter.value

        return (
          <Button
            key={filter.value}
            variant={isActive ? 'default' : 'outline'}
            size="sm"
            onClick={() => onFilterChange(filter.value)}
            className="flex items-center space-x-2"
          >
            <Icon className="h-4 w-4" />
            <span>{filter.label}</span>
          </Button>
        )
      })}
    </div>
  )
}
