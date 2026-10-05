/* ============================================================
 * 环境观测台 · 视图层 v4
 * GitHub Dashboard 1:1 复刻（Morphogenesis 版）
 * 数据全部来自 EnvData（API_CONTRACT.md §10 数据层约定）。
 * ============================================================ */
(function () {
'use strict';

/* ---------- 小工具 ---------- */
function $(id) { return document.getElementById(id); }
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}
function h(html) { var t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; }
function on(id, ev, fn) { var n = typeof id === 'string' ? $(id) : id; if (n) n.addEventListener(ev, fn); }

var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
function pad(n) { return (n < 10 ? '0' : '') + n; }
function fmtDate(ts) { var d = new Date(ts * 1000); return MONTHS[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear(); }
function fmtTime(ts) { var d = new Date(ts * 1000); return pad(d.getHours()) + ':' + pad(d.getMinutes()); }

/* ---------- 状态 ---------- */
var PKG = null, SNAP = null;
var BRANCH = {}, TASK = {}, OPP = [];
var taskSort = 'updated';

/* ---------- 文案映射 ---------- */
var STATUS_ZH = { available: '待认领', partial: '部分完成', handoff: '待转交', claimed: '进行中', submitting: '提交中', completed: '已完成', failed: '失败', blocked: '阻塞' };
var BRANCH_ZH = { proposed: '提议', exploring: '探索', testing: '验证中', supported: '已支持', disputed: '争议', dormant: '休眠', refuted: '已反驳', archived: '已归档' };
var REASON_ZH = { eligible: 'eligible', insufficient_evidence: '证据不足', unknown_cost: '成本未知', refuted_under_conditions: '条件下被反驳', dormant: '休眠', archived: '已归档', out_of_scope: '越界' };

/* ---------- 契约 §5：actor 提取 + 事件文案 ---------- */
function actorOf(body) {
  if (!body) return 'swarm';
  if (body.worker_id) return body.worker_id;
  if (body.from) return body.from;
  if (body.payload && body.payload.worker_id) return body.payload.worker_id;
  if (body.actor && body.actor.role != null) return body.actor.role + '-' + body.actor.instance;
  return 'swarm';
}
function taskOf(e) { return e.task_id || (e.body && e.body.task_id) || ''; }
function normEvent(ev) { return ev.indexOf('research.') === 0 ? 'research_' + ev.slice(9) : ev; }
function phrase(e) {
  var b = e.body || {};
  var p = b.payload || b;
  switch (normEvent(e.event)) {
    case 'created': return '任务创建' + (b.derived_from ? ' · 派生自 ' + b.derived_from : '');
    case 'claimed': return actorOf(b) + ' 认领 ' + taskOf(e);
    case 'renewed': return actorOf(b) + ' 续租' + (b.expires_at ? ' · 至 ' + fmtTime(b.expires_at) : '');
    case 'released': return '释放' + (b.evidence ? ' · ' + b.evidence : '');
    case 'handoff': return (b.from || '?') + ' → ' + (b.to || '?') + ' 转交';
    case 'completed': return taskOf(e) + ' 完成' + (b.result_id ? ' · 结果已留痕 ' + b.result_id : '');
    case 'failed': return taskOf(e) + ' 失败' + (b.evidence ? ' · ' + b.evidence : '');
    case 'blocked': return taskOf(e) + ' 阻塞 · 条件失败 ×' + (b.condition_fail_count || 0);
    case 'policy_selection': return '策略选择 ' + (b.actual_task_id || '') + (b.reason ? ' · ' + b.reason : '');
    case 'research_choice': return actorOf(b) + ' 选择 ' + (p.selected || '') + (p.overridden ? '（覆盖推荐 ' + p.recommended_task_id + '）' : '');
    case 'research_selection': return actorOf(b) + ' 认领 ' + (p.actual_task_id || taskOf(e));
    case 'research_execution': return '隔离执行 run:' + (b.run_id || '') + (b.result ? ' · ' + b.result : '');
    case 'execution_confirmed': return '实验完成 · 效果 known';
    case 'execution_unconfirmed': return '执行未确认 · 待归档复核';
    case 'note_submitted': return '写入痕迹 ' + (p.note_id || '') + (p.kind ? ' · kind=' + p.kind : '');
    case 'contribution_accepted': return '经验命中 ' + (p.result_id || '');
    case 'proposal_accepted': return '提议准入 ' + (p.proposal_id || '');
    case 'branch_sleep': return '分支休眠 ' + (b.branch_id || '') + (p.reason ? ' · ' + p.reason : '');
    case 'branch_downgrade': return '分支降级 ' + (b.branch_id || '');
    case 'branch_reopen': return '分支重开 ' + (b.branch_id || '') + (p.reason ? ' · ' + p.reason : '');
    case 'contribution_superseded': return '贡献取代 ' + (p.result_id || '') + (p.reason ? ' · ' + p.reason : '');
    case 'project_created': return '项目创建';
    case 'branch_created': return '分支创建 ' + (b.branch_id || '');
  }
  return e.event;
}
function toneOf(e) {
  var n = normEvent(e.event);
  if (n === 'contribution_accepted' || n === 'proposal_accepted') return 'gold';
  if (n === 'failed' || n === 'blocked' || n === 'branch_sleep' || n === 'contribution_superseded') return 'red';
  if (n === 'completed' || n === 'execution_confirmed') return 'green';
  if (n === 'claimed' || n === 'research_selection' || n === 'research_choice' || n === 'policy_selection') return 'blue';
  return 'gray';
}

/* ---------- 图标 ---------- */
var ICO_PR = '<svg class="row-ico ico-green" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z"/></svg>';
var ICO_ISSUE_RED = '<svg class="row-ico ico-red" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z"/></svg>';
var ICO_ISSUE_GOLD = '<svg class="row-ico ico-gold" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z"/></svg>';
var ICO_DONE = '<svg class="row-ico ico-purple" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M8 16A8 8 0 1 1 8 0a8 8 0 0 1 0 16Zm3.78-9.72a.751.751 0 0 0-.018-1.042.751.751 0 0 0-1.042-.018L6.75 9.19 5.28 7.72a.751.751 0 0 0-1.042.018.751.751 0 0 0-.018 1.042l2 2a.75.75 0 0 0 1.06 0Z"/></svg>';
var ICO_KEBAB = '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M8 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM1.5 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Zm13 0a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z"/></svg>';

/* ---------- 图层栈（Esc 关闭最上层） ---------- */
var LAYERS = [];
function pushLayer(name, closeFn) { LAYERS.push({ name: name, close: closeFn }); }
function closeTop() { var l = LAYERS.pop(); if (l) l.close(); }

/* ---------- 下拉 ---------- */
var ddOpen = null, ddTrigger = null;
function toggleDD(el, trigger) {
  if (ddOpen === el) { closeDD(); return; }
  closeDD();
  el.hidden = false;
  ddOpen = el; ddTrigger = trigger || null;
}
function closeDD() { if (ddOpen) { ddOpen.hidden = true; ddOpen = null; ddTrigger = null; } }
document.addEventListener('click', function (ev) {
  if (!ddOpen) return;
  if (ddOpen.contains(ev.target)) return;
  if (ddTrigger && ddTrigger.contains(ev.target)) return;
  closeDD();
});
function placeFixed(el, anchor) {
  var r = anchor.getBoundingClientRect();
  el.style.top = (r.bottom + 6) + 'px';
  el.style.left = Math.max(8, Math.min(r.right - 220, window.innerWidth - 240)) + 'px';
}

/* ---------- 抽屉 ---------- */
function openDrawer(overlayId, panelId) {
  var ov = $(overlayId), panel = $(panelId);
  ov.hidden = false; panel.hidden = false;
  requestAnimationFrame(function () { panel.classList.add('is-open'); });
  pushLayer(panelId, function () { closeDrawer(overlayId, panelId); });
}
function closeDrawer(overlayId, panelId) {
  var ov = $(overlayId), panel = $(panelId);
  panel.classList.remove('is-open');
  setTimeout(function () { ov.hidden = true; panel.hidden = true; }, 200);
  LAYERS = LAYERS.filter(function (l) { return l.name !== panelId; });
}

/* ---------- Toast ---------- */
var toastTimer = null;
function toast(msg) {
  var t = $('toast');
  t.textContent = msg;
  t.hidden = false;
  requestAnimationFrame(function () { t.classList.add('is-on'); });
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function () {
    t.classList.remove('is-on');
    setTimeout(function () { t.hidden = true; }, 220);
  }, 2400);
}

/* ---------- 视图路由 ---------- */
var VIEWS = ['home', 'signals', 'feed'];
function currentView() {
  var m = (location.hash || '').match(/^#\/(\w+)/);
  return m && VIEWS.indexOf(m[1]) >= 0 ? m[1] : 'home';
}
function switchView(v) {
  if (('#/' + v) === location.hash) { applyView(); return; }
  location.hash = '#/' + v;
}
function applyView() {
  var v = currentView();
  VIEWS.forEach(function (x) { $('view-' + x).hidden = x !== v; });
  document.querySelectorAll('.side-link').forEach(function (a) {
    a.classList.toggle('is-active', a.getAttribute('data-view') === v);
  });
  document.body.classList.remove('nav-open');
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', applyView);

/* ---------- 问候（1:1 Good evening） ---------- */
function renderGreeting() {
  var hr = new Date().getHours();
  var g = hr < 5 ? 'Working late' : hr < 12 ? 'Good morning' : hr < 18 ? 'Good afternoon' : 'Good evening';
  $('greetTitle').textContent = g + ', swarm-gen-1!';
  var goal = PKG && PKG.context && PKG.context.project ? PKG.context.project.goal : '';
  $('greetSub').textContent = '项目 p1 · ' + goal;
}

/* ---------- 侧栏分支（1:1 Top repositories） ---------- */
var branchQuery = '';
function avatarClass(id) {
  if (/soft/.test(id)) return 'b-soft';
  if (/hard/.test(id)) return 'b-hard';
  return 'b-hybrid';
}
function oppOf(branchId) {
  for (var i = 0; i < OPP.length; i++) if (OPP[i].branch_id === branchId) return OPP[i];
  return null;
}
function renderBranches() {
  var list = $('branchList');
  list.innerHTML = '';
  var items = SNAP.branches.slice().sort(function (a, b) {
    var oa = oppOf(a.branch_id), ob = oppOf(b.branch_id);
    return (ob ? ob.share : 0) - (oa ? oa.share : 0);
  });
  if (branchQuery) {
    items = items.filter(function (b) { return b.branch_id.toLowerCase().indexOf(branchQuery) >= 0; });
  }
  if (!items.length) {
    list.innerHTML = '<li class="muted loading-line">No branches found</li>';
  } else {
    items.forEach(function (b) {
      var li = h('<li><a class="branch-item" href="#/branches">'
        + '<span class="branch-avatar ' + avatarClass(b.branch_id) + '"></span>'
        + '<span class="branch-name">p1 / <b>' + esc(b.branch_id) + '</b></span>'
        + '<span class="branch-status">' + esc(BRANCH_ZH[b.status] || b.status) + '</span>'
        + '</a></li>');
      li.querySelector('a').addEventListener('click', function (ev) {
        ev.preventDefault();
        openWayfinder(b.branch_id);
      });
      list.appendChild(li);
    });
  }
  $('branchMore').hidden = SNAP.branches.length <= 5;
}

/* ---------- In-flight tasks（1:1 Pull requests） ---------- */
function inflightTasks() {
  var rows = PKG.tasks.filter(function (t) { return t.status === 'claimed' || t.status === 'submitting'; });
  if (taskSort === 'created') rows.sort(function (a, b) { return b.created_at - a.created_at; });
  else if (taskSort === 'owner') rows.sort(function (a, b) { return String(a.owner).localeCompare(String(b.owner)); });
  else rows.sort(function (a, b) { return b.updated_at - a.updated_at; });
  return rows;
}
function branchTag(branchId) {
  return branchId ? '<span class="tag tag-branch">' + esc(branchId) + '</span>' : '<span class="tag">no-branch</span>';
}
function statusPill(status) {
  var cls = status === 'claimed' ? 'pill-green' : status === 'submitting' ? 'pill-gold'
    : status === 'completed' ? 'pill-purple' : status === 'failed' || status === 'blocked' ? 'pill-red'
    : status === 'handoff' ? 'pill-blue' : 'pill-gray';
  return '<span class="pill ' + cls + '">' + esc(status) + '</span>';
}
function taskRow(t, icon, metaExtra) {
  var s = t.signal;
  var branch = s.payload.branch_id;
  var meta = 'p1/' + (branch || 'inbox') + '#' + s.task_id
    + ' · ' + (t.owner ? 'Claimed by ' + esc(t.owner) : 'Unclaimed')
    + ' · Updated ' + fmtDate(t.updated_at)
    + (metaExtra ? ' · ' + metaExtra : '');
  var li = h('<li class="gh-row">'
    + icon
    + '<div class="row-main">'
    + '<a class="row-title" data-open-replay="' + esc(s.task_id) + '">' + esc(s.payload.goal) + '</a>'
    + '<div class="row-meta">' + meta + '</div>'
    + '</div>'
    + branchTag(branch)
    + statusPill(t.status)
    + '<div class="row-actions">'
    + '<button class="row-action" data-open-replay="' + esc(s.task_id) + '">Open in replay</button>'
    + '<button class="hbtn hbtn-sm row-menu" data-menu="' + esc(s.task_id) + '" aria-label="Task actions">' + ICO_KEBAB + '</button>'
    + '</div>'
    + '</li>');
  return li;
}
function renderTasks() {
  var list = $('taskList');
  list.innerHTML = '';
  var rows = inflightTasks();
  $('taskListEmpty').hidden = rows.length > 0;
  rows.forEach(function (t) { list.appendChild(taskRow(t, ICO_PR, null)); });
}

/* ---------- Signals 视图（1:1 Issues + 泳道） ---------- */
function matchFilter(t, q) {
  if (!q) return true;
  var s = t.signal;
  var hay = (s.task_id + ' ' + s.payload.goal + ' ' + (s.payload.branch_id || '') + ' ' + (t.owner || '') + ' ' + t.status).toLowerCase();
  return hay.indexOf(q) >= 0;
}
function evidenceOf(taskId) {
  for (var i = PKG.task_audit.length - 1; i >= 0; i--) {
    var e = PKG.task_audit[i];
    if (e.task_id === taskId && e.event === 'failed' && e.body && e.body.evidence) return e.body.evidence;
  }
  return null;
}
function renderSignals() {
  var q = ($('homeFilterInput').value || '').trim().toLowerCase();
  var needs = [], pool = [], sediment = [];
  PKG.tasks.forEach(function (t) {
    if (!matchFilter(t, q)) return;
    if (t.status === 'failed' || t.status === 'blocked') needs.push(t);
    else if (t.status === 'available' || t.status === 'partial' || t.status === 'handoff') pool.push(t);
    else if (t.status === 'completed') sediment.push(t);
  });
  needs.sort(function (a, b) { return b.updated_at - a.updated_at; });
  pool.sort(function (a, b) { return b.updated_at - a.updated_at; });
  sediment.sort(function (a, b) { return b.updated_at - a.updated_at; });

  var il = $('issueList'); il.innerHTML = '';
  needs.forEach(function (t) {
    var extra = t.status === 'failed' ? (evidenceOf(t.signal.task_id) ? 'evidence: ' + esc(evidenceOf(t.signal.task_id)) : null)
      : '条件失败 ×' + t.condition_fail_count;
    il.appendChild(taskRow(t, ICO_ISSUE_RED, extra));
  });
  $('issueListEmpty').hidden = needs.length > 0;

  var pl = $('poolList'); pl.innerHTML = '';
  pool.forEach(function (t) { pl.appendChild(taskRow(t, ICO_ISSUE_GOLD, 'capability: ' + esc(t.signal.required_capability))); });
  $('poolCount').textContent = pool.length + ' open';

  var sl = $('sedimentList'); sl.innerHTML = '';
  sediment.forEach(function (t) { sl.appendChild(taskRow(t, ICO_DONE, t.result_id ? 'result: ' + esc(t.result_id) : null)); });
  $('sedimentCount').textContent = sediment.length + ' settled';

  var attn = PKG.tasks.filter(function (t) { return t.status === 'failed' || t.status === 'blocked'; }).length;
  var badge = $('navSignalCount');
  badge.hidden = attn === 0;
  badge.textContent = attn;
}

/* ---------- Feed（task_audit 全量） ---------- */
function feedItem(e, live) {
  var li = h('<li class="feed-item' + (live ? ' is-live' : '') + '">'
    + '<span class="dot dot-' + toneOf(e) + '"></span>'
    + '<span class="feed-text">' + esc(phrase(e)) + '</span>'
    + '<span class="feed-meta">' + esc(taskOf(e)) + ' · ' + fmtTime(e.at) + '</span>'
    + '</li>');
  li.addEventListener('click', function () { if (taskOf(e)) openReplay(taskOf(e)); });
  return li;
}
function renderFeed() {
  var list = $('feedList');
  list.innerHTML = '';
  PKG.task_audit.forEach(function (e) { list.appendChild(feedItem(e, false)); });
  $('feedCount').textContent = PKG.task_audit.length + ' events · sequence 升序';
}

/* ---------- Ledger（1:1 Latest from our changelog） ---------- */
var LEDGER_KINDS = { completed: 1, failed: 1, blocked: 1, research_contribution_accepted: 1, research_branch_sleep: 1, research_branch_reopen: 1, research_proposal_accepted: 1, research_contribution_superseded: 1 };
function renderLedger() {
  var box = $('ledgerList');
  box.innerHTML = '';
  var items = PKG.task_audit.filter(function (e) { return LEDGER_KINDS[normEvent(e.event)]; })
    .slice().sort(function (a, b) { return b.sequence - a.sequence; })
    .slice(0, 6);
  var lastDay = null;
  items.forEach(function (e) {
    var day = fmtDate(e.at);
    if (day !== lastDay) {
      box.appendChild(h('<div class="ledger-day">' + esc(day) + '</div>'));
      lastDay = day;
    }
    var row = h('<div class="ledger-item"><span class="dot dot-' + toneOf(e) + '"></span><span class="ledger-link">' + esc(phrase(e)) + '</span></div>');
    row.addEventListener('click', function () { switchView('feed'); });
    box.appendChild(row);
  });
}

/* ---------- 专家意见（kind=expert_opinion，恒 unverified） ---------- */
function renderExperts() {
  var notes = (PKG.context.notes || []).filter(function (n) { return n.kind === 'expert_opinion'; });
  var box = $('expertList');
  box.innerHTML = '';
  var badge = $('expertCount');
  badge.hidden = notes.length === 0;
  badge.textContent = notes.length;
  notes.forEach(function (n) {
    var signer = n.signer || 'anonymous';
    var src = (n.source_refs && n.source_refs.length)
      ? '<div class="expert-src mono">' + esc(n.source_refs[0].identifier) + ' · ' + esc(n.source_refs[0].location) + '</div>' : '';
    box.appendChild(h('<div class="expert">'
      + '<div class="expert-head">'
      + '<span class="expert-avatar">' + esc(signer.replace(/^(Dr\.|Prof\.)\s*/, '').charAt(0)) + '</span>'
      + '<span class="expert-name">' + esc(signer) + '</span>'
      + (n.branch_id ? '<span class="tag tag-branch">' + esc(n.branch_id) + '</span>' : '')
      + '<span class="pill pill-gold">' + esc(n.review_state) + '</span>'
      + '</div>'
      + '<p class="expert-text">' + esc(n.text) + '</p>'
      + src
      + '</div>'));
  });
}

/* ---------- 通知（1:1 unread dot） ---------- */
var unread = 0;
function pushNotif(e) {
  var li = h('<li class="notif-item"><span class="dot dot-' + toneOf(e) + '"></span>'
    + '<div><div class="notif-text">' + esc(phrase(e)) + '</div>'
    + '<div class="notif-meta muted">' + esc(taskOf(e)) + ' · ' + fmtTime(e.at) + '</div></div></li>');
  li.addEventListener('click', function () {
    closeDD();
    if (taskOf(e)) openReplay(taskOf(e));
  });
  $('notifList').prepend(li);
  $('notifEmpty').hidden = true;
  unread++;
  $('notifDot').hidden = false;
}
function toggleNotif() {
  var panel = $('notifPanel');
  if (panel.hidden) {
    toggleDD(panel, $('notifBtn'));
    unread = 0;
    $('notifDot').hidden = true;
    $('notifMeta').textContent = '· all caught up';
  } else closeDD();
}

/* ---------- Wayfinder ---------- */
function renderWayfinder(focusId) {
  var box = $('wfRoutes');
  box.innerHTML = '';
  if (!OPP.length) {
    box.innerHTML = '<p class="muted">暂无机会数据。</p>';
    $('wfReadout').textContent = '—';
    return;
  }
  OPP.forEach(function (o) {
    var b = BRANCH[o.branch_id] || {};
    var f = o.factors;
    var reasons = (o.reasons || []).map(function (r) { return '<span class="tag">' + esc(REASON_ZH[r] || r) + '</span>'; }).join('');
    var node = h('<button class="wf-route' + (o.branch_id === focusId ? ' is-focus' : '') + (o.eligible ? '' : ' is-ineligible') + '">'
      + '<div class="wf-route-top">'
      + '<span class="branch-avatar ' + avatarClass(o.branch_id) + '"></span>'
      + '<b class="mono">' + esc(o.branch_id) + '</b>'
      + '<span class="pill ' + (o.eligible ? 'pill-green' : 'pill-red') + '">' + (o.eligible ? 'eligible' : 'ineligible') + '</span>'
      + '<span class="wf-share">' + Math.round(o.share * 100) + '%</span>'
      + '</div>'
      + '<div class="share-bar"><i style="width:' + Math.round(o.share * 100) + '%"></i></div>'
      + '<div class="wf-factors muted">evidence ' + f.evidence + ' · applicability ' + f.applicability + ' · goal ' + f.goal_relevance + ' · risk ' + f.risk + '</div>'
      + '<div class="wf-factors muted">支持 ×' + f.support_count + ' / 反驳 ×' + f.refute_count + ' · 成本 ' + (o.known_cost == null ? '—' : o.known_cost) + ' · 状态 ' + esc(BRANCH_ZH[b.status] || b.status || '—') + '</div>'
      + (reasons ? '<div class="wf-reasons">' + reasons + '</div>' : '')
      + '</button>');
    node.addEventListener('click', function () { setReadout(o); });
    box.appendChild(node);
  });
  var focus = null;
  if (focusId) focus = oppOf(focusId);
  setReadout(focus || OPP[0]);
}
function setReadout(o) {
  $('wfReadout').innerHTML = '当前路线 <b class="mono">' + esc(o.branch_id) + '</b> · 份额 <b>'
    + Math.round(o.share * 100) + '%</b> · evidence ' + o.factors.evidence + ' / risk ' + o.factors.risk
    + (o.eligible ? ' · 可路由' : ' · 不可路由');
}
function openWayfinder(focusId) {
  renderWayfinder(focusId);
  openDrawer('wfOverlay', 'wfPanel');
}

/* Wayfinder 问答（Copilot 卡片交互） */
function wayfinderAnswer(q) {
  q = (q || '').toLowerCase();
  if (!OPP.length) return '暂无机会数据。';
  var pick = OPP[0];
  if (/risk|风险|radar/.test(q)) {
    pick = OPP.slice().sort(function (a, b) { return b.factors.risk - a.factors.risk; })[0];
  } else if (/cost|成本|cheap/.test(q)) {
    var known = OPP.filter(function (o) { return o.known_cost != null; }).sort(function (a, b) { return a.known_cost - b.known_cost; });
    if (known.length) pick = known[0];
  } else if (/sleep|dormant|休眠/.test(q)) {
    var dor = OPP.filter(function (o) { return (o.reasons || []).indexOf('dormant') >= 0; });
    if (dor.length) pick = dor[0];
  } else if (/fail|失败|根因|root/.test(q)) {
    var ev = null;
    PKG.tasks.forEach(function (t) { if (t.status === 'failed') ev = evidenceOf(t.signal.task_id); });
    return '最近失败信号：T-15 硬边界基线（v1 参数族）。<br>evidence：' + esc(ev || '—')
      + '<br>专家 Prof. K 认为更可能是时间步长问题（unverified，意见≠事实）；v2 修正任务 T-16 已由 w-03 认领。'
      + '<br><a data-open-replay="T-15">Open T-15 in replay →</a>';
  }
  var f = pick.factors;
  return '建议路线 <b class="mono">' + esc(pick.branch_id) + '</b> · 机会份额 <b>' + Math.round(pick.share * 100) + '%</b> · '
    + (pick.eligible ? 'eligible' : 'ineligible')
    + '<br>evidence ' + f.evidence + ' · applicability ' + f.applicability + ' · goal ' + f.goal_relevance + ' · risk ' + f.risk
    + '<br>支持 ×' + f.support_count + ' / 反驳 ×' + f.refute_count + ' · 成本 ' + (pick.known_cost == null ? '—' : pick.known_cost)
    + ((pick.reasons || []).length ? '<br>理由：' + pick.reasons.map(function (r) { return REASON_ZH[r] || r; }).join('、') : '')
    + '<br><a data-open-wf="' + esc(pick.branch_id) + '">在 Wayfinder 面板中查看路线 →</a>';
}
function wfAsk(q) {
  var input = $('wfAskInput');
  var question = (q != null ? q : input.value).trim();
  if (!question) { input.focus(); return; }
  var ans = $('wfAnswer');
  ans.hidden = false;
  ans.innerHTML = '<span class="muted">正在询问 WindFinder（真实 pi-agent）…</span>';
  fetch('/api/wayfinder/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: question })
  })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d && d.answer) {
        ans.innerHTML = renderPiAnswer(d.answer);
      } else {
        ans.innerHTML = '<span class="muted">' + esc((d && (d.detail || d.error)) || '无回答') + '</span>';
      }
    })
    .catch(function (e) {
      ans.innerHTML = '<span class="muted">请求失败：' + esc(String((e && e.message) || e)) + '</span>';
    });
}

