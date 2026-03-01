import { useState } from 'react';
import { useMelodyContext } from '../context/MelodyContext';
import { generateMelody } from '../utils/api';

/**
 * Custom hook for generating melodies.
 */
export function useMelodyGenerator() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const { addMelody } = useMelodyContext();

  /**
   * Generates a new melody using the specified model, instrument, and options.
   *
   * @param {string} modelId - The ID of the model to use
   * @param {number} instrument - The General MIDI program number
   * @param {Object} options - Generation options (temperature, top_k, top_p, num_notes, etc.)
   */
  const generate = async (modelId, instrument = 0, options = {}) => {
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
