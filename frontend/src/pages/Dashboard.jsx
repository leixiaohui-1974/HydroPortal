import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';

const QUICK_LINKS = [
  { to: '/guard', label: 'HydroGuard', desc: 'SCADA 监控与调度' },
  { to: '/design', label: 'HydroDesign', desc: '工程设计与审查' },
  { to: '/lab', label: 'HydroLab', desc: '科研实验与文献' },
  { to: '/edu', label: 'HydroEdu', desc: '教育培训与考核' },
  { to: '/arena', label: 'HydroArena', desc: '竞赛与排行' },
];

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [stations, setStations] = useState([]);

  useEffect(() => {
    client.get('/gateway/health').then((r) => setHealth(r.data)).catch(() => {});
    client.get('/guard/alerts').then((r) => setAlerts(r.data)).catch(() => {});
    client.get('/guard/stations').then((r) => setStations(r.data)).catch(() => {});
  }, []);

  const onlineStations = stations.filter((s) => s.status === 'online').length;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">系统总览</h1>

      {/* Status cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatusCard title="在线站点" value={`${onlineStations} / ${stations.length}`} color="green" />
        <StatusCard title="活跃告警" value={alerts.length} color="red" />
        <StatusCard title="今日调度" value="12" color="blue" />
        <StatusCard
          title="Portal 状态"
          value={health?.portal === 'ok' ? '正常' : '检查中...'}
          color="indigo"
        />
      </div>

      {/* Quick links */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">快速入口</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {QUICK_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="block bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md hover:border-hydro-400 transition-all"
            >
              <h3 className="font-semibold text-hydro-700">{link.label}</h3>
              <p className="text-sm text-gray-500 mt-1">{link.desc}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent alerts */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">最近告警</h2>
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">告警ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">站点</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">级别</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">消息</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-gray-400">
                    暂无告警
                  </td>
                </tr>
              ) : (
                alerts.map((a) => (
                  <tr key={a.alert_id} className="border-t border-gray-100">
                    <td className="px-4 py-3 font-mono text-xs">{a.alert_id}</td>
                    <td className="px-4 py-3">{a.station_id}</td>
                    <td className="px-4 py-3">
                      <LevelBadge level={a.level} />
                    </td>
                    <td className="px-4 py-3">{a.message}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* App health */}
      {health && (
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-3">服务状态</h2>
          <div className="flex flex-wrap gap-3">
            {Object.entries(health.apps || {}).map(([id, status]) => (
              <div
                key={id}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  status === 'ok'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}
              >
                {id}: {status}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatusCard({ title, value, color }) {
  const colors = {
    green: 'bg-green-50 border-green-200 text-green-700',
    red: 'bg-red-50 border-red-200 text-red-700',
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    indigo: 'bg-indigo-50 border-indigo-200 text-indigo-700',
  };
  return (
    <div className={`rounded-lg border p-4 ${colors[color] || colors.blue}`}>
      <p className="text-sm opacity-80">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

function LevelBadge({ level }) {
  const cls =
    level === 'critical'
      ? 'bg-red-100 text-red-700'
      : level === 'warning'
        ? 'bg-yellow-100 text-yellow-700'
        : 'bg-blue-100 text-blue-700';
  return <span className={`px-2 py-0.5 rounded text-xs font-medium ${cls}`}>{level}</span>;
}
