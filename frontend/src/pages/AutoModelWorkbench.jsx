import React, { useEffect, useState } from 'react';
import client from '../api/client';

const FALLBACK_PROJECT = {
  name: '大渡河流域划分 MVP',
  basin: '大渡河',
  objective: '先完成流域划分输入收敛，再进入后续模拟与审查',
  phase: '数据发现与空间建模',
  currentWorkflow: 'watershed_delineation',
  blocker: 'canonical artifact 仍未稳定落仓，运行管道待收口',
  nextAction: '修复 native coder 的 workspace/output-root 对齐后，重跑 canonical 写入与审查',
};

const FALLBACK_STATUS_CARDS = [
  { title: '当前阶段', value: '数据发现', tone: 'blue' },
  { title: '主线对象', value: '干流水库 + 水文站', tone: 'green' },
  { title: '待人工确认', value: '黑马', tone: 'amber' },
  { title: '延后处理', value: '雨量站', tone: 'slate' },
];

const FALLBACK_DATA_SOURCES = [
  {
    name: 'dem.tif',
    role: 'primary_dem',
    status: 'authoritative',
    note: '当前流域划分主 DEM',
  },
  {
    name: 'hydrorivers_daduhe_main.shp',
    role: 'river_network_main',
    status: 'authoritative',
    note: '主干河网参考',
  },
  {
    name: '11150大渡河智能体.json',
    role: 'supporting_evidence',
    status: 'supporting',
    note: '用于补强瀑布沟等节点证据',
  },
  {
    name: 'station_info.csv',
    role: 'raw_station_source',
    status: 'review_required',
    note: '可作原始来源，但不能直接当 authoritative outlet',
  },
];

const FALLBACK_SCOPE_ROWS = [
  { name: '瀑布沟', type: 'reservoir_or_node', decision: '纳入主线', confidence: '较高' },
  { name: '石棉', type: 'hydrology_station', decision: '纳入主线', confidence: '较高' },
  { name: '黑马', type: 'hydrology_station', decision: '待复核', confidence: '不足' },
  { name: '丰乐', type: 'rain_gauge', decision: '延后到面雨量阶段', confidence: '已明确' },
  { name: '晒经', type: 'rain_gauge', decision: '延后到面雨量阶段', confidence: '已明确' },
];

const FALLBACK_WORKFLOW_STEPS = [
  { name: '数据发现', status: 'done', detail: '已能生成 source inventory / reliability' },
  { name: '站点与 Outlet 规范化', status: 'active', detail: '主线范围已清楚，canonical 落仓未完成' },
  { name: '流域划分', status: 'pending', detail: '等待 data pack 与 canonical 输入稳定' },
  { name: '审查报告', status: 'pending', detail: '待 workflow_run 产出后生成 review bundle' },
];

const FALLBACK_RUNTIME_SIGNALS = [
  ['当前运行器', 'hm + agent-teams'],
  ['长任务模式', '已支持'],
  ['结构化状态', 'watch --json'],
  ['当前问题', 'native coder 写入链仍需收口'],
];