function inlineMd(s) {
  return esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/`([^`]+)`/g, '<code>$1</code>');
}
function renderPiAnswer(md) {
  var lines = String(md).split('\n');
  var out = [];
  var inCode = false;
  lines.forEach(function (line) {
    if (/^\s*```/.test(line)) { inCode = !inCode; return; }
    if (inCode) { out.push('<pre class="wf-code">' + esc(line) + '</pre>'); return; }
    var t = line.replace(/^\s+/, '');
    if (/^###\s+/.test(t)) { out.push('<div class="wf-h3">' + esc(t.replace(/^###\s+/, '')) + '</div>'); return; }
    if (/^##\s+/.test(t)) { out.push('<div class="wf-h2">' + esc(t.replace(/^##\s+/, '')) + '</div>'); return; }
    if (/^#\s+/.test(t)) { out.push('<div class="wf-h1">' + esc(t.replace(/^#\s+/, '')) + '</div>'); return; }
    if (/^[-*]\s+/.test(t)) { out.push('<div class="wf-li">· ' + inlineMd(t.replace(/^[-*]\s+/, '')) + '</div>'); return; }
    if (/^\|.*\|/.test(t) && t.indexOf('---') === -1) {
      var cells = t.replace(/^\||\|$/g, '').split('|').map(function (c) { return inlineMd(c.trim()); });
      out.push('<div class="wf-tr">' + cells.map(function (c) { return '<span class="wf-td">' + c + '</span>'; }).join('') + '</div>');
      return;
    }
    if (/^---+$/.test(t) || /^\|\s*[-:]+\s*(\|\s*[-:]+\s*)*\|?$/.test(t)) return;
    out.push('<div>' + inlineMd(t) + '</div>');
  });
  return out.join('');
}

