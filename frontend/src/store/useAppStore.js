import React, { createContext, useContext, useReducer, useCallback } from 'react';
import client from '../api/client';

// ---------------------------------------------------------------------------
// State shape
// ---------------------------------------------------------------------------

const initialState = {
  user: null,
  alerts: [],
  stations: [],
  notifications: [],
  settings: {
    theme: 'light',
    language: 'zh-CN',
  },
  loading: {
    alerts: false,
    stations: false,
  },
  error: null,
};

// ---------------------------------------------------------------------------
// Reducer
// ---------------------------------------------------------------------------

const ACTION = {
  SET_USER: 'SET_USER',
  SET_ALERTS: 'SET_ALERTS',
  SET_STATIONS: 'SET_STATIONS',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  DISMISS_NOTIFICATION: 'DISMISS_NOTIFICATION',
  UPDATE_SETTINGS: 'UPDATE_SETTINGS',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  LOGOUT: 'LOGOUT',
};

function reducer(state, action) {
  switch (action.type) {
    case ACTION.SET_USER:
      return { ...state, user: action.payload };
    case ACTION.SET_ALERTS:
      return { ...state, alerts: action.payload, loading: { ...state.loading, alerts: false } };
    case ACTION.SET_STATIONS:
      return { ...state, stations: action.payload, loading: { ...state.loading, stations: false } };
    case ACTION.ADD_NOTIFICATION:
      return {
        ...state,
        notifications: [
          ...state.notifications,
          { id: Date.now(), ...action.payload },
        ],
      };
    case ACTION.DISMISS_NOTIFICATION:
      return {
        ...state,
        notifications: state.notifications.filter((n) => n.id !== action.payload),
      };
    case ACTION.UPDATE_SETTINGS:
      return { ...state, settings: { ...state.settings, ...action.payload } };
    case ACTION.SET_LOADING:
      return { ...state, loading: { ...state.loading, ...action.payload } };
    case ACTION.SET_ERROR:
      return { ...state, error: action.payload };
    case ACTION.LOGOUT:
      return { ...initialState };
    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Context + Provider
// ---------------------------------------------------------------------------

const AppStoreContext = createContext(null);

export function AppStoreProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // --- Actions ---------------------------------------------------------------

  const login = useCallback(async (username, password) => {
    try {
      const res = await client.post('/auth/login', { username, password });
      const { access_token } = res.data;
      localStorage.setItem('hydro_token', access_token);
      const me = await client.get('/auth/me');
      dispatch({ type: ACTION.SET_USER, payload: me.data });
      return me.data;
    } catch (err) {
      dispatch({ type: ACTION.SET_ERROR, payload: err.message });
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('hydro_token');
    dispatch({ type: ACTION.LOGOUT });
  }, []);

  const fetchAlerts = useCallback(async () => {
    dispatch({ type: ACTION.SET_LOADING, payload: { alerts: true } });
    try {
      const res = await client.get('/guard/alerts');
      dispatch({ type: ACTION.SET_ALERTS, payload: res.data });
    } catch (err) {
      dispatch({ type: ACTION.SET_ERROR, payload: err.message });
      dispatch({ type: ACTION.SET_LOADING, payload: { alerts: false } });
    }
  }, []);

  const fetchStations = useCallback(async () => {
    dispatch({ type: ACTION.SET_LOADING, payload: { stations: true } });
    try {
      const res = await client.get('/guard/stations');
      dispatch({ type: ACTION.SET_STATIONS, payload: res.data });
    } catch (err) {
      dispatch({ type: ACTION.SET_ERROR, payload: err.message });
      dispatch({ type: ACTION.SET_LOADING, payload: { stations: false } });
    }
  }, []);

  const addNotification = useCallback((notification) => {
    dispatch({ type: ACTION.ADD_NOTIFICATION, payload: notification });
  }, []);

  const dismissNotification = useCallback((id) => {
    dispatch({ type: ACTION.DISMISS_NOTIFICATION, payload: id });
  }, []);

  const updateSettings = useCallback((patch) => {
    dispatch({ type: ACTION.UPDATE_SETTINGS, payload: patch });
  }, []);

  const value = {
    ...state,
    login,
    logout,
    fetchAlerts,
    fetchStations,
    addNotification,
    dismissNotification,
    updateSettings,
  };

  return (
    <AppStoreContext.Provider value={value}>
      {children}
    </AppStoreContext.Provider>
  );
}

export function useAppStore() {
  const ctx = useContext(AppStoreContext);
  if (!ctx) {
    throw new Error('useAppStore must be used within AppStoreProvider');
  }
  return ctx;
}

export default useAppStore;
