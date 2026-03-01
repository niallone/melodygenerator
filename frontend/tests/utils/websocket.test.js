import { describe, it, expect, vi, beforeEach } from 'vitest';

// In-memory mock WebSocket instances for inspection
let mockInstances;

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(url) {
    this.url = url;
    this.readyState = MockWebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onerror = null;
    this.onclose = null;
    this._listeners = {};
    this.send = vi.fn();
    this.close = vi.fn();
    mockInstances.push(this);
  }

  addEventListener(event, handler, options) {
    if (!this._listeners[event]) {
      this._listeners[event] = [];
    }
    this._listeners[event].push({ handler, once: options?.once ?? false });
  }

  removeEventListener(event, handler) {
    if (this._listeners[event]) {
      this._listeners[event] = this._listeners[event].filter((l) => l.handler !== handler);
    }
  }

  // Helper to simulate the server opening the connection
  _simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) this.onopen();
    if (this._listeners['open']) {
      for (const listener of this._listeners['open']) {
        listener.handler();
      }
      // Remove once listeners
      this._listeners['open'] = this._listeners['open'].filter((l) => !l.once);
    }
  }

  // Helper to simulate receiving a message from the server
  _simulateMessage(data) {
    const event = { data: JSON.stringify(data) };
    if (this.onmessage) this.onmessage(event);
  }
}

// Assign static properties accessible via instances too
MockWebSocket.prototype.CONNECTING = MockWebSocket.CONNECTING;
MockWebSocket.prototype.OPEN = MockWebSocket.OPEN;
MockWebSocket.prototype.CLOSING = MockWebSocket.CLOSING;
MockWebSocket.prototype.CLOSED = MockWebSocket.CLOSED;

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
