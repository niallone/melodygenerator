'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.melodygenerator.fun';

const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

interface MidiNote {
  pitch: number;
  velocity: number;
  startTick: number;
  endTick: number;
}

interface ParsedMidi {
  ticksPerBeat: number;
  notes: MidiNote[];
}

interface Selection {
  start: number;
  end: number;
}

interface GalleryMelody {
  id: number;
  model_id: string;
  instrument_name: string;
  midi_file: string;
  wav_file: string;
  created: string;
}

// ─── API helpers ───

function downloadUrl(filename: string) {
  return `${API_URL}/melody/download/${filename}`;
}

async function fetchGallery(limit = 30): Promise<{ melodies: GalleryMelody[] }> {
  const res = await fetch(`${API_URL}/melody/gallery?limit=${limit}&offset=0`);
  if (!res.ok) throw new Error('Failed to fetch gallery');
  return res.json();
}

// ─── MIDI parser ───

function parseMidi(buffer: ArrayBuffer): ParsedMidi {
  const view = new DataView(buffer);
  let pos = 0;

  const readU16 = () => { const v = view.getUint16(pos); pos += 2; return v; };
  const readU32 = () => { const v = view.getUint32(pos); pos += 4; return v; };
  const readVarLen = () => {
    let val = 0;
    for (let i = 0; i < 4; i++) {
      const byte = view.getUint8(pos++);
      val = (val << 7) | (byte & 0x7f);
      if (!(byte & 0x80)) break;
    }
    return val;
  };

  if (readU32() !== 0x4d546864) throw new Error('Not a MIDI file');
  readU32(); // header length
  readU16(); // format
  const numTracks = readU16();
  const ticksPerBeat = readU16();

  const notes: MidiNote[] = [];

  for (let t = 0; t < numTracks; t++) {
    if (readU32() !== 0x4d54726b) throw new Error('Bad track header');
    const trackLen = readU32();
    const trackEnd = pos + trackLen;
    let tick = 0;
    let runningStatus = 0;
    const activeNotes = new Map<number, { tick: number; velocity: number }>();

    while (pos < trackEnd) {
      tick += readVarLen();
      let status = view.getUint8(pos);
      if (status < 0x80) {
        status = runningStatus;
      } else {
        pos++;
        if (status >= 0x80 && status < 0xf0) runningStatus = status;
      }

      const type = status & 0xf0;
      if (type === 0x90 || type === 0x80) {
        const pitch = view.getUint8(pos++);
        const velocity = view.getUint8(pos++);
        if (type === 0x90 && velocity > 0) {
          activeNotes.set(pitch, { tick, velocity });
        } else {
          const start = activeNotes.get(pitch);
          if (start) {
            notes.push({ pitch, velocity: start.velocity, startTick: start.tick, endTick: tick });
            activeNotes.delete(pitch);
          }
        }
      } else if (type === 0xb0 || type === 0xa0 || type === 0xe0) {
        pos += 2;
      } else if (type === 0xc0 || type === 0xd0) {
        pos += 1;
      } else if (status === 0xff) {
        view.getUint8(pos++); // meta type
        const len = readVarLen();
        pos += len;
      } else if (status === 0xf0 || status === 0xf7) {
        const len = readVarLen();
        pos += len;
      }
    }

    // Close any unclosed notes
    for (const [pitch, start] of activeNotes) {
      notes.push({ pitch, velocity: start.velocity, startTick: start.tick, endTick: tick });
    }

    pos = trackEnd;
  }

  return { ticksPerBeat, notes };
}

// ─── Piano Roll Component ───

