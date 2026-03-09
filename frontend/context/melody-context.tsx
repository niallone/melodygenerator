'use client';

import { createContext, useContext, useState, type ReactNode } from 'react';
import type { Melody } from '../types';

interface MelodyContextValue {
  melodies: Melody[];
  addMelody: (melody: Melody) => void;
}

const MelodyContext = createContext<MelodyContextValue | undefined>(undefined);

export function MelodyProvider({ children }: { children: ReactNode }) {
  const [melodies, setMelodies] = useState<Melody[]>([]);

  const addMelody = (melody: Melody) => {
    setMelodies((prev) => [...prev, melody]);
  };

  return (
    <MelodyContext.Provider value={{ melodies, addMelody }}>
      {children}
    </MelodyContext.Provider>
  );
}

export function useMelodyContext(): MelodyContextValue {
  const context = useContext(MelodyContext);
  if (!context) {
    throw new Error('useMelodyContext must be used within a MelodyProvider');
  }
  return context;
}
