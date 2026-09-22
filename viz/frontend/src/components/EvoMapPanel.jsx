import React, { useEffect, useState } from 'react';

// EvoMap read-only explorer (E track endpoint /api/evomap, schema
// morph.evomap.readonly/1). Requests fire only on first entry into the info
// view and on explicit search/refresh — never on a timer. Everything shown is
// projected from real response fields; missing keys render nothing, and no
// EvoMap data ever feeds the runtime topology views.
const ASSET_TYPES = ['', 'Gene', 'Capsule'];
const LIMITS = [5, 10, 20, 50];

const STATE_LABEL = {
  live: 'live · 实时', cache: 'cache · 缓存', stale_cache: 'stale · 过期缓存', error: 'error · 失败',
  ok: 'ok', empty: 'empty · 空', unconfigured: 'unconfigured · 未配置',
};

const StateChip = ({ state }) => (
  <span className={`morph-evomap-state state-${String(state ?? 'unknown').replace(/_/g, '-')}`}>
    {STATE_LABEL[state] ?? String(state ?? 'unknown')}
  </span>
);

// Unknown must never render as zero: null/undefined/'' stay hidden.
const num = (value, digits = 2) => (
  value === null || value === undefined || value === '' || !Number.isFinite(Number(value))
    ? null
    : Number(value).toFixed(digits)
);

// Asset card: only fields the Hub actually returned (server-side whitelist).
const AssetCard = ({ asset }) => {
  const meta = [
    ['类型', asset.asset_type], ['状态', asset.status], ['trust', asset.trust_tier],
    ['GDI', num(asset.gdi_score)], ['相似度', num(asset.similarity)],
    ['赞/踩', asset.upvotes !== undefined || asset.downvotes !== undefined ? `${asset.upvotes ?? 0}/${asset.downvotes ?? 0}` : null],
    ['查看', asset.view_count], ['复用', asset.reuse_count],
    ['来源节点', asset.source_node_alias ?? asset.source_node_id],
  ].filter(([, value]) => value !== null && value !== undefined && value !== '');
  return (
    <li className='morph-evomap-asset'>
      <div className='morph-evomap-asset-head'>
        <strong>{asset.short_title || asset.asset_id || '未命名资产'}</strong>
        {asset.domain ? <span className='morph-evomap-domain'>{asset.domain}</span> : null}
      </div>
      {asset.nl_summary ? <p className='morph-evomap-summary'>{asset.nl_summary}</p> : null}
      {asset.trigger_text ? <p className='morph-evomap-trigger'>触发：{asset.trigger_text}</p> : null}
      <div className='morph-evomap-meta'>
        {meta.map(([key, value]) => <span key={key}>{key} {String(value)}</span>)}
        {asset.asset_id ? <span className='morph-evomap-id' title={asset.asset_id}>id {asset.asset_id.slice(0, 12)}…</span> : null}
      </div>
    </li>
  );
};

// community_categories comes from the official GET /a2a/assets/categories
// (E track). Real shape: {state, error, cache_age_seconds, by_type:
// [{type,count}], by_gene_category: [{category,count}]}. Absent field renders
// nothing — no fabricated counts.
const CategoryChips = ({ rows, keyName }) => (
  <div className='morph-evomap-cats'>
    {rows.map((row) => {
      const name = row?.[keyName];
      const count = Number(row?.count);
      if (name === undefined || name === null) return null;
      return <span key={String(name)} className='morph-evomap-cat'>{String(name)}{Number.isFinite(count) ? <b>{count.toLocaleString()}</b> : null}</span>;
    })}
  </div>
);

