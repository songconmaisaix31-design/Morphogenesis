import React from 'react';

// EvoMap is an independent read-only endpoint (E track). This panel renders
// whatever the service actually returns — status/source/cache fields and the
// nested result lists (e.g. community_search.assets, local_pool.genes) — and
// never folds any of it into the runtime topology views. Loading happens once
// when the info view is entered and on explicit refresh; no polling.
const MAX_ITEMS = 6;
const MAX_DEPTH = 2;

const isScalar = (value) => value === null || ['string', 'number', 'boolean'].includes(typeof value);

const ScalarRows = ({ object }) => {
  const rows = Object.entries(object ?? {}).filter(([, value]) => isScalar(value));
  if (!rows.length) return null;
  return (
    <dl className='morph-evomap-fields'>
      {rows.map(([key, value]) => (
        <div key={key} className='morph-evomap-field'>
          <dt>{key}</dt>
          <dd>{value === null ? 'null' : String(value)}</dd>
        </div>
      ))}
    </dl>
  );
};

const ValueBlock = ({ name, value, depth }) => {
  if (isScalar(value)) {
    return (
      <div className='morph-evomap-field'>
        <dt>{name}</dt>
        <dd>{value === null ? 'null' : String(value)}</dd>
      </div>
    );
  }
  if (Array.isArray(value)) {
    if (!value.length) return <p className='morph-evomap-line'>{name}：空列表。</p>;
    const objects = value.filter((item) => item && typeof item === 'object');
    return (
      <div className='morph-evomap-section'>
        <span className='morph-evomap-key'>{name} · {value.length} 条</span>
        {depth >= MAX_DEPTH ? <p className='morph-evomap-line'>层级过深，省略详情。</p> : (
          <ul className='morph-evomap-list'>
            {objects.slice(0, MAX_ITEMS).map((item, index) => (
              <li key={index} className='morph-evomap-item'>
                <ScalarRows object={item} />
                {Object.keys(item).some((key) => !isScalar(item[key])) ? (
                  <div className='morph-evomap-nested'>
                    {Object.entries(item).filter(([, v]) => !isScalar(v)).slice(0, 3).map(([key, v]) => (
                      <ValueBlock key={key} name={key} value={v} depth={depth + 1} />
                    ))}
                  </div>
                ) : null}
              </li>
            ))}
            {objects.length > MAX_ITEMS ? <li className='morph-evomap-line'>其余 {objects.length - MAX_ITEMS} 条省略。</li> : null}
            {objects.length < value.length ? (
              <li className='morph-evomap-line'>{value.filter((item) => !item || typeof item !== 'object').map(String).join(' · ')}</li>
            ) : null}
          </ul>
        )}
      </div>
    );
  }
  if (value && typeof value === 'object') {
    return (
      <div className='morph-evomap-section'>
        <span className='morph-evomap-key'>{name}</span>
        <ScalarRows object={value} />
        {depth < MAX_DEPTH ? Object.entries(value).filter(([, v]) => !isScalar(v)).slice(0, 4).map(([key, v]) => (
          <ValueBlock key={key} name={key} value={v} depth={depth + 1} />
        )) : null}
      </div>
    );
  }
  return null;
};

const EvoMapPanel = ({ evomap, onRefresh }) => (
  <section className='morph-evomap' aria-label='EvoMap 只读状态'>
    <div className='morph-evomap-head'>
      <span className='morph-panel-title'>EvoMap · 只读状态</span>
      <span className='morph-evomap-tag'>独立端点 /api/evomap · 非运行拓扑</span>
      <button type='button' className='morph-evomap-refresh' onClick={onRefresh}
        disabled={evomap.state === 'loading'}>{evomap.state === 'loading' ? '读取中…' : '刷新'}</button>
    </div>
    {evomap.state === 'idle' ? <p className='morph-evomap-line'>进入信息界面后读取一次；也可手动刷新。</p> : null}
    {evomap.state === 'loading' ? <p className='morph-evomap-line'>正在读取 EvoMap 状态…</p> : null}
    {evomap.state === 'missing' ? <p className='morph-evomap-line'>/api/evomap 尚未提供（E 轨合入后启用）；未配置时不展示推断信息。</p> : null}
    {evomap.state === 'error' ? <p className='morph-evomap-line'>EvoMap 状态不可用：{evomap.detail}</p> : null}
    {evomap.state === 'ok' ? (
      <div className='morph-evomap-body'>
        {Object.entries(evomap.data ?? {}).map(([key, value]) => (
          <ValueBlock key={key} name={key} value={value} depth={0} />
        ))}
        {Object.keys(evomap.data ?? {}).length === 0 ? <p className='morph-evomap-line'>端点已响应，但返回为空对象。</p> : null}
      </div>
    ) : null}
  </section>
);

export default React.memo(EvoMapPanel);
