'use client';

import { MelodyProvider } from '../context/melody-context';
import { ThemeProvider } from '../context/theme-context';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <MelodyProvider>
        {children}
      </MelodyProvider>
    </ThemeProvider>
  );
}
