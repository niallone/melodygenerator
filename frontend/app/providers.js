'use client';

import { MelodyProvider } from '../context/MelodyContext';

export function Providers({ children }) {
  return (
    <MelodyProvider>
      {children}
    </MelodyProvider>
  );
}
