'use client';

import { useState } from 'react';
import { MelodyGenerator } from '../components/melody/MelodyGenerator';
import { MelodyList } from '../components/melody/MelodyList';
import Gallery from '../components/melody/Gallery';

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <>
      <h1 className="text-2xl font-bold mb-4">AI Melody Generator</h1>
      <MelodyGenerator onGenerated={() => setRefreshKey(k => k + 1)} />
      <MelodyList />
      <h2 className="text-xl font-semibold mt-8 mb-4">Recent Melodies</h2>
      <Gallery refreshKey={refreshKey} />
    </>
  );
}
