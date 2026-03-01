'use client';

import { useState } from 'react';
import Card from '../common/Card';
import { MelodyPlayer } from './MelodyPlayer';
import { getDownloadUrl } from '../../utils/api';

function timeAgo(dateString) {
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

export default function GalleryCard({ melody, isActive, onPlay }) {
  const audioFile = melody.wav_file || melody.midi_file;
  const url = getDownloadUrl(audioFile);
  const midiUrl = getDownloadUrl(melody.midi_file);

  return (
    <Card className="flex flex-col gap-3 p-4">
      <div className="flex justify-between items-start">
        <div>
          <p className="font-medium text-sm">{melody.instrument_name || 'Piano'}</p>
          <p className="text-xs text-gray-500">{melody.model_id}</p>
        </div>
        <span className="text-xs text-gray-400">{timeAgo(melody.created)}</span>
      </div>

      <MelodyPlayer url={url} midiUrl={midiUrl} isActive={isActive} onPlay={onPlay} />

      <div className="flex justify-between items-center text-xs text-gray-400">
        <span>temp {melody.temperature} / {melody.num_notes} notes</span>
        <a href={url} download className="text-primary hover:underline">
          Download
        </a>
      </div>
    </Card>
  );
}
