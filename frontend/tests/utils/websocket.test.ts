import { describe, it, expect, vi, beforeEach } from 'vitest';

interface MockListener {
  handler: () => void;
  once: boolean;
}

let mockInstances: MockWebSocket[];

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  CONNECTING = MockWebSocket.CONNECTING;
  OPEN = MockWebSocket.OPEN;
  CLOSING = MockWebSocket.CLOSING;
  CLOSED = MockWebSocket.CLOSED;

  url: string;
  readyState: number;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  _listeners: Record<string, MockListener[]> = {};
  send = vi.fn();
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    this.readyState = MockWebSocket.CONNECTING;
    mockInstances.push(this);
  }

  addEventListener(event: string, handler: () => void, options?: { once?: boolean }) {
    if (!this._listeners[event]) {
      this._listeners[event] = [];
    }
    this._listeners[event].push({ handler, once: options?.once ?? false });
  }

  removeEventListener(event: string, handler: () => void) {
    if (this._listeners[event]) {
      this._listeners[event] = this._listeners[event].filter((l) => l.handler !== handler);
    }
  }

  _simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) this.onopen();
    if (this._listeners['open']) {
      for (const listener of this._listeners['open']) {
        listener.handler();
      }
      this._listeners['open'] = this._listeners['open'].filter((l) => !l.once);
    }
  }

  _simulateMessage(data: Record<string, unknown>) {
    const event = { data: JSON.stringify(data) };
    if (this.onmessage) this.onmessage(event);
  }
}

beforeEach(() => {
  mockInstances = [];
  vi.stubGlobal('WebSocket', MockWebSocket);
  vi.resetModules();
});

async function loadWebsocket() {
  return import('../../utils/websocket');
}

describe('createStreamingConnection', () => {
  it('creates WebSocket with correct URL', async () => {
    const { createStreamingConnection } = await loadWebsocket();
    createStreamingConnection({});

    expect(mockInstances).toHaveLength(1);
    expect(mockInstances[0].url).toBe('ws://localhost:4050/melody/generate/stream');
  });

  it('dispatches generation_started to onStarted callback', async () => {
    const { createStreamingConnection } = await loadWebsocket();
    const onStarted = vi.fn();
    createStreamingConnection({ onStarted });

    const ws = mockInstances[0];
    ws._simulateMessage({ type: 'generation_started', total_notes: 100 });

    expect(onStarted).toHaveBeenCalledWith({ type: 'generation_started', total_notes: 100 });
  });

  it('dispatches note events to onNote callback', async () => {
    const { createStreamingConnection } = await loadWebsocket();
    const onNote = vi.fn();
    createStreamingConnection({ onNote });

    const ws = mockInstances[0];
    const noteData = { type: 'note', pitch: 60, duration: 0.5 };
    ws._simulateMessage(noteData);

    expect(onNote).toHaveBeenCalledWith(noteData);
  });

  it('dispatches generation_complete to onComplete callback', async () => {
    const { createStreamingConnection } = await loadWebsocket();
    const onComplete = vi.fn();
    createStreamingConnection({ onComplete });

    const ws = mockInstances[0];
    const completeData = { type: 'generation_complete', midi_file: 'melody.mid' };
    ws._simulateMessage(completeData);

    expect(onComplete).toHaveBeenCalledWith(completeData);
  });

  it('dispatches error messages to onError callback', async () => {
    const { createStreamingConnection } = await loadWebsocket();
    const onError = vi.fn();
    createStreamingConnection({ onError });

    const ws = mockInstances[0];
    ws._simulateMessage({ type: 'error', message: 'Something went wrong' });

    expect(onError).toHaveBeenCalledWith(expect.any(Error));
    expect(onError.mock.calls[0][0].message).toBe('Something went wrong');
  });
});
