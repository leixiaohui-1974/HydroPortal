import React, { createContext, useContext, useState, useEffect } from 'react';
import client from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('hydro_token');
    if (token) {
      client
        .get('/auth/me')
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('hydro_token');
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const res = await client.post('/auth/login', { username, password });
    const { access_token } = res.data;
    localStorage.setItem('hydro_token', access_token);
    const me = await client.get('/auth/me');
    setUser(me.data);
    return me.data;
  };

  const logout = () => {
    localStorage.removeItem('hydro_token');
    setUser(null);
  };

  return React.createElement(
    AuthContext.Provider,
    { value: { user, loading, login, logout } },
    children
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export default useAuth;
