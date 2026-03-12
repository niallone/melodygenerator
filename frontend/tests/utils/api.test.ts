import { describe, it, expect, vi, beforeEach } from 'vitest';

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

async function loadApi() {
  vi.resetModules();
  return import('../../utils/api');
}

describe('fetchModels', () => {
  it('calls the correct URL', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([{ id: 'model-1', name: 'Test Model' }]),
    });

    const { fetchModels } = await loadApi();
    await fetchModels();

    expect(fetchMock).toHaveBeenCalledWith('https://api.melodygenerator.fun/melody/models');
  });
});

describe('fetchInstruments', () => {
  it('calls the correct URL', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([{ id: 0, name: 'Piano' }]),
    });

    const { fetchInstruments } = await loadApi();
    await fetchInstruments();

    expect(fetchMock).toHaveBeenCalledWith('https://api.melodygenerator.fun/melody/instruments');
  });
});

describe('generateMelody', () => {
  it('sends correct payload', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          midi_file: 'melody_123.mid',
          wav_file: 'melody_123.wav',
        }),
    });

    const { generateMelody } = await loadApi();
    await generateMelody('model-1', 0, {
      temperature: 1.0,
      top_k: 40,
      top_p: 0.9,
      num_notes: 200,
    });

    expect(fetchMock).toHaveBeenCalledWith('https://api.melodygenerator.fun/melody/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model_id: 'model-1',
        instrument: 0,
        temperature: 1.0,
        top_k: 40,
        top_p: 0.9,
        num_notes: 200,
        seed_midi: null,
        key_signature: null,
        tempo: null,
        style: null,
      }),
    });
  });
});

describe('getDownloadUrl', () => {
  it('returns correct URL format for filename', async () => {
    const { getDownloadUrl } = await loadApi();
    const url = getDownloadUrl('melody_123.wav');

    expect(url).toBe('https://api.melodygenerator.fun/melody/download/melody_123.wav');
  });

  it('returns full URL as-is for R2 URLs', async () => {
    const { getDownloadUrl } = await loadApi();
    const r2Url = 'https://files.melodygenerator.fun/melody_123.wav';
    const url = getDownloadUrl(r2Url);

    expect(url).toBe(r2Url);
  });
});
