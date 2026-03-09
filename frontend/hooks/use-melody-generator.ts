'use client';

import { useState } from 'react';
import { useMelodyContext } from '../context/melody-context';
import { generateMelody } from '../utils/api';
import type { GenerationOptions } from '../types';

export function useMelodyGenerator() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addMelody } = useMelodyContext();

  const generate = async (modelId: string, instrument: number = 0, options: GenerationOptions = {}) => {
    setIsGenerating(true);
    setError(null);

    try {
      const newMelody = await generateMelody(modelId, instrument, options);
      addMelody(newMelody);
    } catch (err) {
      setError('Failed to generate melody. Please try again.');
      console.error('Error generating melody:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  return { generate, isGenerating, error };
}
