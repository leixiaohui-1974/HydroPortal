// @vitest-environment happy-dom

import React from 'react';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

vi.mock('../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import client from '../api/client';
import { AuthProvider, useAuth } from './useAuth';

function AuthProbe() {
  const { user, loading } = useAuth();

  return (
    <>
      <div data-testid="loading">{String(loading)}</div>
      <div data-testid="user">{user ? JSON.stringify(user) : 'null'}</div>
    </>
  );
}

function renderAuth() {
  return render(
    <AuthProvider>
      <AuthProbe />
    </AuthProvider>
  );
}

describe('AuthProvider bootstrap', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
    cleanup();
  });

  test('skips /auth/me when no token exists', async () => {
    renderAuth();

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    expect(screen.getByTestId('user').textContent).toBe('null');
    expect(client.get).not.toHaveBeenCalled();
  });

  test('clears stale token when /auth/me fails', async () => {
    localStorage.setItem('hydro_token', 'stale-token');
    client.get.mockRejectedValueOnce(new Error('unauthorized'));

    renderAuth();

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    expect(screen.getByTestId('user').textContent).toBe('null');
    expect(client.get).toHaveBeenCalledWith('/auth/me');
    expect(localStorage.getItem('hydro_token')).toBeNull();
  });

  test('loads current user when token is valid', async () => {
    localStorage.setItem('hydro_token', 'valid-token');
    client.get.mockResolvedValueOnce({
      data: { username: 'admin', role: 'admin' },
    });

    renderAuth();

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    expect(client.get).toHaveBeenCalledWith('/auth/me');
    expect(screen.getByTestId('user').textContent).toContain('"username":"admin"');
    expect(localStorage.getItem('hydro_token')).toBe('valid-token');
  });
});
