import { describe, expect, test, vi } from 'vitest';

import { ACTION, initialState, reducer } from './useAppStore';

describe('useAppStore reducer', () => {
  test('adds a notification with a generated id', () => {
    vi.spyOn(Date, 'now').mockReturnValue(4242);

    const state = reducer(initialState, {
      type: ACTION.ADD_NOTIFICATION,
      payload: { level: 'info', message: 'Saved' },
    });

    expect(state.notifications).toEqual([
      { id: 4242, level: 'info', message: 'Saved' },
    ]);
  });

  test('dismisses a notification by id', () => {
    const state = {
      ...initialState,
      notifications: [
        { id: 1, message: 'Keep' },
        { id: 2, message: 'Remove' },
      ],
    };

    const next = reducer(state, {
      type: ACTION.DISMISS_NOTIFICATION,
      payload: 2,
    });

    expect(next.notifications).toEqual([{ id: 1, message: 'Keep' }]);
  });

  test('merges settings patches without dropping existing keys', () => {
    const next = reducer(initialState, {
      type: ACTION.UPDATE_SETTINGS,
      payload: { theme: 'dark' },
    });

    expect(next.settings).toEqual({
      theme: 'dark',
      language: 'zh-CN',
    });
  });

  test('clears loading flags when alerts and stations are set', () => {
    const loadingState = {
      ...initialState,
      loading: {
        alerts: true,
        stations: true,
      },
    };

    const withAlerts = reducer(loadingState, {
      type: ACTION.SET_ALERTS,
      payload: [{ id: 'alert-1' }],
    });
    const withStations = reducer(withAlerts, {
      type: ACTION.SET_STATIONS,
      payload: [{ id: 'station-1' }],
    });

    expect(withAlerts.loading.alerts).toBe(false);
    expect(withStations.loading.stations).toBe(false);
    expect(withStations.alerts).toEqual([{ id: 'alert-1' }]);
    expect(withStations.stations).toEqual([{ id: 'station-1' }]);
  });

  test('resets state on logout', () => {
    const dirtyState = {
      user: { username: 'admin' },
      alerts: [{ id: 'alert-1' }],
      stations: [{ id: 'station-1' }],
      notifications: [{ id: 1, message: 'Saved' }],
      settings: { theme: 'dark', language: 'en-US' },
      loading: { alerts: true, stations: true },
      error: 'boom',
    };

    expect(reducer(dirtyState, { type: ACTION.LOGOUT })).toEqual(initialState);
  });
});