/* ---------- 任务回放 ---------- */
function openReplay(taskId) {
  window.EnvData.fetchReplay(taskId).then(function (r) {
    $('replayTitle').textContent = taskId + (r.task ? ' · ' + r.task.signal.payload.goal : '');
    var html = '';
    if (r.task) {
      var t = r.task;
      html += '<div class="chips">'
        + statusPill(t.status)
        + branchTag(t.signal.payload.branch_id)
        + '<span class="tag">owner ' + esc(t.owner || '—') + '</span>'
        + '<span class="tag">attempts ×' + t.attempts + '</span>'
        + '<span class="tag">capability ' + esc(t.signal.required_capability) + '</span>'
        + '</div>';
      html += '<div class="kv"><span class="k">dependencies</span><span class="mono">' + esc((t.dependencies || []).join(', ') || '—') + '</span></div>';
      html += '<div class="kv"><span class="k">result_id</span><span class="mono">' + esc(t.result_id || '—') + '</span></div>';
      html += '<div class="kv"><span class="k">created</span><span>' + fmtDate(t.created_at) + ' ' + fmtTime(t.created_at) + '</span></div>';
    }
    html += '<h4>Timeline · sequence 升序</h4><ul class="tl">';
    r.audit.forEach(function (e) {
      html += '<li class="tl-item tone-' + toneOf(e) + '">' + esc(phrase(e))
        + '<span class="tl-time">seq ' + e.sequence + ' · ' + fmtTime(e.at) + '</span></li>';
    });
    html += '</ul>';
    if (r.executions.length) {
      html += '<h4>Executions</h4>';
      r.executions.forEach(function (x) {
        html += '<div class="kv"><span class="k mono">' + esc(x.run_id) + '</span><span>'
          + 'execution=' + esc(x.recorded_result.execution_state)
          + ' · verdict=' + esc(x.recorded_result.scientific_verdict)
          + ' · effect=' + esc(x.recorded_result.effect_state) + ' '
          + '<span class="pill ' + (x.archive_status === 'verified' ? 'pill-green' : 'pill-red') + '">' + esc(x.archive_status) + '</span>'
          + '</span></div>';
      });
    }
    if (r.observations.length) {
      html += '<h4>Observations</h4>';
      r.observations.forEach(function (n) {
        html += '<div class="kv"><span class="k mono">' + esc(n.note_id) + '</span><span>'
          + '<span class="tag">' + esc(n.kind) + '</span> '
          + '<span class="pill ' + (n.review_state === 'verified' ? 'pill-green' : 'pill-gold') + '">' + esc(n.review_state) + '</span><br>'
          + esc(n.text) + '</span></div>';
      });
    }
    if (r.adoption_receipts.length) {
      html += '<h4>Adoption receipts</h4>';
      r.adoption_receipts.forEach(function (a) {
        html += '<div class="kv"><span class="k mono">' + esc(a.receipt_id) + '</span><span>复用 <span class="mono">' + esc(a.adopted_result_id) + '</span> · actor ' + esc(a.actor || '—') + '</span></div>';
      });
    }
    $('replayBody').innerHTML = html;
    openDrawer('replayOverlay', 'replayPanel');
  });
}

