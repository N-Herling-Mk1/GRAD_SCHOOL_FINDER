/* Wiring: boot sequence, filter chips, keyboard, clock. */
(function () {
  var families = [], currentFamily = '', currentState = null;

  function clock() {
    var el = document.getElementById('clock');
    if (!el) return;
    el.textContent = new Date().toTimeString().slice(0, 8) + '  local';
  }

  function loadState(code) {
    if (!code) { currentState = null; GF.panel.idle(); return; }
    GF.map.highlight(null);
    currentState = code;
    Promise.all([GF.api.state(code, currentFamily), GF.api.faculty(code)]).then(function (res) {
      var doc = res[0];
      GF.panel.render(doc, res[1]);
      if (!doc.__notfound) {
        GF.map.markers(doc, function (id) { GF.panel.openInstitution(id); GF.map.highlight(id); });
      } else {
        GF.map.markers(null);
      }
    }).catch(function () { /* status strip already reported it */ });
  }

  function wireFilters() {
    var box = document.getElementById('filters');
    box.addEventListener('click', function (e) {
      var btn = e.target.closest('.chipf');
      if (!btn) return;

      if (btn.hasAttribute('data-metric')) {
        var m = btn.getAttribute('data-metric');
        Array.prototype.forEach.call(box.querySelectorAll('.chipf[data-metric]'), function (b) {
          b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
        });
        GF.map.setMetric(m);
        GF.ui.say('map metric: ' + (m === 'institutions'
          ? 'institutions in scope \u2014 comparable between states'
          : m === 'lens' ? 'faculty lens \u2014 strong-fit faculty traced from papers; AZ over-sampled'
          : 'programs on file \u2014 reflects collection depth, not supply'));
        return;
      }

      if (!btn.hasAttribute('data-family')) return;
      currentFamily = btn.getAttribute('data-family') || '';
      Array.prototype.forEach.call(box.querySelectorAll('.chipf[data-family]'), function (b) {
        b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
      });
      GF.map.setFamily(currentFamily);
      document.getElementById('filternote').textContent = currentFamily
        ? 'Filtered to one family. Everything on the map and in the panel is that family only.'
        : 'Institution counts are comparable between states. Program counts are not.';
      if (currentState) loadState(currentState);
    });
  }

  function boot() {
    GF.ui.say('booting');
    clock();
    setInterval(clock, 1000);

    Promise.all([GF.api.meta(), GF.api.geo(), GF.api.index()])
      .then(function (res) {
        var meta = res[0], geo = res[1], index = res[2];
        families = meta.families;
        GF.panel.init(families, function (id) { GF.map.highlight(id); });
        GF.map.build(geo, index, loadState);
        document.getElementById('coverage').textContent = index.coverage + ' states loaded';
        GF.ui.say('ready \u2014 ' + Object.keys(geo.states).length + ' jurisdictions, ' +
          index.loaded.length + ' pack(s): ' + index.loaded.join(', '), 'ok');
        wireFilters();
      })
      .catch(function (e) { GF.ui.fail('boot failed: ' + e.message); });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') GF.map.clear();
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
