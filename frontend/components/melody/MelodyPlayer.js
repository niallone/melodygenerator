'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import Button from '../common/Button';

export function MelodyPlayer({ url, midiUrl, isActive, onPlay }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    setError(null);
  }, [url]);

  useEffect(() => {
    if (!isActive && isPlaying && audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  }, [isActive, isPlaying]);

  const handlePlayPause = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      if (!isActive) onPlay();
      audio.play().then(() => setIsPlaying(true)).catch(e => {
        setError('Playback failed. Try downloading instead.');
        console.error('Playback error:', e);
      });
    }
  }, [isPlaying, isActive, onPlay]);

  const handleTimeUpdate = useCallback(() => {
    if (audioRef.current) setCurrentTime(audioRef.current.currentTime);
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    if (audioRef.current) setDuration(audioRef.current.duration);
  }, []);

  const handleEnded = useCallback(() => {
    setIsPlaying(false);
    setCurrentTime(0);
  }, []);

  const handleSeek = useCallback((e) => {
    const audio = audioRef.current;
    if (!audio || !duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.touches ? e.touches[0].clientX - rect.left : e.clientX - rect.left;
    const pct = Math.max(0, Math.min(1, x / rect.width));
    audio.currentTime = pct * duration;
    setCurrentTime(audio.currentTime);
  }, [duration]);

  const formatTime = (t) => {
    if (!t || !isFinite(t)) return '0:00';
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const progress = duration ? (currentTime / duration) * 100 : 0;

  return (
    <div className="w-full">
      <audio
        ref={audioRef}
        src={url}
        preload="metadata"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
        onError={() => setError('Failed to load audio.')}
      />

      {error ? (
        <p className="text-error text-sm text-center">{error}</p>
      ) : (
        <div className="flex flex-col gap-2">
          {/* Play button + time */}
          <div className="flex items-center gap-3">
            <button
              onClick={handlePlayPause}
              className="w-10 h-10 flex items-center justify-center rounded-full bg-primary text-white flex-shrink-0 hover:opacity-90 active:scale-95 transition-transform"
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <svg width="14" height="16" viewBox="0 0 14 16" fill="currentColor">
                  <rect x="1" y="1" width="4" height="14" rx="1" />
                  <rect x="9" y="1" width="4" height="14" rx="1" />
                </svg>
              ) : (
                <svg width="14" height="16" viewBox="0 0 14 16" fill="currentColor">
                  <path d="M2 1.5v13l11-6.5z" />
                </svg>
              )}
            </button>

            {/* Progress bar */}
            <div
              className="flex-1 h-8 flex items-center cursor-pointer touch-none"
              onClick={handleSeek}
              onTouchStart={handleSeek}
            >
              <div className="w-full h-2 bg-light-gray rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-100"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            <span className="text-xs text-dark-gray flex-shrink-0 w-12 text-right">
              {formatTime(currentTime)}/{formatTime(duration)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
