import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '5G Network Slice Simulator',
  description: 'Real-time 5G Network Slicing Simulation Platform',
  icons: {
    icon: '🌐',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#1a1a2e" />
      </head>
      <body className={`${inter.className} bg-slate-950 text-white`}>
        {children}
      </body>
    </html>
  )
}