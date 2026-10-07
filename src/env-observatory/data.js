/* Same-origin research facts. Missing services stay empty, never examples.
 * source describes transport; per-record provenance and acceptance stay intact. */
(function () {
  'use strict';
  var pkg = null, source = 'unconnected';
  function apiUrl(resource, taskId, since) {
    var project = new URLSearchParams(window.location.search).get('project_id');
    var url = '/api/research/' + resource;
    if (taskId !== undefined) url += '/' + encodeURIComponent(taskId);
    var query = new URLSearchParams();
    if (project) query.set('project_id', project);
    if (since !== undefined) query.set('since_seq', since);
    return url + (query.toString() ? '?' + query : '');
  }
  function fetchJson(url) {
    if (!/^https?:$/.test(window.location.protocol)) return Promise.reject(new Error('HTTP service not connected'));
    return window.fetch(url).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }
  function emptySnapshot(error) {
    return { source: 'unconnected', error: String(error.message || error), branches: [],
      opportunities: { opportunities: [] }, contributions: [], supersessions: [], constraints: null };
  }
  function fetchPackage() {
    return fetchJson(apiUrl('package')).then(function (data) {
      pkg = data; source = 'backend'; data.source = source; return data;
    }).catch(function (error) {
      source = 'unconnected';
      pkg = { source: source, error: String(error.message || error), project_id: null,
        tasks: [], task_audit: [], executions: [], adoption_receipts: [],
        context: { project: null, notes: [], research_v1: emptySnapshot(error) } };
      return pkg;
    });
  }
  function fetchSnapshot() {
    return fetchJson(apiUrl('snapshot')).then(function (data) {
      data.source = 'backend'; return data;
    }).catch(emptySnapshot);
  }
  function fetchReplay(taskId) {
    return fetchJson(apiUrl('replay', taskId)).then(function (data) {
      data.source = 'backend'; return data;
    }).catch(function (error) {
      return { source: 'unconnected', error: String(error.message || error), task_id: taskId,
        task: null, audit: [], executions: [], observations: [], adoption_receipts: [] };
    });
  }
  function subscribeActivity(onEvent) {
    if (source !== 'backend' || !pkg) return function () {};
    var stopped = false;
    var since = (pkg.task_audit || []).reduce(function (n, e) { return Math.max(n, e.sequence || 0); }, 0);
    function poll() {
      if (stopped) return;
      fetchJson(apiUrl('activity', undefined, since)).then(function (data) {
        if (stopped) return;
        (data.events || []).forEach(function (e) {
          if (e.sequence > since) {
            since = e.sequence;
            onEvent(Object.assign({}, e, { live: true }));
          }
        });
      }).catch(function () { /* Read-only polling; no generated events. */ });
    }
    var timer = setInterval(poll, 3200);
    return function () { stopped = true; clearInterval(timer); };
  }
  window.EnvData = { fetchPackage: fetchPackage, fetchSnapshot: fetchSnapshot,
    fetchReplay: fetchReplay, subscribeActivity: subscribeActivity,
    getSource: function () { return source; } };
})();
