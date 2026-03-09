'use client';

import { useEffect, useRef } from 'react';
import { Midi } from '@tonejs/midi';

interface MelodyVisualiserProps {
  midiUrl: string;
}

export default function MelodyVisualiser({ midiUrl }: MelodyVisualiserProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const loadAndVisualiseMidi = async () => {
      const response = await fetch(midiUrl);
      const arrayBuffer = await response.arrayBuffer();
      const midi = new Midi(arrayBuffer);

      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      canvas.width = 600;
      canvas.height = 200;

      ctx.fillStyle = '#333333';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const noteHeight = 2;
      const pixelsPerTick = canvas.width / midi.durationTicks;

      midi.tracks.forEach((track) => {
        track.notes.forEach((note) => {
          const x = note.ticks * pixelsPerTick;
          const y = canvas.height - (note.midi - 21) * noteHeight;
          const width = note.durationTicks * pixelsPerTick;

          ctx.fillStyle = `hsl(${note.midi * 2}, 100%, 50%)`;
          ctx.fillRect(x, y, width, noteHeight);
        });
      });
    };

    loadAndVisualiseMidi();
  }, [midiUrl]);

  return (
    <div className="melody-visualiser">
      <canvas ref={canvasRef} style={{ width: '100%', height: 'auto' }} />
    </div>
  );
}
