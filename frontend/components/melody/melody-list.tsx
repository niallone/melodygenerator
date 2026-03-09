'use client';

import { useState } from 'react';
import { useMelodyContext } from '../../context/melody-context';
import { MelodyPlayer } from './melody-player';
import Card from '../common/card';

export function MelodyList() {
  const { melodies } = useMelodyContext();
  const [activeMelodyId, setActiveMelodyId] = useState<number | null>(null);

  if (melodies.length === 0) {
    return (
      <p className="text-white/50">
        No melodies generated yet. Click the button to create one!<br />
        It may take 1 - 2 minutes to generate.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {melodies.map((melody) => (
        <Card key={melody.id} className="flex flex-col items-center p-6 animate-fade-in-up">
          <h3 className="mb-4 text-sm font-medium text-white">{melody.name}</h3>
          <MelodyPlayer
            url={melody.url}
            midiUrl={melody.midiUrl}
            isActive={activeMelodyId === melody.id}
            onPlay={() => setActiveMelodyId(melody.id)}
          />
          <a
            href={melody.url}
            download
            className="mt-4 text-sm text-indigo-400 hover:underline font-medium"
          >
            Download
          </a>
        </Card>
      ))}
    </div>
  );
}
