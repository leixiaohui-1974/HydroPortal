import { describe, expect, test } from 'vitest';

import { buildWebSocketUrl } from './useWebSocket';

describe('buildWebSocketUrl', () => {
  test('appends token when missing', () => {
    const url = buildWebSocketUrl('/ws/scada?stations=ST-001', {
      location: { protocol: 'http:', host: 'localhost:3000' },
      token: 'abc123',
    });

    expect(url).toBe('ws://localhost:3000/ws/scada?stations=ST-001&token=abc123');
  });

  test('does not override token when already present', () => {
    const url = buildWebSocketUrl('/ws/scada?token=server-issued&stations=ST-001', {
      location: { protocol: 'https:', host: 'portal.example.com' },
      token: 'local-token',
    });

    expect(url).toBe('wss://portal.example.com/ws/scada?token=server-issued&stations=ST-001');
  });

  test('does not append token to third-party websocket urls', () => {
    const url = buildWebSocketUrl('wss://feeds.example.net/ws/scada?stations=ST-001', {
      location: { protocol: 'https:', host: 'portal.example.com' },
      token: 'local-token',
    });

    expect(url).toBe('wss://feeds.example.net/ws/scada?stations=ST-001');
  });
});
