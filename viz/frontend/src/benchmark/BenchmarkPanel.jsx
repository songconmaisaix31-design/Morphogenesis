// Read-only persisted benchmark summary panel. Every number comes from the
// /api/benchmark JSON; nothing here invents scores, and unknown cost stays 未知.
import React, { useMemo } from 'react';
import './benchmark.css';

const knownNumber = (value) => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
const number = (value, digits = 2) => knownNumber(value) ? Number(value).toFixed(digits) : '未知';
const percent = (value) => knownNumber(value) ? `${(Number(value) * 100).toFixed(0)}%` : '未知';

function Stat({ value, label }) {
  return (
    <div className='benchmark-stat'>
      <span className='benchmark-stat-value'>{value}</span>
      <span className='benchmark-stat-label'>{label}</span>
    </div>
  );
}

function ConditionCard({ condition }) {
  const benchmark = condition.benchmark ?? {};
  const models = condition.per_model_descriptive ?? {};
  const tokens = condition.tokens ?? {};
  const cost = condition.cost ?? {};
  const modelEntries = Object.entries(models);
  return (
    <section className='benchmark-condition' aria-label={condition.label ?? condition.id}>
      <header className='benchmark-condition-head'>
        <strong>{condition.label ?? condition.id}</strong>
        <span className='benchmark-condition-meta'>{condition.workers ?? '?'} worker · {condition.tasks ?? '?'} task</span>
      </header>
      <div className='benchmark-stats'>
        <Stat value={percent(benchmark.accuracy)} label='accuracy' />
        <Stat value={number(benchmark.correct, 0)} label='correct' />
        <Stat value={number(benchmark.incorrect, 0)} label='incorrect' />
        <Stat value={number(benchmark.malformed, 0)} label='malformed' />
        <Stat value={number(benchmark.missing, 0)} label='missing' />
        <Stat value={percent(benchmark.strict_json_rate)} label='JSON 约束' />
      </div>
      <div className='benchmark-models'>
        <h5>每模型明细（分配去中心化，仅描述性）</h5>
        {modelEntries.length === 0 && <p className='swarm-detail-dim'>无每模型明细。</p>}
        <ul>
          {modelEntries.map(([model, value]) => (
            <li key={model}>
              <span className='benchmark-model'>{model}</span>
              <span className='benchmark-model-detail'>
                请求 {number(value.requested, 0)} · 对 {number(value.correct, 0)} · 错 {number(value.incorrect, 0)} · 格式错 {number(value.malformed, 0)} · 缺 {number(value.missing, 0)} · 准确率 {percent(value.accuracy)}
              </span>
            </li>
          ))}
        </ul>
      </div>
      <div className='benchmark-cost'>
        <span>tokens {knownNumber(tokens.known_total) ? number(tokens.known_total, 0) : '未知'}（已知 {number(tokens.known_requests, 0)} 请求）</span>
        <span>cost {knownNumber(cost.billed_usd) ? `$${number(cost.billed_usd, 4)}` : '未知'}</span>
        <span>provenance {condition.provenance ?? '未知'}</span>
      </div>
    </section>
  );
}

export default function BenchmarkPanel({ benchmark = null }) {
  const conditions = useMemo(
    () => (benchmark && Array.isArray(benchmark.conditions) ? benchmark.conditions : []),
    [benchmark],
  );
  if (!conditions.length) {
    return (
      <section className='benchmark-panel' aria-label='Benchmark 校验'>
        <h4>Benchmark 校验（0 组）</h4>
        <p className='swarm-detail-dim'>尚未配置 benchmark 结果。</p>
      </section>
    );
  }
  return (
    <section className='benchmark-panel' aria-label='Benchmark 校验'>
      <h4>Benchmark 校验（{conditions.length} 组）</h4>
      {benchmark?.note && <p className='benchmark-note'>{benchmark.note}</p>}
      <div className='benchmark-conditions'>
        {conditions.map((condition) => (
          <ConditionCard key={condition.id ?? condition.label ?? Math.random()} condition={condition} />
        ))}
      </div>
    </section>
  );
}
