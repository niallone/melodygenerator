import { WS_URL } from './api';
import type { StreamingCallbacks, StreamingConnection } from '../types';

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 1000;

export function createStreamingConnection(callbacks: StreamingCallbacks): StreamingConnection {
  let retryCount = 0;
  let ws: WebSocket | null = null;
  let pendingMessage: Record<string, unknown> | null = null;
  let closed = false;

  function connect() {
    ws = new WebSocket(`${WS_URL}/melody/generate/stream`);

    ws.onopen = () => {
      retryCount = 0;
      if (pendingMessage && ws) {
        ws.send(JSON.stringify(pendingMessage));
        pendingMessage = null;
      }
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'generation_started':
            callbacks.onStarted?.(data);
            break;
          case 'note':
            callbacks.onNote?.(data);
            break;
          case 'generation_complete':
            callbacks.onComplete?.(data);
            break;
          case 'error':
            callbacks.onError?.(new Error(data.message));
            break;
          default:
            break;
        }
      } catch (err) {
        callbacks.onError?.(err as Error);
      }
    };

    ws.onerror = () => {
      callbacks.onError?.(new Error('WebSocket connection error'));
    };

    ws.onclose = (event: CloseEvent) => {
      callbacks.onClose?.(event);

      if (!closed && retryCount < MAX_RETRIES && !event.wasClean) {
        retryCount++;
        const delay = BASE_DELAY_MS * Math.pow(2, retryCount - 1);
        setTimeout(() => {
          if (!closed) connect();
        }, delay);
      }
    };
  }

  connect();

  return {
    send: (data: Record<string, unknown>) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
      } else {
        pendingMessage = data;
      }
    },
    close: () => {
      closed = true;
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        ws.close();
      }
    },
    get readyState() {
      return ws ? ws.readyState : WebSocket.CLOSED;
    },
    onReady: (callback: () => void) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        callback();
      } else if (ws) {
        ws.addEventListener('open', callback, { once: true });
      }
    },
  };
}
