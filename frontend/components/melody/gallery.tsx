'use client';

import { useState, useEffect, useCallback } from 'react';
import GalleryCard from './gallery-card';
import { fetchGallery } from '../../utils/api';
import LoadingSpinner from '../common/loading-spinner';
import Button from '../common/button';
import type { GalleryMelody } from '../../types';

const PAGE_SIZE = 20;

interface GalleryProps {
  refreshKey: number;
}

export default function Gallery({ refreshKey }: GalleryProps) {
  const [melodies, setMelodies] = useState<GalleryMelody[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeMelodyId, setActiveMelodyId] = useState<number | null>(null);

  const loadMelodies = useCallback(async (newOffset: number = 0, append: boolean = false) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchGallery(PAGE_SIZE, newOffset);
      setMelodies((prev) => (append ? [...prev, ...data.melodies] : data.melodies));
      setTotal(data.total);
      setOffset(newOffset);
    } catch {
      setError('Failed to load gallery.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMelodies(0, false);
  }, [refreshKey, loadMelodies]);

  const handleLoadMore = () => {
    loadMelodies(offset + PAGE_SIZE, true);
  };

  const hasMore = offset + PAGE_SIZE < total;

  if (isLoading && melodies.length === 0) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  if (error && melodies.length === 0) {
    return <p className="text-error">{error}</p>;
  }

  if (melodies.length === 0) {
    return <p className="text-text-secondary dark:text-dark-text-secondary">No melodies yet. Generate one above!</p>;
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {melodies.map((melody) => (
          <GalleryCard
            key={melody.id}
            melody={melody}
            isActive={activeMelodyId === melody.id}
            onPlay={() => setActiveMelodyId(melody.id)}
          />
        ))}
      </div>
      {hasMore && (
        <div className="flex justify-center mt-6">
          <Button onClick={handleLoadMore} disabled={isLoading}>
            {isLoading ? <LoadingSpinner /> : 'Load More'}
          </Button>
        </div>
      )}
    </div>
  );
}
