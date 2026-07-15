type MessageHandler = (data: unknown) => void;

export class SocketClient {
  private socket: WebSocket | null = null;
  private readonly url: string;
  private readonly handlers = new Set<MessageHandler>();
  private reconnectDelay = 1000;
  private closedByUser = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(url: string) {
    this.url = url;
  }

  connect(): void {
    this.closedByUser = false;
    this.open();
  }

  private open(): void {
    const socket = new WebSocket(this.url);
    this.socket = socket;

    socket.onopen = () => {
      this.reconnectDelay = 1000;
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handlers.forEach((handler) => handler(data));
      } catch {
        // Ignore malformed messages.
      }
    };

    socket.onclose = () => {
      if (this.closedByUser) {
        return;
      }

      this.reconnectTimer = setTimeout(() => this.open(), this.reconnectDelay);
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 15000);
    };
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.add(handler);

    return () => {
      this.handlers.delete(handler);
    };
  }

  close(): void {
    this.closedByUser = true;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    const socket = this.socket;
    this.socket = null;

    if (!socket) {
      return;
    }

    if (socket.readyState === WebSocket.CONNECTING) {
      socket.onopen = () => socket.close(1000, "Client closing");
      socket.onerror = () => {
        /* ignore */
      };
      return;
    }

    if (socket.readyState === WebSocket.OPEN) {
      socket.close(1000, "Client closing");
    }
  }
}