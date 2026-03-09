'use client';

import Link from 'next/link';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../context/theme-context';

export function Header() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="bg-[#07060b]/80 backdrop-blur-md border-b border-white/[0.08] sticky top-0 z-50">
      <div className="max-w-[1200px] mx-auto px-8 py-4 flex justify-between items-center">
        <Link href="/" className="text-xl font-bold text-white hover:text-indigo-400 transition-colors">
          AI Melody Generator
        </Link>
        <div className="flex items-center gap-6">
          <nav>
            <ul className="list-none p-0 m-0 flex gap-6">
              <li>
                <Link href="/" className="text-white/50 hover:text-indigo-400 transition-colors text-sm font-medium">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/about" className="text-white/50 hover:text-indigo-400 transition-colors text-sm font-medium">
                  About
                </Link>
              </li>
            </ul>
          </nav>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-white/50 hover:bg-white/[0.05] transition-colors"
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
          </button>
        </div>
      </div>
    </header>
  );
}
