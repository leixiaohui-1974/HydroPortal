// @vitest-environment happy-dom

import React from 'react';
import { act, cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import useWebSocket, { buildWebSocketUrl } from './useWebSocket';

class MockWebSocket {
  static OPEN = 1;
  static instances = [];

  constructor(url) {
    this.url = url;
    this.readyState = MockWebSocket.OPEN;
    this.close = vi.fn(() => {
      this.readyState = 3;
      if (this.onclose) {
        this.onclose();
      }
    });
    this.send = vi.fn();
    this.onopen = null;
    this.onclose = null;
    this.onerror = null;
    this.onmessage = null;
    MockWebSocket.instances.push(this);
  }
}

function WebSocketProbe({ url, enabled }) {
  const { connected } = useWebSocket(url, { enabled });
  return React.createElement('div', { 'data-testid': 'connected' }, String(connected));
}

describe('useWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.useFakeTimers();
    vi.stubGlobal('WebSocket', MockWebSocket);
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  test('does not reconnect after the hook is disabled', () => {
    const view = render(React.createElement(WebSocketProbe, { url: '/ws/scada', enabled: true }));

    expect(MockWebSocket.instances).toHaveLength(1);

    act(() => {
      MockWebSocket.instances[0].onclose();
    });

    view.rerender(React.createElement(WebSocketProbe, { url: '/ws/scada', enabled: false }));

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(MockWebSocket.instances).toHaveLength(1);
    expect(screen.getByTestId('connected').textContent).toBe('false');
  });
});

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
