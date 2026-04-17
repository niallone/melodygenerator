import '../styles/globals.css';
import { Inter } from 'next/font/google';
import { Providers } from './providers';
import ErrorBoundary from '../components/common/error-boundary';
import type { Metadata } from 'next';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'AI Melody Generator',
  description: 'Generate unique melodies with AI-powered neural networks. Create music using LSTM and Transformer models.',
  icons: {
    icon: '/favicon.ico',
  },
  metadataBase: new URL('https://melodygenerator.fun'),
  openGraph: {
    title: 'AI Melody Generator',
    description: 'Generate unique melodies with AI-powered neural networks.',
    url: 'https://melodygenerator.fun',
    siteName: 'AI Melody Generator',
    type: 'website',
  },
  twitter: {
    card: 'summary',
    title: 'AI Melody Generator',
    description: 'Generate unique melodies with AI-powered neural networks.',
  },
  alternates: {
    canonical: 'https://melodygenerator.fun',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className={`${inter.className} bg-[#07060b] text-white`}>
        <Providers>
          <ErrorBoundary>
            <div className="flex flex-col min-h-screen">
              {children}
            </div>
          </ErrorBoundary>
        </Providers>
        <script defer src="https://t.melodygenerator.fun/script.js" data-website-id="c371cafa-7c4e-4f82-8069-ba7fa05c0ced" />
      </body>
    </html>
  );
}
