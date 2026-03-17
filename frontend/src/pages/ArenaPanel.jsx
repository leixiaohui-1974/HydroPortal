import React, { useEffect, useState } from 'react';
import client from '../api/client';

export default function ArenaPanel() {
  const [contests, setContests] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [selectedContest, setSelectedContest] = useState(null);

  useEffect(() => {
    client.get('/arena/contests').then((r) => setContests(r.data)).catch(() => {});
  }, []);

  const loadLeaderboard = async (contestId) => {
    setSelectedContest(contestId);
    try {
      const res = await client.get(`/arena/leaderboard/${contestId}`);
      setLeaderboard(res.data);
    } catch {
      setLeaderboard([]);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">HydroArena - 竞赛平台</h1>

      {/* Contest list */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">竞赛列表</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {contests.map((c) => (
            <div
              key={c.contest_id}
              className={`bg-white rounded-lg border p-5 cursor-pointer transition-all hover:shadow-md ${
                selectedContest === c.contest_id
                  ? 'border-hydro-500 ring-2 ring-hydro-200'
                  : 'border-gray-200'
              }`}
              onClick={() => loadLeaderboard(c.contest_id)}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs text-gray-400">{c.contest_id}</span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${
                    c.status === 'active'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {c.status === 'active' ? '进行中' : '即将开始'}
                </span>
              </div>
              <h3 className="font-semibold text-base">{c.name}</h3>
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                <span>{c.participants} 名参赛者</span>
                <span>截止: {c.deadline}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Leaderboard */}
      {selectedContest && (
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-3">
            排行榜 - {selectedContest}
          </h2>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 w-20">排名</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">用户</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 w-32">得分</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((entry) => (
                  <tr key={entry.rank} className="border-t border-gray-100">
                    <td className="px-4 py-3">
                      {entry.rank <= 3 ? (
                        <span className="text-lg">
                          {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : '🥉'}
                        </span>
                      ) : (
                        <span className="text-gray-500">#{entry.rank}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-medium">{entry.username}</td>
                    <td className="px-4 py-3 font-mono font-semibold text-hydro-700">
                      {entry.score}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Submit section */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">提交方案</h2>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500 mb-4">选择竞赛并上传您的解决方案文件</p>
          <div className="flex items-center gap-4">
            <select className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">选择竞赛...</option>
              {contests.map((c) => (
                <option key={c.contest_id} value={c.contest_id}>
                  {c.name}
                </option>
              ))}
            </select>
            <button className="px-6 py-2 bg-hydro-600 text-white text-sm rounded-lg hover:bg-hydro-700 transition-colors">
              提交
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