/* ---------- 快捷搜索（1:1 command palette） ---------- */
var cmdkOpen = false, cmdkSel = 0, cmdkCache = [];
function cmdkItems() {
  var items = [
    { t: 'Go to Dashboard', hint: 'g d', run: function () { switchView('home'); } },
    { t: 'Go to Signals', hint: 'g i', run: function () { switchView('signals'); } },
    { t: 'Go to Feed', hint: 'g p', run: function () { switchView('feed'); } },
    { t: 'Open Wayfinder', hint: 'w', run: function () { openWayfinder(); } },
    { t: 'Toggle notifications', hint: 'g n', run: function () { toggleNotif(); } }
  ];
  Object.keys(TASK).forEach(function (id) {
    var goal = TASK[id].signal.payload.goal;
    items.push({ t: 'Open replay ' + id + ' · ' + goal, hint: 'task', run: function () { openReplay(id); } });
  });
  SNAP.branches.forEach(function (b) {
    items.push({ t: 'View branch ' + b.branch_id + ' (' + (BRANCH_ZH[b.status] || b.status) + ')', hint: 'branch', run: function () { openWayfinder(b.branch_id); } });
  });
  return items;
}
function renderCmdk(q) {
  q = q.trim().toLowerCase();
  cmdkCache = cmdkItems().filter(function (it) { return !q || it.t.toLowerCase().indexOf(q) >= 0; }).slice(0, 12);
  cmdkSel = 0;
  var list = $('cmdkList');
  list.innerHTML = '';
  if (!cmdkCache.length) {
    list.innerHTML = '<li class="cmdk-item muted">No results found.</li>';
    return;
  }
  cmdkCache.forEach(function (it, i) {
    var li = h('<li class="cmdk-item' + (i === cmdkSel ? ' is-sel' : '') + '"><span>' + esc(it.t) + '</span><span class="cmdk-hint">' + esc(it.hint) + '</span></li>');
    li.addEventListener('click', function () { closeCmdk(); it.run(); });
    li.addEventListener('mousemove', function () { setCmdkSel(i); });
    list.appendChild(li);
  });
}
function setCmdkSel(i) {
  cmdkSel = i;
  var nodes = $('cmdkList').querySelectorAll('.cmdk-item');
  nodes.forEach(function (n, j) { n.classList.toggle('is-sel', j === i); });
}
function openCmdk() {
  if (cmdkOpen) return;
  $('cmdk').hidden = false;
  cmdkOpen = true;
  $('cmdkInput').value = '';
  renderCmdk('');
  $('cmdkInput').focus();
  pushLayer('cmdk', closeCmdk);
}
function closeCmdk() {
  if (!cmdkOpen) return;
  $('cmdk').hidden = true;
  cmdkOpen = false;
  LAYERS = LAYERS.filter(function (l) { return l.name !== 'cmdk'; });
}

