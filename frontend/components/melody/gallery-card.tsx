'use client';

import Card from '../common/card';
import { MelodyPlayer } from './melody-player';
import { getDownloadUrl } from '../../utils/api';
import type { GalleryMelody } from '../../types';

function timeAgo(dateString: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateString).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

interface GalleryCardProps {
  melody: GalleryMelody;
  isActive: boolean;
  onPlay: () => void;
}

export default function GalleryCard({ melody, isActive, onPlay }: GalleryCardProps) {
  const audioFile = melody.wav_file || melody.midi_file;
  const url = getDownloadUrl(audioFile);
  const midiUrl = getDownloadUrl(melody.midi_file);

  return (
    <Card className="flex flex-col gap-3 p-4">
      <div className="flex justify-between items-start">
        <div>
          <p className="font-medium text-sm text-white">{melody.instrument_name || 'Piano'}</p>
          <p className="text-xs text-white/50">{melody.model_id}</p>
        </div>
        <span className="text-xs text-white/50">{timeAgo(melody.created)}</span>
      </div>

      <MelodyPlayer url={url} midiUrl={midiUrl} isActive={isActive} onPlay={onPlay} />

      <div className="flex justify-between items-center text-xs text-white/50">
        <span className="tabular-nums">temp {melody.temperature} / {melody.num_notes} notes</span>
        <a href={url} download className="text-indigo-400 hover:underline font-medium">
          Download
        </a>
      </div>
    </Card>
  );
}
