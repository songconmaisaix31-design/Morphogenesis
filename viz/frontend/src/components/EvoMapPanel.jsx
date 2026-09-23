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
  not_applicable: 'n/a · 不适用', unknown: 'unknown · 未知',
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
// The detail view opens strictly on demand via the 详情 button — cards never
// prefetch, so rendering a result list fires zero extra requests.
const AssetCard = ({ asset, onOpen }) => {
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
        {asset.asset_id ? (
          <button type='button' className='morph-evomap-asset-open'
            onClick={() => onOpen?.(asset.asset_id)}>详情</button>
        ) : null}
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

// On-demand asset detail, frozen E-track contract morph.evomap.asset/1:
// GET /api/evomap/asset?id=<asset_id> returns one JSON with three blocks —
// asset_detail / asset_timeline / gene_branches — each carrying its own
// state (live|cache|stale_cache|error, plus not_applicable|unknown for
// gene_branches), fetched_at, cache ages and a fixed error code. Click-only,
// never polled; missing keys render nothing; no detail data ever feeds the
// runtime topology views.
const DETAIL_FIELDS = [
  ['类型', (a) => a.asset_type], ['状态', (a) => a.status], ['trust', (a) => a.trust_tier],
  ['GDI', (a) => num(a.gdi_score)], ['相似度', (a) => num(a.similarity)],
  ['赞/踩', (a) => (a.upvotes !== undefined || a.downvotes !== undefined ? `${a.upvotes ?? 0}/${a.downvotes ?? 0}` : null)],
  ['我的投票', (a) => a.user_vote],
  ['查看', (a) => a.view_count], ['复用', (a) => a.reuse_count],
  ['分叉', (a) => a.fork_count], ['迭代', (a) => a.iteration_count],
  ['版本', (a) => a.version], ['域名', (a) => a.domain],
  ['来源节点', (a) => a.source_node_alias ?? a.source_node_id],
  ['创建', (a) => a.created_at], ['更新', (a) => a.updated_at],
  ['捆绑 Capsule', (a) => (typeof a.bundle_capsule === 'string' ? a.bundle_capsule : null)],
  ['谱系', (a) => (a.lineage && typeof a.lineage === 'object' ? JSON.stringify(a.lineage).slice(0, 200) : a.lineage ?? null)],
];

const BlockMeta = ({ block }) => {
  if (!block) return null;
  const bits = [];
  if (block.cache_age_seconds != null) bits.push(`缓存年龄 ${Math.round(block.cache_age_seconds)}s / TTL ${Math.round(block.cache_ttl_seconds ?? 0)}s`);
  if (block.fetched_at == null && block.state) bits.push('从未成功获取');
  if (block.error) bits.push(`错误码 ${block.error}`);
  return bits.length ? <p className='morph-evomap-line'>{bits.join(' · ')}</p> : null;
};

const BranchCard = ({ branch }) => {
  const capsules = Array.isArray(branch?.capsules) ? branch.capsules : [];
  const meta = [
    ['Capsule', branch?.capsule_count], ['平均 GDI', num(branch?.avg_gdi)],
    ['平均置信', num(branch?.avg_confidence)], ['成功率', num(branch?.success_rate)],
  ].filter(([, value]) => value !== null && value !== undefined);
  return (
    <li className='morph-evomap-branch'>
      <div className='morph-evomap-asset-head'>
        <strong>{branch?.node_alias ?? branch?.node_id ?? '未命名节点'}</strong>
      </div>
      {meta.length ? (
        <div className='morph-evomap-meta'>
          {meta.map(([key, value]) => <span key={key}>{key} {String(value)}</span>)}
        </div>
      ) : null}
      {branch?.best_capsule ? (
        <p className='morph-evomap-summary'>
          最佳 Capsule{num(branch.best_capsule.gdi_score) !== null ? `（GDI ${num(branch.best_capsule.gdi_score)}）` : ''}：
          {branch.best_capsule.summary ?? branch.best_capsule.asset_id ?? ''}
        </p>
      ) : null}
      {capsules.length ? (
        <div className='morph-evomap-meta'>
          {capsules.map((capsule, index) => (
            <span key={capsule?.asset_id ?? index} className='morph-evomap-id' title={capsule?.asset_id ? String(capsule.asset_id) : undefined}>
              {String(capsule?.asset_id ?? '').slice(0, 12)}…{capsule?.status ? ` ${capsule.status}` : ''}{num(capsule?.gdi_score) !== null ? ` GDI ${num(capsule.gdi_score)}` : ''}
            </span>
          ))}
        </div>
      ) : null}
    </li>
  );
};

const AssetDetail = ({ detail }) => {
  if (!detail || detail.state === 'idle') return null;
  const data = detail.data;
  const block = data && typeof data === 'object' ? data : {};
  const detailBlock = block.asset_detail && typeof block.asset_detail === 'object' ? block.asset_detail : null;
  const timelineBlock = block.asset_timeline && typeof block.asset_timeline === 'object' ? block.asset_timeline : null;
  const branchesBlock = block.gene_branches && typeof block.gene_branches === 'object' ? block.gene_branches : null;
  const asset = detailBlock?.asset && typeof detailBlock.asset === 'object' ? detailBlock.asset : null;
  const events = Array.isArray(timelineBlock?.events) ? timelineBlock.events : [];
  const branches = Array.isArray(branchesBlock?.branches) ? branchesBlock.branches : [];
  const notFound = detailBlock?.error === 'http_404';
  return (
    <div className='morph-evomap-section morph-evomap-detail' aria-label='资产按需详情'>
      <span className='morph-evomap-key'>
        资产详情 · 点击按需加载
        {detail.assetId ? <span className='morph-evomap-id' title={detail.assetId}>id {String(detail.assetId).slice(0, 12)}…</span> : null}
      </span>
      {detail.state === 'loading' ? <p className='morph-evomap-line'>正在读取资产详情…</p> : null}
      {detail.state === 'missing' ? <p className='morph-evomap-line'>资产详情端点尚未提供（等待 E 轨合入）；不展示推断信息。</p> : null}
      {detail.state === 'not_found' ? <p className='morph-evomap-line'>资产不存在或不可读取（asset_not_found）。</p> : null}
      {detail.state === 'invalid' ? <p className='morph-evomap-line'>详情请求参数无效：{detail.detail}</p> : null}
      {detail.state === 'error' ? <p className='morph-evomap-line'>详情读取失败：{detail.detail}</p> : null}
      {detail.state === 'ok' && data ? (
        <div className='morph-evomap-detail-body'>
          {block.hub ? (
            <p className='morph-evomap-line'>
              Hub {block.hub.base_url}{block.hub.asset_endpoint} · {block.hub.auth} · API key {block.hub.api_key_configured ? '已配置' : '未配置'}
              {block.generated_at ? ` · 生成于 ${new Date(block.generated_at * 1000).toTimeString().slice(0, 8)}` : ''}
            </p>
          ) : null}
          {notFound ? <p className='morph-evomap-line'>资产不存在或不可读取（Hub 404 / asset_not_found）。</p> : null}

          <div className='morph-evomap-detail-col'>
            <span className='morph-evomap-key'>资产详情{detailBlock?.state ? <StateChip state={detailBlock.state} /> : null}</span>
            <BlockMeta block={detailBlock} />
            {asset ? (
              <div className='morph-evomap-detail-asset'>
                <div className='morph-evomap-asset-head'>
                  <strong>{asset.short_title || asset.asset_id || '未命名资产'}</strong>
                </div>
                {asset.nl_summary ? <p className='morph-evomap-summary'>{asset.nl_summary}</p> : null}
                {asset.trigger_text ? <p className='morph-evomap-trigger'>触发：{asset.trigger_text}</p> : null}
                <div className='morph-evomap-meta'>
                  {DETAIL_FIELDS.map(([key, pick]) => {
                    const value = pick(asset);
                    return value !== null && value !== undefined && value !== ''
                      ? <span key={key}>{key} {String(value)}</span>
                      : null;
                  })}
                </div>
              </div>
            ) : (detailBlock && !notFound ? <p className='morph-evomap-line'>{detailBlock.state === 'error' ? '详情获取失败，无资产字段。' : '端点未返回资产详情字段（空结果）。'}</p> : null)}
          </div>

          <div className='morph-evomap-detail-col'>
            <span className='morph-evomap-key'>
              演化时间线{timelineBlock?.state ? <StateChip state={timelineBlock.state} /> : null}
              {timelineBlock?.total != null ? ` · 共 ${timelineBlock.total} 条` : ''}
              {timelineBlock?.asset_type ? ` · ${timelineBlock.asset_type}` : ''}
            </span>
            <BlockMeta block={timelineBlock} />
            {events.length ? (
              <ol className='morph-evomap-timeline'>
                {events.map((event, index) => (
                  <li key={index}>
                    {event?.timestamp != null ? <span className='morph-evomap-id'>{String(event.timestamp)}</span> : null}
                    {event?.type != null ? <span>{String(event.type)}</span> : null}
                    {event?.description != null ? <span className='morph-evomap-line'>{String(event.description)}</span> : null}
                  </li>
                ))}
              </ol>
            ) : (timelineBlock?.state === 'error' ? null : <p className='morph-evomap-line'>无演化时间线记录（空结果）。</p>)}
          </div>

          <div className='morph-evomap-detail-col'>
            <span className='morph-evomap-key'>
              基因分支{branchesBlock?.state ? <StateChip state={branchesBlock.state} /> : null}
              {branchesBlock?.total_branches != null ? ` · ${branchesBlock.total_branches} 分支` : ''}
              {branchesBlock?.total_capsules != null ? ` · ${branchesBlock.total_capsules} Capsule` : ''}
            </span>
            {branchesBlock?.state === 'not_applicable' ? <p className='morph-evomap-line'>非 Gene 资产，不请求分支。</p> : null}
            {branchesBlock?.state === 'unknown' ? <p className='morph-evomap-line'>详情获取失败，无法判定是否 Gene，未请求分支。</p> : null}
            <BlockMeta block={branchesBlock} />
            {branchesBlock?.gene_summary ? <p className='morph-evomap-summary'>{branchesBlock.gene_summary}</p> : null}
            {branches.length ? (
              <ul className='morph-evomap-list'>
                {branches.map((branch, index) => <BranchCard key={branch?.node_id ?? index} branch={branch} />)}
              </ul>
            ) : (branchesBlock && !['error', 'not_applicable', 'unknown'].includes(branchesBlock.state)
              ? <p className='morph-evomap-line'>该 Gene 无分支记录（空结果）。</p> : null)}
          </div>

          {Array.isArray(block.boundaries) && block.boundaries.length ? (
            <ul className='morph-evomap-boundaries'>
              {block.boundaries.map((line, index) => <li key={index}>{line}</li>)}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
};

const EvoMapPanel = ({ evomap, detail, onSearch, onOpenAsset }) => {
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
                  {search.assets.map((asset, index) => <AssetCard key={asset.asset_id ?? index} asset={asset} onOpen={onOpenAsset} />)}
                </ul>
              ) : (
                <p className='morph-evomap-line'>{search.state === 'error' ? '本次获取失败，无资产列表。' : '该查询无返回资产。'}</p>
              )}
            </div>
          ) : null}

          <AssetDetail detail={detail} />

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
