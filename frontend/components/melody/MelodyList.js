'use client';

import { useState } from 'react';
import { useMelodyContext } from '../../context/MelodyContext';
import { MelodyPlayer } from './MelodyPlayer';
import Card from '../common/Card';

export function MelodyList() {
  const { melodies } = useMelodyContext();
  const [activeMelodyId, setActiveMelodyId] = useState(null);

  if (melodies.length === 0) {
    return (
      <p>
        No melodies generated yet. Click the button to create one!<br />
        It may take 1 - 2 minutes to generate.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      {melodies.map((melody) => (
        <Card key={melody.id} className="flex flex-col items-center p-6">
          <h3 className="mb-4">{melody.name}</h3>
          <MelodyPlayer
            url={melody.url}
            midiUrl={melody.midiUrl}
            isActive={activeMelodyId === melody.id}
            onPlay={() => setActiveMelodyId(melody.id)}
          />
          <a
            href={melody.url}
            download
            className="mt-4 text-primary no-underline hover:underline"
          >
            Download
          </a>
        </Card>
      ))}
    </div>
  );
}
