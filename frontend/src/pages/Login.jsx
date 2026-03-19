import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../hooks/useAuth';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const demoAuthEnv = import.meta.env.VITE_HYDROPORTAL_DEMO_AUTH?.trim().toLowerCase();
  const hasExplicitDemoAuth = demoAuthEnv !== undefined && demoAuthEnv !== '';
  const showDemoCredentials = hasExplicitDemoAuth
    ? ['1', 'true', 'yes', 'on'].includes(demoAuthEnv)
    : import.meta.env.DEV;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/', { replace: true });
    } catch {
      setError('用户名或密码错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-hydro-800 to-hydro-600">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-hydro-800">HydroPortal</h1>
          <p className="text-gray-500 mt-2">水网门户 - 统一登录</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hydro-500 focus:border-transparent outline-none"
              placeholder="输入用户名"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hydro-500 focus:border-transparent outline-none"
              placeholder="输入密码"
              required
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm bg-red-50 px-4 py-2 rounded-lg">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-hydro-600 hover:bg-hydro-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? '登录中...' : '登 录'}
          </button>
        </form>

        {showDemoCredentials && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-2">演示账号：</p>
            <div className="text-xs text-gray-600 space-y-1">
              <p>admin / admin123 (管理员)</p>
              <p>designer / design123 (设计师)</p>
              <p>operator / oper123 (调度员)</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