/* ---------- 键盘快捷键（g d / g i / g p / g n / w / / / Esc） ---------- */
var gPending = false, gTimer = null;
document.addEventListener('keydown', function (e) {
  var ae = document.activeElement;
  var typing = ae && (/^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName) || ae.isContentEditable);
  if (e.key === 'Escape') { closeDD(); closeTop(); return; }
  if (typing) return;
  if (e.key === '/') { e.preventDefault(); openCmdk(); return; }
  if (e.key === 'w' || e.key === 'W') { e.preventDefault(); openWayfinder(); return; }
  if (gPending) {
    gPending = false; clearTimeout(gTimer);
    var k = e.key.toLowerCase();
    if (k === 'd' || k === 'h') switchView('home');
    else if (k === 'i') switchView('signals');
    else if (k === 'p') switchView('feed');
    else if (k === 'n') toggleNotif();
    return;
  }
  if (e.key === 'g') { gPending = true; gTimer = setTimeout(function () { gPending = false; }, 900); }
});

/* ---------- 行菜单 / 排序菜单 ---------- */
var menuTaskId = null;
function openTaskMenu(taskId, anchor) {
  menuTaskId = taskId;
  $('taskMenuTitle').textContent = taskId + ' actions';
  var m = $('taskMenu');
  m.hidden = false;
  placeFixed(m, anchor);
  if (ddOpen && ddOpen !== m) ddOpen.hidden = true;
  ddOpen = m; ddTrigger = anchor;
}

