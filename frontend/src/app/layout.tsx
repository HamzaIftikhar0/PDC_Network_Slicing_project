import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '5G Network Slice Traffic Generator',
  description: 'Real-time performance monitoring for eMBB, URLLC, and mMTC slices',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}