const Categories = ({ categories }) => {
  if (!categories || typeof categories !== 'object') return null;
  const byType = Array.isArray(categories.by_type) ? categories.by_type : [];
  const byGene = Array.isArray(categories.by_gene_category) ? categories.by_gene_category : [];
  if (!byType.length && !byGene.length && !categories.state) return null;
  return (
    <div className='morph-evomap-section'>
      <span className='morph-evomap-key'>
        社区类别（真实计数，可参考选择搜索方向）<StateChip state={categories.state} />
      </span>
      {categories.error ? <p className='morph-evomap-line'>类别获取失败：错误码 {categories.error}</p> : null}
      {byType.length ? <CategoryChips rows={byType} keyName='type' /> : null}
      {byGene.length ? <CategoryChips rows={byGene} keyName='category' /> : null}
      {categories.cache_age_seconds != null ? (
        <p className='morph-evomap-line'>缓存年龄 {Math.round(categories.cache_age_seconds)}s / TTL {Math.round(categories.cache_ttl_seconds ?? 0)}s</p>
      ) : null}
    </div>
  );
};

const LocalPool = ({ pool }) => {
  if (!pool) return null;
  const genes = Array.isArray(pool.genes) ? pool.genes : [];
  return (
    <div className='morph-evomap-section'>
      <span className='morph-evomap-key'>本地 Gene 池 <StateChip state={pool.state} /></span>
      <p className='morph-evomap-line'>
        来源：{pool.source ?? '未配置'}{pool.error ? ` · 错误码 ${pool.error}` : ''} · {genes.length} 条
      </p>
      {genes.length ? (
        <ul className='morph-evomap-list'>
          {genes.slice(0, 8).map((gene, index) => {
            const geneId = gene.gene_id ?? gene.ref?.gene_id ?? 'unknown';
            const trigger = Array.isArray(gene.trigger) ? gene.trigger.join(' / ') : (typeof gene.trigger === 'string' ? gene.trigger : '');
            return (
              <li key={`${geneId}-${index}`} className='morph-evomap-item'>
                <div className='morph-evomap-meta'>
                  <span className='morph-evomap-id' title={String(geneId)}>{String(geneId)}</span>
                  {num(gene.weight) !== null ? <span>权重 {num(gene.weight)}</span> : null}
                  {gene.use_count !== undefined ? <span>采用 {gene.use_count}</span> : null}
                  {gene.archived_at != null ? <span>已归档</span> : null}
                </div>
                {trigger ? <p className='morph-evomap-trigger'>触发：{trigger}</p> : null}
                {typeof gene.strategy === 'string' && gene.strategy ? <p className='morph-evomap-summary'>{gene.strategy.slice(0, 160)}</p> : null}
              </li>
            );
          })}
          {genes.length > 8 ? <li className='morph-evomap-line'>其余 {genes.length - 8} 条省略。</li> : null}
        </ul>
      ) : null}
      {(pool.notes ?? []).map((note, index) => <p key={index} className='morph-evomap-line'>{note}</p>)}
    </div>
  );
};

