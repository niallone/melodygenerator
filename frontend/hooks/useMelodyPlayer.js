import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for managing melody playback using HTML5 Audio.
 *
 * @param {string} url - The URL of the audio file (WAV) to play
 * @returns {Object} An object containing playback control functions and state
 */
export function useMelodyPlayer(url) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const audioRef = useRef(null);

  // Load audio when URL changes
  useEffect(() => {
    const audio = new Audio(url);
    audioRef.current = audio;

    const handleCanPlay = () => setIsLoading(false);
    const handleError = () => {
      setError('Failed to load melody. Please try again.');
      setIsLoading(false);
    };
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('canplaythrough', handleCanPlay);
    audio.addEventListener('error', handleError);
    audio.addEventListener('ended', handleEnded);

    setIsLoading(true);
    setIsPlaying(false);
    setError(null);

    return () => {
      audio.removeEventListener('canplaythrough', handleCanPlay);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('ended', handleEnded);
      audio.pause();
      audio.src = '';
    };
  }, [url]);

  const togglePlayback = useCallback(async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      await audio.play();
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const stopPlayback = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.pause();
    audio.currentTime = 0;
    setIsPlaying(false);
  }, []);

  return { togglePlayback, stopPlayback, isPlaying, isLoading, error };
}
