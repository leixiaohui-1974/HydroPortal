import React, { useEffect, useState } from 'react';
import client from '../api/client';
import useWebSocket from '../hooks/useWebSocket';

export default function GuardPanel() {
  const [stations, setStations] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [dispatchForm, setDispatchForm] = useState({ station_id: '', command: '' });
  const [dispatchResult, setDispatchResult] = useState(null);

  // Real-time SCADA data via WebSocket
  const { connected, lastData: scadaData } = useWebSocket('/ws/scada', { enabled: true });

  useEffect(() => {
    client.get('/guard/stations').then((r) => setStations(r.data)).catch(() => {});
    client.get('/guard/alerts').then((r) => setAlerts(r.data)).catch(() => {});
  }, []);

  const acknowledgeAlert = async (alertId) => {
    await client.post(`/guard/alerts/${alertId}/ack`);
    setAlerts((prev) => prev.filter((a) => a.alert_id !== alertId));
  };

  const submitDispatch = async (e) => {
    e.preventDefault();
    try {
      const res = await client.post('/guard/dispatch', dispatchForm);
      setDispatchResult(res.data);
      setDispatchForm({ station_id: '', command: '' });
    } catch {
      setDispatchResult({ status: 'error', message: 'Dispatch failed' });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">HydroGuard - SCADA 监控</h1>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium ${
            connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}
        >
          WebSocket: {connected ? '已连接' : '断开'}
        </span>
      </div>

      {/* Station list */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">监测站点</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {stations.map((s) => (
            <div
              key={s.station_id}
              className="bg-white rounded-lg border border-gray-200 p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs text-gray-400">{s.station_id}</span>
                <StatusDot status={s.status} />
              </div>
              <p className="font-medium text-sm">{s.name}</p>
              <p className="text-xs text-gray-400 mt-1">
                {s.lat.toFixed(2)}, {s.lon.toFixed(2)}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Real-time SCADA readings */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">实时数据</h2>
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">站点</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">水位 (m)</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">流量 (m3/s)</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">压力 (MPa)</th>
              </tr>
            </thead>
            <tbody>
              {(scadaData || []).map((reading) => (
                <tr key={reading.station_id} className="border-t border-gray-100">
                  <td className="px-4 py-3 font-mono text-xs">{reading.station_id}</td>
                  <td className="px-4 py-3 font-mono">{reading.water_level?.toFixed(2)}</td>
                  <td className="px-4 py-3 font-mono">{reading.flow_rate?.toFixed(1)}</td>
                  <td className="px-4 py-3 font-mono">{reading.pressure?.toFixed(3)}</td>
                </tr>
              ))}
              {!scadaData && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-gray-400">
                    等待数据...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alerts */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">活跃告警</h2>
        {alerts.length === 0 ? (
          <p className="text-gray-400 text-sm">暂无未确认告警</p>
        ) : (
          <div className="space-y-2">
            {alerts.map((a) => (
              <div
                key={a.alert_id}
                className={`flex items-center justify-between p-4 rounded-lg border ${
                  a.level === 'critical'
                    ? 'bg-red-50 border-red-200'
                    : 'bg-yellow-50 border-yellow-200'
                }`}
              >
                <div>
                  <span className="font-mono text-xs text-gray-500">{a.alert_id}</span>
                  <span className="mx-2 text-gray-300">|</span>
                  <span className="text-sm font-medium">{a.station_id}</span>
                  <span className="mx-2 text-gray-300">|</span>
                  <span className="text-sm">{a.message}</span>
                </div>
                <button
                  onClick={() => acknowledgeAlert(a.alert_id)}
                  className="px-3 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-100 transition-colors"
                >
                  确认
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Dispatch form */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">创建调度指令</h2>
        <form onSubmit={submitDispatch} className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">目标站点</label>
              <select
                value={dispatchForm.station_id}
                onChange={(e) => setDispatchForm((f) => ({ ...f, station_id: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                required
              >
                <option value="">选择站点...</option>
                {stations.map((s) => (
                  <option key={s.station_id} value={s.station_id}>
                    {s.station_id} - {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">调度命令</label>
              <input
                type="text"
                value={dispatchForm.command}
                onChange={(e) => setDispatchForm((f) => ({ ...f, command: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                placeholder="例如：开闸放水 50m3/s"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            className="mt-4 px-6 py-2 bg-hydro-600 hover:bg-hydro-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            下发指令
          </button>
          {dispatchResult && (
            <div className="mt-3 text-sm text-green-700 bg-green-50 px-4 py-2 rounded-lg">
              {dispatchResult.message} (ID: {dispatchResult.dispatch_id})
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

function StatusDot({ status }) {
  const colors = {
    online: 'bg-green-400',
    warning: 'bg-yellow-400',
    offline: 'bg-red-400',
  };
  return (
    <span className="flex items-center gap-1 text-xs text-gray-500">
      <span className={`w-2 h-2 rounded-full ${colors[status] || 'bg-gray-400'}`} />
      {status}
    </span>
  );
}
