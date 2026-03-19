// @vitest-environment happy-dom

import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
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
  const { user, loading, login, logout } = useAuth();
  const [result, setResult] = React.useState(null);

  return (
    <>
      <div data-testid="loading">{String(loading)}</div>
      <div data-testid="user">{user ? JSON.stringify(user) : 'null'}</div>
      <div data-testid="result">{result ? JSON.stringify(result) : 'null'}</div>
      <button
        type="button"
        onClick={async () => {
          const nextUser = await login('demo', 'demo-password');
          setResult(nextUser);
        }}
      >
        login
      </button>
      <button type="button" onClick={logout}>
        logout
      </button>
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

  test('login stores the token and populates the current user', async () => {
    client.post.mockResolvedValueOnce({
      data: { access_token: 'fresh-token' },
    });
    client.get.mockResolvedValueOnce({
      data: { username: 'demo', role: 'operator' },
    });

    renderAuth();

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    fireEvent.click(screen.getByRole('button', { name: 'login' }));

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toContain('"username":"demo"');
    });

    expect(client.post).toHaveBeenCalledWith('/auth/login', {
      username: 'demo',
      password: 'demo-password',
    });
    expect(client.get).toHaveBeenCalledWith('/auth/me');
    expect(screen.getByTestId('result').textContent).toContain('"role":"operator"');
    expect(localStorage.getItem('hydro_token')).toBe('fresh-token');
  });

  test('logout clears the token and resets the current user', async () => {
    localStorage.setItem('hydro_token', 'valid-token');
    client.get.mockResolvedValueOnce({
      data: { username: 'admin', role: 'admin' },
    });

    renderAuth();

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toContain('"username":"admin"');
    });

    fireEvent.click(screen.getByRole('button', { name: 'logout' }));

    expect(screen.getByTestId('user').textContent).toBe('null');
    expect(localStorage.getItem('hydro_token')).toBeNull();
  });
});