/* ---------- 全局事件委托 ---------- */
document.addEventListener('click', function (ev) {
  var t = ev.target;
  var replay = t.closest('[data-open-replay]');
  if (replay) { ev.preventDefault(); openReplay(replay.getAttribute('data-open-replay')); return; }
  var wf = t.closest('[data-open-wf]');
  if (wf) { ev.preventDefault(); openWayfinder(wf.getAttribute('data-open-wf')); return; }
  var menu = t.closest('[data-menu]');
  if (menu) { ev.preventDefault(); openTaskMenu(menu.getAttribute('data-menu'), menu); return; }
  var gt = t.closest('[data-goto]');
  if (gt) {
    ev.preventDefault();
    var dest = gt.getAttribute('data-goto');
    if (dest === '#/branches') openWayfinder();
    else location.hash = dest;
    return;
  }
});

/* ---------- 绑定 chrome ---------- */
on('globalMenuBtn', 'click', function () { document.body.classList.toggle('nav-open'); });
on('globalSearchBtn', 'click', openCmdk);
on('copilotBtn', 'click', function () { openWayfinder(); });

on('createBtn', 'click', function () { toggleDD($('createMenu'), $('createBtn')); });
document.querySelectorAll('#createMenu .dd-item').forEach(function (b) {
  b.addEventListener('click', function () {
    closeDD();
    toast('已创建 ' + b.textContent.trim() + ' 草稿（mock · 需真实后端 choose()）');
  });
});

