/**
 * The base URL for API requests.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4050';

/**
 * The WebSocket URL for streaming requests.
 */
export const WS_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4050')
  .replace('http://', 'ws://')
  .replace('https://', 'wss://');

/**
 * Fetches the list of available melody generation models from the API.
 */
export async function fetchModels() {
  const response = await fetch(`${API_URL}/melody/models`);
  if (!response.ok) {
    throw new Error(`Failed to fetch models: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetches the list of available instruments from the API.
 */
export async function fetchInstruments() {
  const response = await fetch(`${API_URL}/melody/instruments`);
  if (!response.ok) {
    throw new Error(`Failed to fetch instruments: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetches available conditions for conditional generation.
 */
export async function fetchConditions() {
  const response = await fetch(`${API_URL}/melody/conditions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch conditions: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Generates a new melody using the specified model and options.
 *
 * @param {string} modelId - The ID of the model to use
 * @param {number} instrument - The General MIDI program number
 * @param {Object} options - Generation options
 */
export async function generateMelody(modelId, instrument = 0, options = {}) {
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
    url: `${API_URL}/melody/download/${audioFile}`,
    midiUrl: `${API_URL}/melody/download/${data.midi_file}`,
  };
}

/**
 * Get the download URL for a file.
 */
export function getDownloadUrl(filename) {
  return `${API_URL}/melody/download/${filename}`;
}

/**
 * Fetches the public melody gallery.
 */
export async function fetchGallery(limit = 20, offset = 0) {
  const response = await fetch(`${API_URL}/melody/gallery?limit=${limit}&offset=${offset}`);
  if (!response.ok) throw new Error('Failed to fetch gallery');
  return response.json();
}
