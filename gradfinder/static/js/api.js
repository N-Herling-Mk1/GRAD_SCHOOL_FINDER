/* Thin fetch layer. Every call drives the status strip, so a slow or failed
   request is visible in the interface rather than only in the console. */
window.GF = window.GF || {};

GF.ui = (function () {
  var bar = null, log = null, pending = 0;

  function el() {
    if (!bar) { bar = document.getElementById('progress'); log = document.getElementById('log'); }
  }

  function progress(pct) { el(); if (bar) bar.style.width = Math.max(0, Math.min(100, pct)) + '%'; }

  function say(msg, kind) {
    el();
    if (!log) return;
    var t = new Date().toTimeString().slice(0, 8);
    log.innerHTML = '<b>' + t + '</b> &nbsp;' + msg;
    log.style.color = kind === 'bad' ? 'var(--bad)' : (kind === 'ok' ? 'var(--ok)' : 'var(--dim)');
  }

  function start(label) { pending++; progress(18); say(label + '\u2026'); }
  function done(label) {
    pending = Math.max(0, pending - 1);
    progress(100);
    say(label, 'ok');
    setTimeout(function () { if (pending === 0) progress(0); }, 420);
  }
  function fail(label) { pending = Math.max(0, pending - 1); progress(0); say(label, 'bad'); }

  return { progress: progress, say: say, start: start, done: done, fail: fail };
})();

GF.api = (function () {
  /* Two modes, one interface.
     live   -- Flask dev server, /api/v1/...
     static -- the exported site (GitHub Pages). Every response was written to
               api/*.json by tools/export_static.py; family filtering, which the
               server does in live mode, is done here instead. */
  var STATIC = !!window.GF_STATIC;
  var BASE = STATIC ? 'api' : '/api/v1';

  function get(path, label) {
    GF.ui.start(label);
    var url = STATIC ? (BASE + path + '.json') : (BASE + path);
    return fetch(url, { headers: { 'Accept': 'application/json' } })
      .then(function (r) {
        GF.ui.progress(70);
        if (r.status === 404) return r.json().then(function (j) { j.__notfound = true; return j; });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (j) {
        if (STATIC && j.status === 'empty') j.__notfound = true;
        GF.ui.done(label + ' \u2014 ok');
        return j;
      })
      .catch(function (e) { GF.ui.fail(label + ' failed: ' + e.message); throw e; });
  }

  /* Mirror of Store.detail(family=...) in services/store.py. Keep the two in step. */
  function filterFamily(doc, family) {
    if (!family || doc.__notfound) return doc;
    var out = Object.assign({}, doc);
    out.institutions = (doc.institutions || []).map(function (inst) {
      var rec = Object.assign({}, inst);
      rec.programs = (inst.programs || []).filter(function (p) { return p.family === family; });
      rec.program_count = rec.programs.length;
      return rec;
    }).filter(function (r) { return r.programs.length; });
    out.institutions.sort(function (a, b) {
      return (b.program_count - a.program_count) || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
    });
    out.filter = { family: family, include_boundary: true };
    return out;
  }

  return {
    mode: STATIC ? 'static' : 'live',
    geo: function () { return get('/geo', 'loading geometry'); },
    meta: function () { return get('/meta', 'loading schema'); },
    index: function () { return get('/states', 'loading state index'); },
    facultyIndex: function () { return get('/faculty', 'loading faculty sites'); },
    faculty: function (code) { return get('/faculty/' + code, 'loading faculty lens ' + code); },
    state: function (code, family) {
      if (STATIC) {
        return get('/states/' + code, 'loading ' + code).then(function (d) { return filterFamily(d, family); });
      }
      var q = family ? ('?family=' + encodeURIComponent(family)) : '';
      return get('/states/' + code + q, 'loading ' + code);
    }
  };
})();