on('notifBtn', 'click', toggleNotif);

on('userMenuBtn', 'click', function () { toggleDD($('userMenu'), $('userMenuBtn')); });
document.querySelectorAll('#userMenu .dd-item').forEach(function (b) {
  b.addEventListener('click', function () {
    closeDD();
    var k = b.getAttribute('data-user');
    if (k === 'signout') {
      $('sessionAlertText').textContent = 'You signed out in another tab or window. Reload to refresh your session.';
      $('sessionAlert').hidden = false;
    } else toast(b.textContent.trim() + ' · 占位入口（demo）');
  });
});

on('sessionAlertDismiss', 'click', function () { $('sessionAlert').hidden = true; });
on('loadErrorRetry', 'click', function () { location.reload(); });

on('switchClassic', 'click', function () { switchView('feed'); });
on('giveFeedback', 'click', function () {
  $('feedbackDlg').hidden = false;
  pushLayer('feedback', closeFeedback);
});
function closeFeedback() {
  $('feedbackDlg').hidden = true;
  LAYERS = LAYERS.filter(function (l) { return l.name !== 'feedback'; });
}
on('fbClose', 'click', closeFeedback);
on('fbCancel', 'click', closeFeedback);
on('fbSend', 'click', function () { closeFeedback(); toast('Feedback sent. 感谢你的路线反馈！'); });
on('feedbackDlg', 'click', function (ev) { if (ev.target === $('feedbackDlg')) closeFeedback(); });

on('tasksViewAll', 'click', function () { switchView('signals'); });
on('issuesViewAll', 'click', function () { switchView('signals'); });
on('ledgerViewAll', 'click', function () { switchView('feed'); });

on('taskSortBtn', 'click', function () {
  var m = $('sortMenu');
  if (ddOpen === m) { closeDD(); return; }
  m.hidden = false;
  placeFixed(m, $('taskSortBtn'));
  if (ddOpen) ddOpen.hidden = true;
  ddOpen = m; ddTrigger = $('taskSortBtn');
});
document.querySelectorAll('#sortMenu .dd-item').forEach(function (b) {
  b.addEventListener('click', function () {
    taskSort = b.getAttribute('data-sort');
    closeDD();
    renderTasks();
  });
});

