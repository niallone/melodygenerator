import '../styles/globals.css';
import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';
import { Providers } from './providers';
import ErrorBoundary from '../components/common/ErrorBoundary';

export const metadata = {
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

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <ErrorBoundary>
            <div className="flex flex-col min-h-screen">
              <Header />
              <div className="flex-1">
                <main className="max-w-[1200px] mx-auto p-8">
                  {children}
                </main>
              </div>
              <Footer />
            </div>
          </ErrorBoundary>
        </Providers>
      </body>
    </html>
  );
}
