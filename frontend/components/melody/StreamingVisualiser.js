'use client';

import { useEffect, useRef, memo } from 'react';

/**
 * Incremental canvas-based piano roll visualiser for streaming note events.
 * Only draws new notes since last render and auto-scrolls.
 */
const StreamingVisualiser = memo(function StreamingVisualiser({ notes }) {
  const canvasRef = useRef(null);
  const drawnCountRef = useRef(0);
  const scrollOffsetRef = useRef(0);

  // Reset when notes array is cleared
  useEffect(() => {
    if (!notes || notes.length === 0) {
      drawnCountRef.current = 0;
      scrollOffsetRef.current = 0;
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#333333';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }
    }
  }, [notes?.length === 0]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !notes || notes.length === 0) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    const noteHeight = 3;
    const pixelsPerBeat = 20;
    const minPitch = 21;
    const maxPitch = 108;
    const pitchRange = maxPitch - minPitch;

    const lastNote = notes[notes.length - 1];
    const totalWidth = (lastNote.offset + (lastNote.duration || 0.5)) * pixelsPerBeat;
    const newScrollOffset = Math.max(0, totalWidth - width + 50);

    // If scroll changed, need full redraw
    if (newScrollOffset !== scrollOffsetRef.current) {
      scrollOffsetRef.current = newScrollOffset;
      drawnCountRef.current = 0;

      ctx.fillStyle = '#333333';
      ctx.fillRect(0, 0, width, height);
    }

    const scrollOffset = scrollOffsetRef.current;
    const startIdx = drawnCountRef.current;

    // Draw only new notes
    for (let i = startIdx; i < notes.length; i++) {
      const note = notes[i];
      const x = note.offset * pixelsPerBeat - scrollOffset;
      const noteWidth = Math.max(2, (note.duration || 0.5) * pixelsPerBeat);
      const y = height - ((note.pitch - minPitch) / pitchRange) * height;

      if (x + noteWidth < 0 || x > width) continue;

      ctx.fillStyle = `hsl(${note.pitch * 2}, 100%, 50%)`;
      ctx.fillRect(x, y - noteHeight / 2, noteWidth, noteHeight);
    }

    drawnCountRef.current = notes.length;

    // Draw playhead
    if (notes.length > 0) {
      const playheadX = lastNote.offset * pixelsPerBeat - scrollOffset;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(playheadX, 0);
      ctx.lineTo(playheadX, height);
      ctx.stroke();
    }
  }, [notes]);

  return (
    <div className="mt-4">
      <canvas
        ref={canvasRef}
        width={600}
        height={200}
        style={{ width: '100%', height: 'auto', borderRadius: '4px' }}
        aria-label="Streaming melody visualisation"
      />
    </div>
  );
});

export default StreamingVisualiser;
