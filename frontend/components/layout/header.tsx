'use client';

import Link from 'next/link';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../context/theme-context';

export function Header() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="bg-white/80 dark:bg-dark-surface-elevated/80 backdrop-blur-md border-b border-border dark:border-dark-border sticky top-0 z-50 transition-colors duration-200">
      <div className="max-w-[1200px] mx-auto px-8 py-4 flex justify-between items-center">
        <Link href="/" className="text-xl font-bold text-text-primary dark:text-dark-text-primary hover:text-primary transition-colors">
          AI Melody Generator
        </Link>
        <div className="flex items-center gap-6">
          <nav>
            <ul className="list-none p-0 m-0 flex gap-6">
              <li>
                <Link href="/" className="text-text-secondary dark:text-dark-text-secondary hover:text-primary dark:hover:text-primary-light transition-colors text-sm font-medium">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/about" className="text-text-secondary dark:text-dark-text-secondary hover:text-primary dark:hover:text-primary-light transition-colors text-sm font-medium">
                  About
                </Link>
              </li>
            </ul>
          </nav>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-text-secondary dark:text-dark-text-secondary hover:bg-light-gray dark:hover:bg-dark-border transition-colors"
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
          </button>
        </div>
      </div>
    </header>
  );
}
