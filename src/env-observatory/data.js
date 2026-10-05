/*
 * 环境观测台 · 前端数据层（全局脚本，非 ES module）
 *
 * 唯一对外契约：window.EnvData
 *   fetchPackage()  -> Promise<package对象>   （§2：任务/审计/回放数据）
 *   fetchSnapshot() -> Promise<snapshot对象>  （§7：三轴/贡献/分支/机会）
 *   fetchReplay(taskId) -> Promise<replay对象>（从 package 按 task_id 切片）
 *   subscribeActivity(cb) -> 取消函数（cb 收到 { at, event, body }）
 *
 * 数据事实源：docs/frontend/API_CONTRACT.md。字段名照抄，不改名/改层级/改语义。
 * mock 数据内联自 environment-viewer/mock/{package,snapshot}.json，
 * 不用 fetch 读本地 JSON（file:// 下 CORS 会拦截，v4 要求双击零依赖打开）。
 *
 * 数据源：默认走真实后端 HTTP（同源 /api/research/*，由 server.py 提供），
 *   project_id 从 URL query 读取（缺省 p1）。fetch 失败（后端没起 / file://
 *   打开）时回退到内联 mock，并在返回对象上标 source: 'live' | 'mock'。
 */
(function () {
  'use strict';

  /* ======================== 内联 mock：package（§2） ======================== */
  const PKG = {
    "schema_version": "research-package/v1",
    "project_id": "p1",
    "limit": 100,
    "tasks_truncated": false,
    "context": {
      "project": { "project_id": "p1", "goal": "比较不同边界处理与采样策略，求解一维泊松方程，得到可验证、可继承的数值方法", "data_bounds": { "data": "synthetic-only" } },
      "notes": [
        { "note_id": "note-op-1", "kind": "expert_opinion", "text": "倾向软边界方法 A，但未提供独立数据", "signer": "Dr. Y", "review_state": "unverified" }
      ]
    },
    "tasks": [
      {
        "swarm_id": "swarm-gen-1",
        "signal": {
          "signal_id": "sig-11",
          "task_id": "T-11",
          "workspace": "/workspace",
          "scope": "science",
          "kind": "opportunity",
          "module": "research",
          "required_capability": "research",
          "payload": {
            "goal": "文献调研：软边界与硬边界的处理方法",
            "project_id": "p1",
            "branch_id": "b-soft"
          }
        },
        "status": "claimed",
        "dependencies": [],
        "acceptance": { "research_proposal_id": "prop-11" },
        "attempts": 1,
        "condition_fail_count": 0,
        "token": 1,
        "owner": "w-04",
        "expires_at": 1731000600.0,
        "created_at": 1730999400.0,
        "updated_at": 1730999400.0,
        "derived_from": null,
        "result_id": null,
        "result": null,
        "effect_applied": false
      },
      {
        "swarm_id": "swarm-gen-1",
        "signal": {
          "signal_id": "sig-12",
          "task_id": "T-12",
          "workspace": "/workspace",
          "scope": "science",
          "kind": "opportunity",
          "module": "research",
          "required_capability": "research",
          "payload": {
            "goal": "实验设计：软边界对照方案",
            "project_id": "p1",
            "branch_id": "b-soft"
          }
        },
        "status": "available",
        "dependencies": [],
        "acceptance": { "research_proposal_id": "prop-12" },
        "attempts": 0,
        "condition_fail_count": 0,
        "token": 0,
        "owner": null,
        "expires_at": null,
        "created_at": 1730999500.0,
        "updated_at": 1730999500.0,
        "derived_from": null,
        "result_id": null,
        "result": null,
        "effect_applied": false
      },
      {
        "swarm_id": "swarm-gen-1",
        "signal": {
          "signal_id": "sig-13",
          "task_id": "T-13",
          "workspace": "/workspace",
          "scope": "science",
          "kind": "opportunity",
          "module": "research",
          "required_capability": "research",
          "payload": {
            "goal": "生成候选：软边界实验代码",
            "project_id": "p1",
            "branch_id": "b-soft"
          }
        },
        "status": "submitting",
        "dependencies": ["T-11"],
        "acceptance": { "research_proposal_id": "prop-13" },
        "attempts": 1,
        "condition_fail_count": 0,
        "token": 2,
        "owner": "w-05",
        "expires_at": 1731001200.0,
        "created_at": 1730999600.0,
        "updated_at": 1731000000.0,
        "derived_from": "T-11",
        "result_id": null,
        "result": null,
        "effect_applied": false
      },
      {
        "swarm_id": "swarm-gen-1",
        "signal": {
          "signal_id": "sig-14",
          "task_id": "T-14",
          "workspace": "/workspace",
          "scope": "science",
          "kind": "opportunity",
          "module": "research",
          "required_capability": "review",
          "payload": {
            "goal": "独立复核：复现软边界结果",
            "project_id": "p1",
            "branch_id": "b-soft"
          }
        },
        "status": "claimed",
        "dependencies": ["T-13"],
        "acceptance": { "research_proposal_id": "prop-14" },
        "attempts": 1,
        "condition_fail_count": 0,
        "token": 1,
        "owner": "w-01",
        "expires_at": 1731001800.0,
        "created_at": 1731000000.0,
        "updated_at": 1731000000.0,
        "derived_from": "T-13",
        "result_id": null,
        "result": null,
        "effect_applied": false
      },
      {
        "swarm_id": "swarm-gen-1",
        "signal": {
          "signal_id": "sig-15",
          "task_id": "T-15",
          "workspace": "/workspace",
          "scope": "science",
          "kind": "opportunity",
          "module": "research",
          "required_capability": "research",
          "payload": {
            "goal": "硬边界嵌入验证",
            "project_id": "p1",
            "branch_id": "b-hard"
          }
        },
        "status": "completed",
        "dependencies": [],
        "acceptance": { "research_proposal_id": "prop-15" },
        "attempts": 2,
        "condition_fail_count": 0,
        "token": 2,
        "owner": "w-03",
        "expires_at": null,
        "created_at": 1730999000.0,
        "updated_at": 1730999800.0,
        "derived_from": null,
        "result_id": "ref:run39",
        "result": { "asset_id": "a-15", "run_id": "run39", "scientific_verdict": "failed", "execution_state": "succeeded" },
        "effect_applied": false
      },
      {
        "swarm_id": "swarm-gen-1",
        "signal": {
          "signal_id": "sig-16",
          "task_id": "T-16",
          "workspace": "/workspace",
          "scope": "science",
          "kind": "opportunity",
          "module": "research",
          "required_capability": "research",
          "payload": {
            "goal": "自适应采样探索",
            "project_id": "p1",
            "branch_id": "b-sampling"
          }
        },
        "status": "available",
        "dependencies": [],
        "acceptance": { "research_proposal_id": "prop-16" },
        "attempts": 0,
        "condition_fail_count": 0,
        "token": 0,
        "owner": null,
        "expires_at": null,
        "created_at": 1731000200.0,
        "updated_at": 1731000200.0,
        "derived_from": null,
        "result_id": null,
        "result": null,
        "effect_applied": false
      }
    ],
    "task_audit": [
      { "sequence": 1, "task_id": "T-11", "event": "claimed", "at": 1730999400.0, "body": { "worker_id": "w-04", "token": 1 } },
      { "sequence": 2, "task_id": "T-13", "event": "research.note_submitted", "at": 1730999460.0, "body": { "event_id": "ev-2", "project_id": "p1", "branch_id": "b-soft", "task_id": "T-13", "source_ref": "note-1", "actor": { "role": "builder", "instance": 1 }, "at": 1730999460.0, "schema_version": "research-v1", "provenance": "mock", "event_kind": "note_submitted", "payload": { "note_id": "note-1", "kind": "observation" }, "correlation_ref": null } },
      { "sequence": 3, "task_id": "T-11", "event": "handoff", "at": 1730999520.0, "body": { "from": "w-04", "to": "w-02", "token": 1 } },
      { "sequence": 4, "task_id": "T-13", "event": "research.contribution_accepted", "at": 1730999580.0, "body": { "event_id": "ev-4", "project_id": "p1", "task_id": "T-13", "source_ref": "ref:run42", "actor": { "role": "reviewer", "instance": 1 }, "at": 1730999580.0, "schema_version": "research-v1", "provenance": "mock", "event_kind": "contribution_accepted", "payload": { "result_id": "ref:run42" }, "correlation_ref": null } },
      { "sequence": 5, "task_id": "T-13", "event": "claimed", "at": 1730999600.0, "body": { "worker_id": "w-05", "token": 2 } },
      { "sequence": 6, "task_id": "T-14", "event": "research_choice", "at": 1730999900.0, "body": { "worker_id": "w-01", "selected": "T-14" } },
      { "sequence": 7, "task_id": "T-15", "event": "research_execution", "at": 1730999700.0, "body": { "run_id": "run39", "worker_id": "w-03", "token": 2, "result": { "execution_state": "succeeded", "scientific_verdict": "failed", "effect_state": "known" } } },
      { "sequence": 8, "task_id": "T-15", "event": "execution_confirmed", "at": 1730999720.0, "body": { "request_id": "run39", "token": 2 } },
      { "sequence": 9, "task_id": "T-15", "event": "completed", "at": 1730999800.0, "body": { "token": 2, "result_id": "ref:run39" } },
      { "sequence": 10, "task_id": "T-14", "event": "claimed", "at": 1731000000.0, "body": { "worker_id": "w-01", "token": 1 } }
    ],
    "audit_truncated": false,
    "executions": [
      {
        "task_id": "T-15",
        "run_id": "run39",
        "audit_sequence": 7,
        "recorded_result": { "execution_state": "succeeded", "scientific_verdict": "failed", "effect_state": "known" },
        "verified_result": { "execution_state": "succeeded", "scientific_verdict": "failed", "effect_state": "known", "provenance": "mock" },
        "archive_status": "verified"
      }
    ],
    "persisted_observations": [],
    "generated_validation_reports": [],
    "assets": [],
    "adoption_receipts": [],
    "export_performed_external_io": false,
    "evidence_boundary": "per_record_provenance",
    "completion_claim": false
  };

  /* ======================== 内联 mock：snapshot（§7） ======================== */
  const SNAP = {
    "policy_version": "research-v1",
    "advisory_only": true,
    "claim_requires_recheck": true,
    "project_id": "p1",
    "exploration_fraction": 0.20,
    "three_axis": {
      "execution": { "succeeded": 3, "failed": 1, "unknown": 0 },
      "hypothesis": { "supported": 2, "refuted": 1, "not_evaluated": 1 },
      "contribution": { "accepted": 3, "proposed": 2, "superseded": 1 }
    },
    "results": [
      { "result_id": "ref:run42", "report_id": "rep-42", "task_id": "T-13", "actor": "w-05", "source_ref": "paper v3", "provenance": "mock", "execution": "succeeded", "hypothesis": "supported", "contribution": "proposed", "asset_id": "a-13", "at": 1731000100.0 },
      { "result_id": "ref:run39", "report_id": "rep-39", "task_id": "T-15", "actor": "w-03", "source_ref": "paper v2", "provenance": "mock", "execution": "succeeded", "hypothesis": "refuted", "contribution": "proposed", "asset_id": "a-15", "at": 1730999800.0 }
    ],
    "contributions": [
      { "result_id": "ref:run42", "report_id": "rep-42", "task_id": "T-13", "actor": "w-05", "source_ref": "paper v3", "provenance": "mock", "execution": "succeeded", "hypothesis": "supported", "contribution": "accepted", "asset_id": "a-13", "reviewer": "reviewer-1", "at": 1731000120.0 },
      { "result_id": "ref:run39", "report_id": "rep-39", "task_id": "T-15", "actor": "w-03", "source_ref": "paper v2", "provenance": "mock", "execution": "succeeded", "hypothesis": "refuted", "contribution": "accepted", "asset_id": "a-15", "reviewer": "reviewer-1", "at": 1730999850.0 }
    ],
    "effective_contributions": [
      { "result_id": "ref:run42", "task_id": "T-13", "actor": "w-05", "hypothesis": "supported", "contribution": "accepted", "source_ref": "paper v3", "at": 1731000120.0 },
      { "result_id": "ref:run39", "task_id": "T-15", "actor": "w-03", "hypothesis": "refuted", "contribution": "accepted", "source_ref": "paper v2", "at": 1730999850.0 }
    ],
    "corrections": [
      { "event_id": "e-1", "branch_id": "b-hard", "kind": "sleep", "reason": "硬边界已被 refuted，降为休眠", "source_ref": "ref:run39", "actor": "reviewer-1", "at": 1730999900.0 }
    ],
    "supersessions": [],
    "trusted_results": [
      { "result_id": "ref:run42", "task_id": "T-13", "actor": "w-05", "hypothesis": "supported", "at": 1731000100.0 },
      { "result_id": "ref:run39", "task_id": "T-15", "actor": "w-03", "hypothesis": "refuted", "at": 1730999800.0 }
    ],
    "branches": [
      { "branch_id": "b-soft", "status": "testing", "authorized": true, "parent_id": null, "supported_by": ["ref:run42"], "refuted_by": [] },
      { "branch_id": "b-sampling", "status": "exploring", "authorized": true, "parent_id": null, "supported_by": [], "refuted_by": [] },
      { "branch_id": "b-hard", "status": "dormant", "authorized": true, "parent_id": null, "supported_by": [], "refuted_by": ["ref:run39"] },
      { "branch_id": "b-cross", "status": "proposed", "authorized": true, "parent_id": null, "supported_by": [], "refuted_by": [] }
    ],
    "opportunities": {
      "version": "research-v1",
      "exploration_fraction": 0.20,
      "total_share": 1.0,
      "opportunities": [
        { "branch_id": "b-soft", "eligible": true, "share": 0.48, "supported_by": ["ref:run42"], "refuted_by": [], "reasons": ["eligible"] },
        { "branch_id": "b-sampling", "eligible": true, "share": 0.27, "supported_by": [], "refuted_by": [], "reasons": ["eligible", "insufficient_evidence", "unknown_cost"] },
        { "branch_id": "b-cross", "eligible": true, "share": 0.25, "supported_by": [], "refuted_by": [], "reasons": ["eligible", "insufficient_evidence", "unknown_cost"] },
        { "branch_id": "b-hard", "eligible": false, "share": 0.0, "supported_by": [], "refuted_by": ["ref:run39"], "reasons": ["refuted_under_conditions"] }
      ]
    }
  };

  /* ======================== 预录活动流（循环播放，模拟蜂群"活着"） ======================== */
  const STREAM = [
    { at: 1731000060, event: 'claimed', body: { worker_id: 'w-05', task_id: 'T-13' } },
    { at: 1731000120, event: 'research.contribution_accepted', body: { event_id: 'ev-12', project_id: 'p1', task_id: 'T-13', source_ref: 'ref:run42', actor: { role: 'reviewer', instance: 1 }, at: 1731000120, event_kind: 'contribution_accepted', payload: { result_id: 'ref:run42' } } },
    { at: 1731000180, event: 'research.note_submitted', body: { event_id: 'ev-13', project_id: 'p1', branch_id: 'b-soft', task_id: 'T-13', actor: { role: 'builder', instance: 2 }, at: 1731000180, event_kind: 'note_submitted', payload: { note_id: 'note-2', kind: 'observation' } } },
    { at: 1731000240, event: 'handoff', body: { from: 'w-05', to: 'w-01', task_id: 'T-13' } },
    { at: 1731000300, event: 'research_execution', body: { task_id: 'T-13', run_id: 'run43' } },
    { at: 1731000360, event: 'execution_confirmed', body: { task_id: 'T-13', request_id: 'run43' } },
    { at: 1731000420, event: 'completed', body: { worker_id: 'w-05', task_id: 'T-13', result_id: 'ref:run43' } },
    { at: 1731000480, event: 'research_choice', body: { worker_id: 'w-06', selected: 'T-16' } }
  ];

  /* ======================== 内部工具 ======================== */

  function projectId() {
    try {
      return new URLSearchParams(window.location.search).get('project_id') || 'p1';
    } catch (e) {
      return 'p1';
    }
  }

  function apiUrl(resource, taskId) {
    var base = '/api/research/' + resource;
    if (taskId !== undefined) base += '/' + encodeURIComponent(taskId);
    return base + '?project_id=' + encodeURIComponent(projectId());
  }

  function fetchJson(url) {
    return window.fetch(url).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status + ' for ' + url);
      return r.json();
    });
  }

  function mockClone(obj) {
    var clone = JSON.parse(JSON.stringify(obj));
    clone.source = 'mock';
    return clone;
  }

  function loadPackage() {
    return fetchJson(apiUrl('package')).then(function (data) {
      data.source = 'live';
      return data;
    }).catch(function () {
      return mockClone(PKG);
    });
  }

  function loadSnapshot() {
    return fetchJson(apiUrl('snapshot')).then(function (data) {
      data.source = 'live';
      return data;
    }).catch(function () {
      return mockClone(SNAP);
    });
  }

  function taskAuditFor(pkg, taskId) {
    return (pkg.task_audit || [])
      .filter(function (e) { return e.task_id === taskId; })
      .sort(function (a, b) { return a.sequence - b.sequence; });
  }

  function replayFor(pkg, taskId) {
    const audit = taskAuditFor(pkg, taskId);
    const executions = (pkg.executions || []).filter(function (e) { return e.task_id === taskId; });
    const observations = (pkg.persisted_observations || []).filter(function (o) { return o.task_id === taskId; });
    const receipts = (pkg.adoption_receipts || []);
    return {
      task_id: taskId,
      task: (pkg.tasks || []).find(function (t) { return t.signal && t.signal.task_id === taskId; }) || null,
      audit: audit,
      executions: executions,
      observations: observations,
      adoption_receipts: receipts
    };
  }

  /* ======================== 对外契约：window.EnvData ======================== */
  window.EnvData = {
    fetchPackage: function () {
      return loadPackage();
    },

    fetchSnapshot: function () {
      return loadSnapshot();
    },

    fetchReplay: function (taskId) {
      return fetchJson(apiUrl('replay', taskId)).then(function (data) {
        data.source = 'live';
        return data;
      }).catch(function () {
        var replay = replayFor(PKG, taskId);
        replay.source = 'mock';
        return replay;
      });
    },

    subscribeActivity: function (onEvent) {
      var stopped = false;
      var timer = null;
      var mode = 'live';
      var seen = {};
      var mockHistory = (PKG.task_audit || []).slice().sort(function (a, b) { return a.sequence - b.sequence; });
      var mockCursor = 0;
      var streamIndex = 0;

      function emit(item) {
        if (!stopped) onEvent({ at: item.at, event: item.event, body: item.body });
      }

      function liveTick() {
        window.fetch(apiUrl('package'))
          .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
          })
          .then(function (pkg) {
            if (stopped) return;
            (pkg.task_audit || []).forEach(function (e) {
              if (!seen[e.sequence]) {
                seen[e.sequence] = true;
                emit(e);
              }
            });
          })
          .catch(function () {
            mode = 'mock';
          });
      }

      function mockTick() {
        if (mockCursor < mockHistory.length) {
          emit(mockHistory[mockCursor]);
          mockCursor += 1;
        } else {
          emit(STREAM[streamIndex % STREAM.length]);
          streamIndex += 1;
        }
      }

      function tick() {
        if (mode === 'live') liveTick();
        else mockTick();
      }

      tick();
      timer = setInterval(tick, 2000);

      return function () {
        stopped = true;
        if (timer) clearInterval(timer);
      };
    }
  };
})();