const EvoMapPanel = ({ evomap, onSearch }) => {
  const data = evomap.data;
  const search = data?.community_search;
  const [form, setForm] = useState({ q: 'repair', type: '', limit: 10 });
  // Echo the server's actual applied query into the form once data arrives.
  useEffect(() => {
    if (search?.query) {
      setForm({ q: search.query.q ?? 'repair', type: search.query.type ?? '', limit: search.query.limit ?? 10 });
    }
  }, [search?.query?.q, search?.query?.type, search?.query?.limit]);

  const submit = (event) => {
    event.preventDefault();
    if (!evomap.loading) onSearch({ q: form.q.trim() || 'repair', type: form.type || undefined, limit: form.limit });
  };

  return (
    <section className='morph-evomap' aria-label='EvoMap 只读探索'>
      <div className='morph-evomap-head'>
        <span className='morph-panel-title'>EvoMap · 只读探索</span>
        <span className='morph-evomap-tag'>独立端点 /api/evomap · 非运行拓扑</span>
        {search ? <StateChip state={search.state} /> : null}
      </div>
      <form className='morph-evomap-form' onSubmit={submit}>
        <input
          type='search'
          value={form.q}
          maxLength={500}
          placeholder='搜索社区资产（q）'
          aria-label='EvoMap 搜索关键词'
          onChange={(event) => setForm((prev) => ({ ...prev, q: event.target.value }))}
        />
        <select value={form.type} aria-label='资产类型' onChange={(event) => setForm((prev) => ({ ...prev, type: event.target.value }))}>
          {ASSET_TYPES.map((type) => <option key={type || 'all'} value={type}>{type || '全部类型'}</option>)}
        </select>
        <select value={form.limit} aria-label='条数上限' onChange={(event) => setForm((prev) => ({ ...prev, limit: Number(event.target.value) }))}>
          {LIMITS.map((limit) => <option key={limit} value={limit}>{limit} 条</option>)}
        </select>
        <button type='submit' disabled={evomap.loading}>{evomap.loading ? '请求中…' : '搜索'}</button>
        <button type='button' disabled={evomap.loading || evomap.state === 'idle' || evomap.state === 'missing'}
          onClick={() => onSearch(undefined)}>刷新</button>
      </form>

      {evomap.state === 'idle' ? <p className='morph-evomap-line'>进入信息界面后读取一次；之后仅手动搜索/刷新，不轮询。</p> : null}
      {evomap.state === 'loading' ? <p className='morph-evomap-line'>正在读取 EvoMap 状态…</p> : null}
      {evomap.state === 'missing' ? <p className='morph-evomap-line'>/api/evomap 尚未提供（E 轨合入后启用）；未配置时不展示推断信息。</p> : null}
      {evomap.state === 'invalid' ? <p className='morph-evomap-line'>参数无效：{evomap.detail}</p> : null}
      {evomap.state === 'error' ? <p className='morph-evomap-line'>EvoMap 状态不可用：{evomap.detail}</p> : null}
      {evomap.loading && data ? <p className='morph-evomap-line'>更新中…以下为上次结果。</p> : null}
      {(evomap.state === 'error' || evomap.state === 'invalid') && data ? (
        <p className='morph-evomap-line morph-evomap-stale-note'>当前查询失败；以下为上次成功结果，状态以其自身标注为准。</p>
      ) : null}

      {data ? (
        <div className='morph-evomap-body'>
          {data.hub ? (
            <p className='morph-evomap-line'>
              Hub {data.hub.base_url}{data.hub.endpoint} · {data.hub.auth} · API key {data.hub.api_key_configured ? '已配置' : '未配置'}
              {data.generated_at ? ` · 生成于 ${new Date(data.generated_at * 1000).toTimeString().slice(0, 8)}` : ''}
            </p>
          ) : null}

          {search ? (
            <div className='morph-evomap-section'>
              <span className='morph-evomap-key'>
                社区搜索 <StateChip state={search.state} />
                {search.count !== undefined ? ` · ${search.count} 条` : ''}
                {search.provider ? ` · provider ${search.provider}` : ''}
                {search.search_status ? ` · ${search.search_status}` : ''}
              </span>
              <p className='morph-evomap-line'>
                查询 q=“{search.query?.q}”{search.query?.type ? ` · type=${search.query.type}` : ''} · limit={search.query?.limit}
                {search.cache_age_seconds != null ? ` · 缓存年龄 ${Math.round(search.cache_age_seconds)}s / TTL ${Math.round(search.cache_ttl_seconds ?? 0)}s` : ''}
                {search.error ? ` · 错误码 ${search.error}` : ''}
              </p>
              {Array.isArray(search.assets) && search.assets.length ? (
                <ul className='morph-evomap-list'>
                  {search.assets.map((asset, index) => <AssetCard key={asset.asset_id ?? index} asset={asset} />)}
                </ul>
              ) : (
                <p className='morph-evomap-line'>{search.state === 'error' ? '本次获取失败，无资产列表。' : '该查询无返回资产。'}</p>
              )}
            </div>
          ) : null}

          <Categories categories={data.community_categories} />
          <LocalPool pool={data.local_pool} />

          {Array.isArray(data.boundaries) && data.boundaries.length ? (
            <ul className='morph-evomap-boundaries'>
              {data.boundaries.map((line, index) => <li key={index}>{line}</li>)}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  );
};

export default React.memo(EvoMapPanel);
