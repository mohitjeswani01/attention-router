/**
 * WebSocket client for real-time attention queue updates.
 * Placeholder — will be wired to ws://localhost:8000/ws/attention when backend supports it.
 */

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function createAttentionWs(_onMessage: (data: unknown) => void): {
  close: () => void;
} {
  // TODO: implement when backend WebSocket endpoint is available
  return { close: () => {} };
}
