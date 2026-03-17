import React, { useEffect, useState } from 'react';
import client from '../api/client';
import { useAuth } from '../hooks/useAuth';

export default function Settings() {
  const { user } = useAuth();
  const [apps, setApps] = useState([]);
  const [tools, setTools] = useState([]);

  useEffect(() => {
    client.get('/apps/list').then((r) => setApps(r.data)).catch(() => {});
    client.get('/gateway/tools').then((r) => setTools(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">设置</h1>

      {/* User profile */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">用户信息</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-500 mb-1">用户名</label>
            <p className="font-medium">{user?.username}</p>
          </div>
          <div>
            <label className="block text-sm text-gray-500 mb-1">显示名称</label>
            <p className="font-medium">{user?.display_name}</p>
          </div>
          <div>
            <label className="block text-sm text-gray-500 mb-1">角色</label>
            <span className="inline-block px-3 py-1 bg-hydro-100 text-hydro-700 rounded-full text-sm font-medium">
              {user?.role}
            </span>
          </div>
        </div>
      </div>

      {/* Installed apps */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">已安装应用</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {apps.map((app) => (
            <div
              key={app.app_id}
              className="flex items-center justify-between border border-gray-200 rounded-lg p-3"
            >
              <div>
                <p className="font-medium text-sm">{app.name}</p>
                <p className="text-xs text-gray-400 font-mono">{app.app_id}</p>
              </div>
              <span
                className={`px-2 py-0.5 rounded text-xs font-medium ${
                  app.status === 'registered'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {app.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Available tools */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">
          MCP 工具列表 ({tools.length})
        </h2>
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">工具名</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">所属应用</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">描述</th>
              </tr>
            </thead>
            <tbody>
              {tools.map((t, i) => (
                <tr key={i} className="border-t border-gray-100">
                  <td className="px-4 py-3 font-mono text-xs text-hydro-700">{t.tool_name}</td>
                  <td className="px-4 py-3">{t.app_id}</td>
                  <td className="px-4 py-3 text-gray-500">{t.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Engine config */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">引擎配置</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <div>
              <p className="font-medium text-sm">HydroOS 内核</p>
              <p className="text-xs text-gray-400">魏家好 — 系统内核与调度引擎</p>
            </div>
            <span className="text-xs text-green-600">已连接</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <div>
              <p className="font-medium text-sm">算法库</p>
              <p className="text-xs text-gray-400">黄志峰 — 优化与智能算法</p>
            </div>
            <span className="text-xs text-green-600">已连接</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <div>
              <p className="font-medium text-sm">水力学引擎</p>
              <p className="text-xs text-gray-400">王孝群 — 水力计算</p>
            </div>
            <span className="text-xs text-yellow-600">待连接</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium text-sm">水质冰期模块</p>
              <p className="text-xs text-gray-400">施垚 — 水质与冰期模拟</p>
            </div>
            <span className="text-xs text-yellow-600">待连接</span>
          </div>
        </div>
      </div>
    </div>
  );
}
