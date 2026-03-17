import React, { useEffect, useState } from 'react';
import client from '../api/client';

export default function DesignPanel() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [schemes, setSchemes] = useState([]);

  useEffect(() => {
    client.get('/design/projects').then((r) => setProjects(r.data)).catch(() => {});
  }, []);

  const loadSchemes = async (projectId) => {
    setSelectedProject(projectId);
    try {
      const res = await client.get(`/design/projects/${projectId}/schemes`);
      setSchemes(res.data);
    } catch {
      setSchemes([]);
    }
  };

  const runCompliance = async (schemeId) => {
    try {
      const res = await client.post('/design/compliance/check', { scheme_id: schemeId });
      alert(
        `合规检查完成：${res.data.compliant ? '通过' : '未通过'}\n已检查 ${res.data.checked_rules} 条规则`
      );
    } catch {
      alert('合规检查失败');
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">HydroDesign - 工程设计</h1>

      {/* Projects */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">设计项目</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {projects.map((p) => (
            <div
              key={p.project_id}
              className={`bg-white rounded-lg border p-4 cursor-pointer transition-all hover:shadow-md ${
                selectedProject === p.project_id
                  ? 'border-hydro-500 ring-2 ring-hydro-200'
                  : 'border-gray-200'
              }`}
              onClick={() => loadSchemes(p.project_id)}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs text-gray-400">{p.project_id}</span>
                <StatusBadge status={p.status} />
              </div>
              <h3 className="font-semibold text-sm">{p.name}</h3>
              <p className="text-xs text-gray-500 mt-1">负责人: {p.owner}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Schemes */}
      {selectedProject && (
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-3">
            方案列表 - {selectedProject}
          </h2>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">方案ID</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">方案名称</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">评分</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody>
                {schemes.map((s) => (
                  <tr key={s.scheme_id} className="border-t border-gray-100">
                    <td className="px-4 py-3 font-mono text-xs">{s.scheme_id}</td>
                    <td className="px-4 py-3">{s.name}</td>
                    <td className="px-4 py-3">
                      <span className="font-mono font-semibold text-hydro-700">{s.score}</span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => runCompliance(s.scheme_id)}
                        className="px-3 py-1 text-xs bg-hydro-600 text-white rounded hover:bg-hydro-700 transition-colors"
                      >
                        合规检查
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    draft: 'bg-gray-100 text-gray-600',
    in_progress: 'bg-blue-100 text-blue-700',
    review: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-green-100 text-green-700',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[status] || styles.draft}`}>
      {status}
    </span>
  );
}