export default function AutoModelWorkbench() {
  const [snapshot, setSnapshot] = useState(null);

  useEffect(() => {
    client.get('/automodel/workbench').then((response) => {
      setSnapshot(response.data);
    }).catch(() => {});
  }, []);

  const project = snapshot?.project || FALLBACK_PROJECT;
  const statusCards = snapshot?.status_cards || FALLBACK_STATUS_CARDS;
  const dataSources = snapshot?.data_sources || FALLBACK_DATA_SOURCES;
  const scopeRows = snapshot?.scope_rows || FALLBACK_SCOPE_ROWS;
  const workflowSteps = snapshot?.workflow_steps || FALLBACK_WORKFLOW_STEPS;
  const runtimeSignals = snapshot?.runtime_signals || FALLBACK_RUNTIME_SIGNALS;

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-stone-200 bg-gradient-to-br from-cyan-50 via-white to-amber-50 p-7">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-cyan-700">
              水利自动化建模工作台
            </p>
            <h1 className="text-3xl font-bold tracking-tight text-stone-900">
              {project.name}
            </h1>
            <p className="text-sm leading-6 text-stone-600">
              流域：{project.basin}。目标：{project.objective}
            </p>
          </div>
          <div className="rounded-2xl border border-cyan-200 bg-white/80 px-5 py-4 shadow-sm">
            <p className="text-xs uppercase tracking-[0.2em] text-stone-500">当前 blocker</p>
            <p className="mt-2 max-w-sm text-sm font-medium text-stone-800">{project.blocker}</p>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {statusCards.map((item) => (
          <StatusCard key={item.title} {...item} />
        ))}
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <Panel
          title="工程状态"
          description="用户看到的是业务进度，不是内部 agent 细节。"
        >
          <dl className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <InfoPair label="当前 phase" value={project.phase} />
            <InfoPair label="当前工作流" value={project.currentWorkflow} />
            <InfoPair label="下一动作" value={project.nextAction} />
            <InfoPair label="运行状态" value="长任务运行中，可持续恢复" />
          </dl>
        </Panel>

        <Panel
          title="运行中心摘要"
          description="这一块后续对接 hm watch --json 的真实状态。"
        >
          <div className="space-y-3">
            {runtimeSignals.map(([label, value]) => (
              <div
                key={label}
                className="flex items-center justify-between rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3"
              >
                <span className="text-sm text-stone-500">{label}</span>
                <span className="text-sm font-medium text-stone-900">{value}</span>
              </div>
            ))}
          </div>
          <RuntimeBadge runtime={snapshot?.runtime} />
          {snapshot?.latest_runtime_excerpt ? (
            <pre className="mt-4 overflow-auto rounded-2xl bg-stone-950 p-4 text-xs leading-6 text-stone-100">
              {snapshot.latest_runtime_excerpt}
            </pre>
          ) : null}
        </Panel>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel
          title="数据发现总览"
          description="先清楚知道哪些数据能进主线，哪些只能做证据。"
        >
          <div className="overflow-hidden rounded-2xl border border-stone-200">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-left text-stone-500">
                <tr>
                  <th className="px-4 py-3 font-medium">数据源</th>
                  <th className="px-4 py-3 font-medium">角色</th>
                  <th className="px-4 py-3 font-medium">状态</th>
                  <th className="px-4 py-3 font-medium">说明</th>
                </tr>
              </thead>
              <tbody>
                {dataSources.map((item) => (
                  <tr key={item.name} className="border-t border-stone-100">
                    <td className="px-4 py-3 font-medium text-stone-900">{item.name}</td>
                    <td className="px-4 py-3 text-stone-600">{item.role}</td>
                    <td className="px-4 py-3">
                      <Badge tone={statusTone(item.status)}>{item.status}</Badge>
                    </td>
                    <td className="px-4 py-3 text-stone-600">{item.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel
          title="工作流步骤"
          description="MVP 先打通 source discovery -> normalize -> delineate -> review。"
        >
          <div className="space-y-3">
            {workflowSteps.map((step, index) => (
              <div
                key={step.name}
                className="rounded-2xl border border-stone-200 bg-white px-4 py-4"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${stepCircle(step.status)}`}>
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-stone-900">{step.name}</p>
                      <p className="text-xs text-stone-500">{step.detail}</p>
                    </div>
                  </div>
                  <Badge tone={workflowTone(step.status)}>{step.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_1fr]">
        <Panel
          title="站点与水库映射"
          description="这里才是当前大渡河流域划分真正要人工看懂的业务核心。"
        >
          <div className="overflow-hidden rounded-2xl border border-stone-200">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-left text-stone-500">
                <tr>
                  <th className="px-4 py-3 font-medium">名称</th>
                  <th className="px-4 py-3 font-medium">类型</th>
                  <th className="px-4 py-3 font-medium">当前决定</th>
                  <th className="px-4 py-3 font-medium">置信度</th>
                  <th className="px-4 py-3 font-medium">几何状态</th>
                  <th className="px-4 py-3 font-medium">证据数</th>
                </tr>
              </thead>
              <tbody>
                {scopeRows.map((row) => (
                  <tr key={row.name} className="border-t border-stone-100">
                    <td className="px-4 py-3 font-medium text-stone-900">{row.name}</td>
                    <td className="px-4 py-3 text-stone-600">{row.type}</td>
                    <td className="px-4 py-3 text-stone-700">{row.decision}</td>
                    <td className="px-4 py-3">
                      <Badge tone={confidenceTone(row.confidence)}>{row.confidence}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge tone={row.geometry_status === 'inside_dem' ? 'green' : 'amber'}>
                        {row.geometry_status || 'unknown'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-stone-700">{row.evidence_count || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel
          title="产品原则"
          description="这一页要始终把内部实现细节压到后台。"
        >
          <ul className="space-y-3 text-sm text-stone-700">
            <RuleItem text="用户看到的是工程状态、数据缺口、可否进入下一步，而不是 tmux、phase 或 agent 内部细节。" />
            <RuleItem text="确定性系统负责 contract、gate、输出路径和 verdict，智能体只做证据整理、解释和摘要。" />
            <RuleItem text="雨量站不应混入当前流域划分主线，它们属于后续面雨量阶段。" />
            <RuleItem text="人工确认点必须显式展示，例如 黑马 这类证据不足站点，不能埋在日志里。" />
          </ul>
        </Panel>
      </section>
    </div>
  );
}

function Panel({ title, description, children }) {
  return (
    <section className="rounded-3xl border border-stone-200 bg-white p-6 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-stone-900">{title}</h2>
        <p className="mt-1 text-sm text-stone-500">{description}</p>
      </div>
      {children}
    </section>
  );
}

function StatusCard({ title, value, tone }) {
  const tones = {
    blue: 'border-cyan-200 bg-cyan-50 text-cyan-800',
    green: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    amber: 'border-amber-200 bg-amber-50 text-amber-800',
    slate: 'border-stone-200 bg-stone-50 text-stone-700',
  };

  return (
    <div className={`rounded-3xl border p-5 ${tones[tone] || tones.slate}`}>
      <p className="text-sm opacity-75">{title}</p>
      <p className="mt-2 text-2xl font-bold">{value}</p>
    </div>
  );
}

function InfoPair({ label, value }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
      <dt className="text-xs uppercase tracking-[0.18em] text-stone-500">{label}</dt>
      <dd className="mt-2 text-sm font-medium leading-6 text-stone-900">{value}</dd>
    </div>
  );
}

function Badge({ tone, children }) {
  const tones = {
    green: 'bg-emerald-100 text-emerald-800',
    blue: 'bg-cyan-100 text-cyan-800',
    amber: 'bg-amber-100 text-amber-800',
    red: 'bg-rose-100 text-rose-800',
    slate: 'bg-stone-100 text-stone-700',
  };
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${tones[tone] || tones.slate}`}>
      {children}
    </span>
  );
}

function RuleItem({ text }) {
  return (
    <li className="flex items-start gap-3 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3">
      <span className="mt-0.5 text-cyan-700">•</span>
      <span>{text}</span>
    </li>
  );
}

function RuntimeBadge({ runtime }) {
  if (!runtime) return null;
  return (
    <div className="mt-4 rounded-2xl border border-cyan-200 bg-cyan-50 px-4 py-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <Badge tone={runtime.alive ? 'green' : 'amber'}>
          {runtime.alive ? '运行中' : '已结束'}
        </Badge>
        <span className="text-stone-700">
          {runtime.workflow || 'unknown'} / phase {runtime.phase || '-'}
        </span>
        <span className="font-medium text-stone-900">
          {runtime.current_step || '-'} / {runtime.total_steps || '-'} {runtime.step_name || ''}
        </span>
      </div>
      <p className="mt-3 text-sm text-stone-600">{runtime.why_waiting}</p>
    </div>
  );
}

function statusTone(status) {
  if (status === 'authoritative') return 'green';
  if (status === 'supporting') return 'blue';
  if (status === 'review_required') return 'amber';
  return 'slate';
}

function workflowTone(status) {
  if (status === 'done') return 'green';
  if (status === 'active') return 'blue';
  return 'slate';
}

function confidenceTone(value) {
  if (value === '较高' || value === '已明确') return 'green';
  if (value === '不足') return 'amber';
  return 'slate';
}

function stepCircle(status) {
  if (status === 'done') return 'bg-emerald-500 text-white';
  if (status === 'active') return 'bg-cyan-600 text-white';
  return 'bg-stone-200 text-stone-600';
}
