import React, { useEffect, useState } from 'react';
import client from '../api/client';

export default function LabPanel() {
  const [experiments, setExperiments] = useState([]);
  const [literature, setLiterature] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    client.get('/lab/experiments').then((r) => setExperiments(r.data)).catch(() => {});
    client.get('/lab/literature').then((r) => setLiterature(r.data)).catch(() => {});
  }, []);

  const searchLiterature = async () => {
    try {
      const res = await client.get('/lab/literature', { params: { q: searchQuery } });
      setLiterature(res.data);
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">HydroLab - 科研实验</h1>

      {/* Experiments */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">模拟实验</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {experiments.map((exp) => (
            <div key={exp.exp_id} className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs text-gray-400">{exp.exp_id}</span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${
                    exp.status === 'completed'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {exp.status}
                </span>
              </div>
              <h3 className="font-semibold text-sm">{exp.name}</h3>
              <p className="text-xs text-gray-500 mt-1">创建者: {exp.created_by}</p>
              <button className="mt-3 px-3 py-1 text-xs bg-hydro-600 text-white rounded hover:bg-hydro-700 transition-colors">
                查看结果
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Literature search */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">文献检索</h2>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && searchLiterature()}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm"
            placeholder="搜索文献标题..."
          />
          <button
            onClick={searchLiterature}
            className="px-4 py-2 bg-hydro-600 text-white text-sm rounded-lg hover:bg-hydro-700 transition-colors"
          >
            搜索
          </button>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
          {literature.map((lit, i) => (
            <div key={i} className="p-4">
              <h3 className="font-semibold text-sm text-hydro-800">{lit.title}</h3>
              <p className="text-xs text-gray-500 mt-1">
                {lit.authors} ({lit.year})
              </p>
            </div>
          ))}
          {literature.length === 0 && (
            <div className="p-6 text-center text-gray-400 text-sm">无结果</div>
          )}
        </div>
      </div>
    </div>
  );
}
