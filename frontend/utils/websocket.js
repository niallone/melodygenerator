import { WS_URL } from './api';

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 1000;

/**
 * Create a WebSocket connection for streaming melody generation
 * with exponential backoff reconnection.
 *
 * @param {Object} callbacks
 * @param {Function} callbacks.onStarted - Called when generation starts
 * @param {Function} callbacks.onNote - Called for each note event
 * @param {Function} callbacks.onComplete - Called when generation finishes
 * @param {Function} callbacks.onError - Called on error
 * @param {Function} [callbacks.onClose] - Called when connection closes
 * @returns {Object} { send, close, onReady, readyState }
 */
export function createStreamingConnection(callbacks) {
  let retryCount = 0;
  let ws = null;
  let pendingMessage = null;
  let closed = false;

  function connect() {
    ws = new WebSocket(`${WS_URL}/melody/generate/stream`);

    ws.onopen = () => {
      retryCount = 0;
      if (pendingMessage) {
        ws.send(JSON.stringify(pendingMessage));
        pendingMessage = null;
      }
    };

    ws.onmessage = (event) => {
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
        callbacks.onError?.(err);
      }
    };

    ws.onerror = () => {
      callbacks.onError?.(new Error('WebSocket connection error'));
    };

    ws.onclose = (event) => {
      callbacks.onClose?.(event);

      // Attempt reconnection if not intentionally closed and retries remaining
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
    send: (data) => {
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
    onReady: (callback) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        callback();
      } else if (ws) {
        ws.addEventListener('open', callback, { once: true });
      }
    },
  };
}
