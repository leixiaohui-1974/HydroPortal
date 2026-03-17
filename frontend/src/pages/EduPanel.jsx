import React, { useEffect, useState } from 'react';
import client from '../api/client';

export default function EduPanel() {
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    client.get('/edu/courses').then((r) => setCourses(r.data)).catch(() => {});
  }, []);

  const difficultyColors = {
    beginner: 'bg-green-100 text-green-700',
    intermediate: 'bg-yellow-100 text-yellow-700',
    advanced: 'bg-red-100 text-red-700',
  };

  const difficultyLabels = {
    beginner: '入门',
    intermediate: '进阶',
    advanced: '高级',
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">HydroEdu - 教育培训</h1>

      {/* Course list */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">课程列表</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {courses.map((c) => (
            <div
              key={c.course_id}
              className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-xs text-gray-400">{c.course_id}</span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${
                    difficultyColors[c.difficulty] || ''
                  }`}
                >
                  {difficultyLabels[c.difficulty] || c.difficulty}
                </span>
              </div>
              <h3 className="font-semibold text-base mb-2">{c.name}</h3>
              <p className="text-sm text-gray-500">{c.modules} 个模块</p>

              {/* Progress bar (simulated) */}
              <div className="mt-4">
                <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                  <span>学习进度</span>
                  <span>33%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-hydro-500 h-2 rounded-full" style={{ width: '33%' }} />
                </div>
              </div>

              <button className="mt-4 w-full py-2 text-sm bg-hydro-600 text-white rounded-lg hover:bg-hydro-700 transition-colors">
                继续学习
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Quiz section */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">在线测验</h2>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-sm">水力学基础测验 #1</h3>
              <p className="text-xs text-gray-500 mt-1">共 10 题 | 满分 100 分 | 限时 30 分钟</p>
            </div>
            <button className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              开始测验
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