on('tmReplay', 'click', function () { closeDD(); if (menuTaskId) openReplay(menuTaskId); });
on('tmAsk', 'click', function () {
  closeDD();
  var t = menuTaskId && TASK[menuTaskId];
  openWayfinder(t && t.signal.payload.branch_id ? t.signal.payload.branch_id : undefined);
});
on('tmCopy', 'click', function () {
  closeDD();
  var text = menuTaskId || '';
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function () { toast('Copied ' + text); }, function () { toast(text); });
  } else toast(text);
});

on('bannerDismiss', 'click', function () { var b = $('banner'); if (b) b.remove(); });
on('bannerRegister', 'click', function () {
  var b = $('bannerRegister');
  b.disabled = true;
  b.textContent = 'Registered ✓';
  toast('已登记 Swarm Assembly 探索名额（mock）');
});

on('sideFilterInput', 'input', function () {
  branchQuery = this.value.trim().toLowerCase();
  renderBranches();
});
on('homeFilterInput', 'input', renderSignals);
on('branchMore', 'click', function () { toast('全部 ' + SNAP.branches.length + ' 条分支已在列表中'); });

on('wfAskBtn', 'click', function () { wfAsk(); });
on('wfAskInput', 'keydown', function (e) { if (e.key === 'Enter') wfAsk(); });
on('wfHint1', 'click', function () { $('wfAskInput').value = '帮我定位 T-15 失败的根因'; wfAsk('帮我定位 T-15 失败的根因 fail'); });
on('wfHint2', 'click', function () { $('wfAskInput').value = '哪条分支下一步的机会份额最高？'; wfAsk('哪条分支下一步的机会份额最高？'); });

document.querySelectorAll('#wfChips button').forEach(function (b) {
  b.addEventListener('click', function () {
    var cmd = b.getAttribute('data-cmd');
    if (cmd === 'top') openWayfinder(OPP.length ? OPP[0].branch_id : undefined);
    else if (cmd === 'focus') {
      switchView('home');
      setTimeout(function () { $('tasksCard').scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 60);
    } else if (cmd === 'risk') {
      switchView('signals');
      setTimeout(function () { $('issueList').scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 60);
    } else if (cmd === 'replay') {
      var done = PKG.tasks.filter(function (t) { return t.status === 'completed'; })
        .sort(function (a, b) { return b.updated_at - a.updated_at; });
      if (done.length) openReplay(done[0].signal.task_id);
    }
  });
});

on('wfClose', 'click', function () { closeDrawer('wfOverlay', 'wfPanel'); });
on('wfOverlay', 'click', function () { closeDrawer('wfOverlay', 'wfPanel'); });
on('replayClose', 'click', function () { closeDrawer('replayOverlay', 'replayPanel'); });
on('replayOverlay', 'click', function () { closeDrawer('replayOverlay', 'replayPanel'); });

on('cmdkInput', 'input', function () { renderCmdk(this.value); });
on('cmdkInput', 'keydown', function (e) {
  if (e.key === 'ArrowDown') { e.preventDefault(); setCmdkSel(Math.min(cmdkSel + 1, cmdkCache.length - 1)); }
  else if (e.key === 'ArrowUp') { e.preventDefault(); setCmdkSel(Math.max(cmdkSel - 1, 0)); }
  else if (e.key === 'Enter') { e.preventDefault(); if (cmdkCache[cmdkSel]) { var it = cmdkCache[cmdkSel]; closeCmdk(); it.run(); } }
});
on('cmdk', 'click', function (ev) { if (ev.target === $('cmdk')) closeCmdk(); });

document.querySelectorAll('[data-foot]').forEach(function (b) {
  b.addEventListener('click', function () { toast(b.textContent.trim() + ' · 占位链接（demo）'); });
});

/* 会话提示（1:1 "signed in with another tab"）——切页签离开后回来触发 */
var hiddenAt = null;
document.addEventListener('visibilitychange', function () {
  if (document.hidden) { hiddenAt = Date.now(); return; }
  if (hiddenAt && Date.now() - hiddenAt > 45000) {
    $('sessionAlertText').textContent = 'You signed in with another tab or window. Reload to refresh your session.';
    $('sessionAlert').hidden = false;
  }
  hiddenAt = null;
});

/* ---------- 启动 ---------- */
Promise.all([window.EnvData.fetchPackage(), window.EnvData.fetchSnapshot()])
  .then(function (rs) {
    PKG = rs[0]; SNAP = rs[1];
    PKG.tasks.forEach(function (t) { TASK[t.signal.task_id] = t; });
    SNAP.branches.forEach(function (b) { BRANCH[b.branch_id] = b; });
    OPP = (SNAP.opportunities.opportunities || []).slice().sort(function (a, b) { return b.share - a.share; });

    renderGreeting();
    renderBranches();
    renderTasks();
    renderSignals();
    renderFeed();
    renderLedger();
    renderExperts();
    applyView();

    $('wfExploreLabel').textContent = 'Optimized for: Exploration ' + Math.round((SNAP.exploration_fraction || 0) * 100) + '%';
    $('wfHint1').innerHTML = '帮我定位这次失败的根因：<span class="hint">[paste evidence here]</span>';
    $('wfHint2').textContent = '哪条分支下一步的机会份额最高？';

    /* 预置未读通知（最近 5 条账本事件） */
    PKG.task_audit.slice(-5).reverse().forEach(function (e) { pushNotif(e); });

    /* 活动流订阅：首循环为历史回放（live=false 跳过），之后实时追加 */
    window.EnvData.subscribeActivity(function (e) {
      if (!e.live) return;
      pushNotif(e);
      var list = $('feedList');
      if (list) {
        list.appendChild(feedItem(e, true));
        $('feedCount').textContent = list.children.length + ' events · sequence 升序';
      }
    });
  })
  .catch(function () {
    $('loadError').hidden = false;
  });

})();