function PianoRoll({
  notes, ticksPerBeat, duration, currentTime, zoom, selection, onSelectionChange,
}: {
  notes: MidiNote[];
  ticksPerBeat: number;
  duration: number;
  currentTime: number;
  zoom: number;
  selection: Selection | null;
  onSelectionChange: (sel: Selection | null) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef<number | null>(null);

  const minPitch = Math.max(0, Math.min(...notes.map((n) => n.pitch)) - 2);
  const maxPitch = Math.min(127, Math.max(...notes.map((n) => n.pitch)) + 2);
  const tickToTime = (tick: number) => tick / ticksPerBeat * 0.5;
  const canvasHeight = Math.max(8 * (maxPitch - minPitch + 1), 300);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    const w = canvas.width;
    const h = canvas.height;
    const pxPerSec = ((w - 48) * zoom) / Math.max(duration, 1);

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#0d0d14';
    ctx.fillRect(0, 0, w, h);

    // Piano keys
    for (let p = minPitch; p <= maxPitch; p++) {
      const y = (maxPitch - p) * 8;
      ctx.fillStyle = [1, 3, 6, 8, 10].includes(p % 12) ? '#111118' : '#16161e';
      ctx.fillRect(0, y, 48, 8);
      ctx.strokeStyle = '#1e1e2a';
      ctx.strokeRect(0, y, 48, 8);
      if (p % 12 === 0) {
        ctx.fillStyle = '#6b7280';
        ctx.font = '9px monospace';
        ctx.fillText(`${NOTE_NAMES[p % 12]}${Math.floor(p / 12) - 1}`, 4, y + 7);
      }
    }

    // Grid lines
    for (let p = minPitch; p <= maxPitch; p++) {
      const y = (maxPitch - p) * 8;
      ctx.strokeStyle = p % 12 === 0 ? '#252530' : '#16161e';
      ctx.beginPath();
      ctx.moveTo(48, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Vertical grid
    for (let t = 0; t < duration; t += 0.5) {
      const x = 48 + t * pxPerSec;
      if (x < 48 || x > w) continue;
      ctx.strokeStyle = '#1a1a28';
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }

    // Selection overlay
    if (selection) {
      const sx = 48 + selection.start * pxPerSec;
      const ex = 48 + selection.end * pxPerSec;
      ctx.fillStyle = 'rgba(139, 92, 246, 0.1)';
      ctx.fillRect(sx, 0, ex - sx, h);
      ctx.strokeStyle = 'rgba(139, 92, 246, 0.4)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(sx, 0); ctx.lineTo(sx, h);
      ctx.moveTo(ex, 0); ctx.lineTo(ex, h);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Notes
    for (const note of notes) {
      const t0 = tickToTime(note.startTick);
      const t1 = tickToTime(note.endTick);
      const x = 48 + t0 * pxPerSec;
      const noteW = Math.max((t1 - t0) * pxPerSec, 2);
      const y = (maxPitch - note.pitch) * 8;
      const alpha = note.velocity / 127;

      if (selection && t0 >= selection.start && t0 < selection.end) {
        ctx.fillStyle = `rgba(139, 92, 246, ${0.4 + 0.6 * alpha})`;
      } else {
        ctx.fillStyle = `rgba(52, 211, 153, ${0.3 + 0.7 * alpha})`;
      }
      ctx.beginPath();
      ctx.roundRect(x, y + 1, noteW, 6, 2);
      ctx.fill();
    }

    // Playhead
    if (currentTime > 0) {
      const px = 48 + currentTime * pxPerSec;
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(px, 0);
      ctx.lineTo(px, h);
      ctx.stroke();
      ctx.lineWidth = 1;
    }
  }, [notes, ticksPerBeat, duration, currentTime, zoom, selection, minPitch, maxPitch]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const ro = new ResizeObserver(() => {
      canvas.width = container.clientWidth;
      canvas.height = canvasHeight;
      draw();
    });
    ro.observe(container);
    return () => ro.disconnect();
  }, [canvasHeight, draw]);

  useEffect(() => { draw(); }, [draw]);

  const xToTime = useCallback((clientX: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return 0;
    const rect = canvas.getBoundingClientRect();
    const x = clientX - rect.left - 48;
    const pxPerSec = ((canvas.width - 48) * zoom) / Math.max(duration, 1);
    return Math.max(0, Math.min(duration, x / pxPerSec));
  }, [zoom, duration]);

  const handleMouseUp = () => setDragging(false);

  return (
    <div
      ref={containerRef}
      className="w-full overflow-x-auto cursor-crosshair"
      style={{ height: `${Math.min(canvasHeight, 400)}px` }}
      onMouseDown={(e) => { dragStart.current = xToTime(e.clientX); setDragging(true); onSelectionChange(null); }}
      onMouseMove={(e) => {
        if (!dragging || dragStart.current === null) return;
        const t = xToTime(e.clientX);
        const start = Math.min(dragStart.current, t);
        const end = Math.max(dragStart.current, t);
        if (end - start > 0.05) onSelectionChange({ start, end });
      }}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <canvas ref={canvasRef} style={{ width: `${100 * zoom}%`, height: `${canvasHeight}px`, minWidth: '100%' }} />
    </div>
  );
}

// ─── Helpers ───

function formatTime(seconds: number) {
  if (!isFinite(seconds)) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function timeAgo(dateStr: string) {
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

// ─── Studio Page ───

export default function StudioPage() {
  const [melodies, setMelodies] = useState<GalleryMelody[]>([]);
  const [selected, setSelected] = useState<GalleryMelody | null>(null);
  const [midi, setMidi] = useState<ParsedMidi | null>(null);
  const [loading, setLoading] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [loopEnabled, setLoopEnabled] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [selection, setSelection] = useState<Selection | null>(null);

  const audioCtxRef = useRef<AudioContext | null>(null);
  const audioBufferRef = useRef<AudioBuffer | null>(null);
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);
  const playStartRef = useRef(0);
  const playOffsetRef = useRef(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    fetchGallery(30)
      .then((data) => setMelodies(data.melodies || []))
      .catch(() => {});
  }, []);

  const stopPlayback = useCallback(() => {
    if (sourceRef.current) {
      try { sourceRef.current.stop(); } catch {}
      sourceRef.current = null;
    }
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
  }, []);

  const loadMelody = useCallback(async (melody: GalleryMelody) => {
    setSelected(melody);
    setPlaying(false);
    stopPlayback();
    setLoading(true);
    setSelection(null);
    setCurrentTime(0);

    try {
      const midiRes = await fetch(downloadUrl(melody.midi_file));
      const midiBuf = await midiRes.arrayBuffer();
      const parsed = parseMidi(midiBuf);
      setMidi(parsed);

      if (!audioCtxRef.current) audioCtxRef.current = new AudioContext();
      const wavRes = await fetch(downloadUrl(melody.wav_file));
      const wavBuf = await wavRes.arrayBuffer();
      audioBufferRef.current = await audioCtxRef.current.decodeAudioData(wavBuf);
      setDuration(audioBufferRef.current.duration);
    } catch (err) {
      console.error('Failed to load melody:', err);
    }
    setLoading(false);
  }, [stopPlayback]);

  const startPlayback = useCallback((fromTime: number) => {
    if (!audioBufferRef.current || !audioCtxRef.current) return;
    stopPlayback();

    const ctx = audioCtxRef.current;
    const source = ctx.createBufferSource();
    source.buffer = audioBufferRef.current;
    source.connect(ctx.destination);

    const useLoop = loopEnabled && selection;
    const startPos = useLoop ? selection!.start : fromTime;
    const endPos = useLoop ? selection!.end : duration;

    if (useLoop) {
      source.loopStart = selection!.start;
      source.loopEnd = selection!.end;
      source.loop = true;
    }

    source.start(0, startPos, useLoop ? undefined : endPos - startPos);
    sourceRef.current = source;
    playStartRef.current = ctx.currentTime;
    playOffsetRef.current = startPos;

    source.onended = () => {
      if (!useLoop) { setPlaying(false); setCurrentTime(0); }
    };

    const tick = () => {
      const elapsed = ctx.currentTime - playStartRef.current;
      let t = playOffsetRef.current + elapsed;
      if (useLoop && t > selection!.end) {
        t = selection!.start + ((t - selection!.start) % (selection!.end - selection!.start));
      }
      setCurrentTime(Math.min(t, duration));
      rafRef.current = requestAnimationFrame(tick);
    };
    tick();
  }, [duration, loopEnabled, selection, stopPlayback]);

  const togglePlay = useCallback(() => {
    if (playing) {
      stopPlayback();
      setPlaying(false);
    } else {
      if (audioCtxRef.current?.state === 'suspended') audioCtxRef.current.resume();
      startPlayback(loopEnabled && selection ? selection.start : currentTime);
      setPlaying(true);
    }
  }, [playing, currentTime, loopEnabled, selection, startPlayback, stopPlayback]);

  // Restart playback when loop toggle changes during play
  useEffect(() => {
    if (playing) startPlayback(loopEnabled && selection ? selection.start : currentTime);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loopEnabled]);

  return (
    <section className="py-20 px-6 sm:px-10">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">Studio</p>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">Melody Explorer</h1>
          <p className="text-white/40 mt-2">Pick a generation and explore it on the piano roll</p>
        </div>

        {/* Melody selector */}
        <div className="mb-6">
          <div className="flex items-center gap-4 mb-3">
            <span className="text-white/50 text-sm font-medium">Recent Generations</span>
            <Link
              href="/"
              className="ml-auto text-xs bg-white text-[#07060b] px-3 py-1.5 rounded font-medium hover:bg-white/90 transition-colors"
            >
              Generate New
            </Link>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
            {melodies.map((m) => (
              <button
                key={m.id}
                onClick={() => loadMelody(m)}
                className={`flex-shrink-0 px-4 py-3 rounded-lg border text-left transition-all text-sm min-w-[160px] ${
                  selected?.id === m.id
                    ? 'bg-indigo-500/10 border-indigo-500/50 text-indigo-300'
                    : 'bg-white/[0.03] border-white/[0.08] text-white/50 hover:border-white/20'
                }`}
              >
                <div className="text-white text-xs font-medium truncate">{m.model_id}</div>
                <div className="text-xs mt-0.5 truncate">{m.instrument_name}</div>
                <div className="text-xs text-white/25 mt-1">{timeAgo(m.created)}</div>
              </button>
            ))}
            {melodies.length === 0 && (
              <div className="text-white/30 text-sm py-4">No melodies yet. Generate one first!</div>
            )}
          </div>
        </div>

        {/* Piano Roll */}
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-[400px] text-white/40">
              <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" />
              </svg>
              Loading…
            </div>
          ) : midi ? (
            <PianoRoll
              notes={midi.notes}
              ticksPerBeat={midi.ticksPerBeat}
              duration={duration}
              currentTime={currentTime}
              zoom={zoom}
              selection={selection}
              onSelectionChange={setSelection}
            />
          ) : (
            <div className="flex items-center justify-center h-[400px] text-white/30 text-sm">
              Select a melody above to view its piano roll
            </div>
          )}
        </div>

        {/* Controls */}
        {midi && (
          <div className="mt-4 flex items-center gap-4 flex-wrap">
            <button
              onClick={togglePlay}
              className="w-10 h-10 rounded-full bg-white text-[#07060b] flex items-center justify-center hover:bg-white/90 transition-colors"
            >
              {playing ? (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="4" width="4" height="16" />
                  <rect x="14" y="4" width="4" height="16" />
                </svg>
              ) : (
                <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              )}
            </button>

            <button
              onClick={() => setLoopEnabled(!loopEnabled)}
              className={`px-3 py-1.5 rounded text-xs font-medium border transition-colors ${
                loopEnabled
                  ? 'bg-violet-500/20 border-violet-500/50 text-violet-300'
                  : 'border-white/10 text-white/40 hover:text-white/60'
              }`}
            >
              Loop{selection ? ' Region' : ''}
            </button>

            <span className="font-mono text-xs text-white/40 tabular-nums">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>

            {selection && (
              <span className="font-mono text-xs text-violet-400 tabular-nums">
                Sel: {formatTime(selection.start)} – {formatTime(selection.end)}
              </span>
            )}

            <div className="flex-1" />

            <div className="flex items-center gap-1">
              <button
                onClick={() => setZoom((z) => Math.max(0.5, z / 1.5))}
                className="w-7 h-7 rounded border border-white/10 text-white/40 flex items-center justify-center hover:text-white text-xs"
              >
                −
              </button>
              <span className="text-xs text-white/30 font-mono w-10 text-center">
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={() => setZoom((z) => Math.min(8, z * 1.5))}
                className="w-7 h-7 rounded border border-white/10 text-white/40 flex items-center justify-center hover:text-white text-xs"
              >
                +
              </button>
            </div>

            <button
              onClick={() => selected && window.open(downloadUrl(selected.midi_file), '_blank')}
              className="px-3 py-1.5 rounded text-xs font-medium border border-white/10 text-white/50 hover:text-white transition-colors"
            >
              Download MIDI
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
