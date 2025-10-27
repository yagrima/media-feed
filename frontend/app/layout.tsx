import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Me Feed - Track Your Media Consumption',
  description: 'Never miss a sequel. Track your media consumption and get notified when new seasons or sequels are available.',
  keywords: ['media tracker', 'movie tracking', 'tv series tracking', 'sequel notifications', 'binge watching', 'media consumption'],
  authors: [{ name: 'Me Feed Team' }],
  creator: 'Me Feed',
  publisher: 'Me Feed',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: '/',
    title: 'Me Feed - Track Your Media Consumption',
    description: 'Never miss a sequel. Track your media consumption and get notified when new seasons or sequels are available.',
    siteName: 'Me Feed',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Me Feed - Track Your Media Consumption',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Me Feed - Track Your Media Consumption',
    description: 'Never miss a sequel. Track your media consumption and get notified when new seasons or sequels are available.',
    images: ['/og-image.png'],
    creator: '@mefeed',
  },
  robots: {
    index: true,
    follow: true,
    nocache: true,
    googleBot: {
      index: true,
      follow: true,
      noimageindex: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
  },
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#000000' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
