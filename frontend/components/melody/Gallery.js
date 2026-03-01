'use client';

import { useState, useEffect, useCallback } from 'react';
import GalleryCard from './GalleryCard';
import { fetchGallery } from '../../utils/api';
import LoadingSpinner from '../common/LoadingSpinner';
import Button from '../common/Button';

const PAGE_SIZE = 20;

export default function Gallery({ refreshKey }) {
  const [melodies, setMelodies] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeMelodyId, setActiveMelodyId] = useState(null);

  const loadMelodies = useCallback(async (newOffset = 0, append = false) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchGallery(PAGE_SIZE, newOffset);
      setMelodies(prev => append ? [...prev, ...data.melodies] : data.melodies);
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
    return <p className="text-gray-500">No melodies yet. Generate one above!</p>;
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
