import type { GenerationOptions, Melody, GalleryResponse } from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.melodygenerator.fun';

export const WS_URL = (process.env.NEXT_PUBLIC_API_URL || 'https://api.melodygenerator.fun')
  .replace('http://', 'ws://')
  .replace('https://', 'wss://');

export async function fetchModels() {
  const response = await fetch(`${API_URL}/melody/models`);
  if (!response.ok) {
    throw new Error(`Failed to fetch models: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchInstruments() {
  const response = await fetch(`${API_URL}/melody/instruments`);
  if (!response.ok) {
    throw new Error(`Failed to fetch instruments: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchConditions() {
  const response = await fetch(`${API_URL}/melody/conditions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch conditions: ${response.statusText}`);
  }
  return response.json();
}

export async function generateMelody(
  modelId: string,
  instrument: number = 0,
  options: GenerationOptions = {},
): Promise<Melody> {
  const response = await fetch(`${API_URL}/melody/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model_id: modelId,
      instrument,
      temperature: options.temperature ?? 0.8,
      top_k: options.top_k ?? 50,
      top_p: options.top_p ?? 0.95,
      num_notes: options.num_notes ?? 500,
      seed_midi: options.seed_midi || null,
      key_signature: options.key_signature || null,
      tempo: options.tempo || null,
      style: options.style || null,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate melody: ${response.statusText}`);
  }

  const data = await response.json();
  if (data.error) {
    throw new Error(data.error);
  }

  const audioFile = data.wav_file || data.midi_file;
  return {
    id: Date.now(),
    name: audioFile,
    url: getDownloadUrl(audioFile),
    midiUrl: getDownloadUrl(data.midi_file),
  };
}

export function getDownloadUrl(fileRef: string): string {
  // If already a full URL (R2), use directly; otherwise build API download URL
  if (fileRef.startsWith('http://') || fileRef.startsWith('https://')) {
    return fileRef;
  }
  return `${API_URL}/melody/download/${fileRef}`;
}

export async function fetchGallery(limit: number = 20, offset: number = 0): Promise<GalleryResponse> {
  const response = await fetch(`${API_URL}/melody/gallery?limit=${limit}&offset=${offset}`);
  if (!response.ok) throw new Error('Failed to fetch gallery');
  return response.json();
}
