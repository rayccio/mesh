import { Message } from '../types';

type MessageHandler = (message: Message) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private handlers: MessageHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnect = 5;

  connect(baseUrl: string) {
    // baseUrl should be the backend base (e.g., http://161.97.183.40:8000)
    let wsUrl: string;
    try {
      // Convert http(s) to ws(s) and append /ws
      const url = new URL(baseUrl);
      const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${url.host}/ws`;
      new URL(wsUrl); // validate
    } catch (e) {
      console.error(`Invalid WebSocket base URL: ${baseUrl}. WebSocket disabled.`);
      return;
    }

    if (this.socket && this.socket.readyState === WebSocket.OPEN) return;
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handlers.forEach(handler => handler(data));
      } catch (err) {
        console.error('Failed to parse WebSocket message', err);
      }
    };

    this.socket.onclose = () => {
      console.log('WebSocket disconnected');
      this.socket = null;
      if (this.reconnectAttempts < this.maxReconnect) {
        this.reconnectAttempts++;
        setTimeout(() => this.connect(baseUrl), 2000 * this.reconnectAttempts);
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error', error);
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  addHandler(handler: MessageHandler) {
    this.handlers.push(handler);
  }

  removeHandler(handler: MessageHandler) {
    this.handlers = this.handlers.filter(h => h !== handler);
  }
}

export const wsService = new WebSocketService();
