'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useMelodyContext } from '../context/melody-context';
import { createStreamingConnection } from '../utils/websocket';
import { getDownloadUrl } from '../utils/api';
import type { NoteEvent, GenerationOptions, StreamingConnection } from '../types';

export function useStreamingGeneration() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [progress, setProgress] = useState(0);
  const [totalNotes, setTotalNotes] = useState(0);
  const [notes, setNotes] = useState<NoteEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { addMelody } = useMelodyContext();
  const connectionRef = useRef<StreamingConnection | null>(null);
  const synthRef = useRef<{ dispose?: () => void; triggerAttackRelease: (freq: number, dur: number) => void } | null>(null);
  const noteBufferRef = useRef<NoteEvent[]>([]);
  const playbackStartedRef = useRef(false);

  useEffect(() => {
    return () => {
      if (connectionRef.current) {
        connectionRef.current.close();
        connectionRef.current = null;
      }
      if (synthRef.current) {
        synthRef.current.dispose?.();
        synthRef.current = null;
      }
    };
  }, []);

  const initSynth = useCallback(async () => {
    if (synthRef.current) return;
    try {
      const Tone = await import('tone');
      await Tone.start();
      const synth = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'triangle' },
        envelope: { attack: 0.02, decay: 0.1, sustain: 0.3, release: 0.5 },
      }).toDestination();
      synth.maxPolyphony = 8;
      synthRef.current = synth;
    } catch (err) {
      console.error('Failed to init Tone.js:', err);
    }
  }, []);

  const playNote = useCallback(async (noteEvent: NoteEvent) => {
    const synth = synthRef.current;
    if (!synth) return;
    try {
      const Tone = await import('tone');
      const freq = Tone.Frequency(noteEvent.pitch, 'midi').toFrequency();
      const duration = noteEvent.duration || 0.5;
      synth.triggerAttackRelease(freq, duration);
    } catch {
      // Ignore playback errors
    }
  }, []);

  const processBuffer = useCallback(() => {
    if (!playbackStartedRef.current && noteBufferRef.current.length >= 5) {
      playbackStartedRef.current = true;
    }
    if (playbackStartedRef.current) {
      while (noteBufferRef.current.length > 0) {
        const note = noteBufferRef.current.shift()!;
        playNote(note);
      }
    }
  }, [playNote]);

  const start = useCallback(
    async (modelId: string, instrument: number, options: GenerationOptions = {}) => {
      setIsStreaming(true);
      setProgress(0);
      setTotalNotes(0);
      setNotes([]);
      setError(null);
      noteBufferRef.current = [];
      playbackStartedRef.current = false;

      await initSynth();

      const connection = createStreamingConnection({
        onStarted: (data) => {
          setTotalNotes(data.total_notes);
        },
        onNote: (noteEvent) => {
          setProgress((p) => p + 1);
          setNotes((prev) => [...prev, noteEvent]);
          noteBufferRef.current.push(noteEvent);
          processBuffer();
        },
        onComplete: (data) => {
          playbackStartedRef.current = true;
          processBuffer();

          setIsStreaming(false);
          const audioFile = data.wav_file || data.midi_file;
          if (audioFile) {
            addMelody({
              id: Date.now(),
              name: audioFile,
              url: getDownloadUrl(audioFile),
              midiUrl: data.midi_file ? getDownloadUrl(data.midi_file) : undefined,
            });
          }
        },
        onError: (err) => {
          setError(err.message || 'Streaming generation failed');
          setIsStreaming(false);
        },
        onClose: () => {
          if (connectionRef.current) {
            setIsStreaming(false);
          }
        },
      });

      connectionRef.current = connection;

      connection.onReady(() => {
        connection.send({
          type: 'start_generation',
          model_id: modelId,
          instrument,
          temperature: options.temperature ?? 0.8,
          top_k: options.top_k ?? 50,
          top_p: options.top_p ?? 0.95,
          num_notes: options.num_notes ?? 500,
          key_signature: options.key_signature || null,
          tempo: options.tempo || null,
          style: options.style || null,
        });
      });
    },
    [initSynth, processBuffer, addMelody],
  );

  const stop = useCallback(() => {
    if (connectionRef.current) {
      connectionRef.current.close();
      connectionRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  return {
    start,
    stop,
    isStreaming,
    progress,
    totalNotes,
    notes,
    error,
  };
}
