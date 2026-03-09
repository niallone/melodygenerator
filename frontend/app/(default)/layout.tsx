import Link from 'next/link';

function MagazineHeader() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/[0.06]">
      <div className="backdrop-blur-md bg-[#07060b]/80">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-10 py-4 flex justify-between items-center">
          <Link href="/" className="text-sm font-bold text-white tracking-wide">
            AI Melody Generator
          </Link>
          <nav>
            <ul className="list-none p-0 m-0 flex gap-6">
              <li>
                <Link href="/" className="text-xs uppercase tracking-[0.15em] text-white/50 hover:text-white transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/studio" className="text-xs uppercase tracking-[0.15em] text-white/50 hover:text-white transition-colors">
                  Studio
                </Link>
              </li>
              <li>
                <Link href="/about" className="text-xs uppercase tracking-[0.15em] text-white/50 hover:text-white transition-colors">
                  About
                </Link>
              </li>
              <li>
                <a href="https://github.com/niallone/melodygenerator" target="_blank" rel="noopener noreferrer" className="text-xs uppercase tracking-[0.15em] text-white/50 hover:text-white transition-colors">
                  GitHub
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
}

function MagazineFooter() {
  return (
    <footer className="border-t border-white/[0.06] bg-[#07060b] py-10 px-6 sm:px-10">
      <div className="max-w-[1400px] mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
        <p className="text-xs text-white/30">&copy; {new Date().getFullYear()} AI Melody Generator</p>
        <a
          href="https://github.com/niallone/melodygenerator"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-white/30 hover:text-white/60 transition-colors"
        >
          View source on GitHub
        </a>
      </div>
    </footer>
  );
}

export default function MagazineLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="dark bg-[#07060b] text-white min-h-screen">
      <MagazineHeader />
      <main className="pt-[60px]">
        {children}
      </main>
      <MagazineFooter />
    </div>
  );
}
