/* The map. Projected geometry -> SVG, choropleth, hover, selection, and the
   zoom layer: wheel zoom at the cursor, drag to pan, shift-drag or right-click
   to box zoom. Right click also opens the options menu. */
window.GF = window.GF || {};

GF.map = (function () {
  var svg, gStates, gLabels, gMarkers, gSites, gBox, tip, chipbox, zoomBtn, wrap, menu;
  var siteRecs = [], sitesOn = true;   // faculty-lens university sites
  var geo = null, index = null, family = '', metric = 'institutions', selected = null;
  var canvas = { width: 975, height: 610 };
  var view = { x: 0, y: 0, w: 975, h: 610 };
  var anim = null, onSelect = null;

  var MIN_W = 40;                 // deepest zoom, in canvas units
  var markerRecs = [];            // {g, label, leader, x, y} for the zoom-aware relayout
  var drag = null;                // active pan or box drag
  var armedBox = false;           // box zoom armed from the menu
  var suppressClick = false;

  var SMALL = ['VT', 'NH', 'MA', 'RI', 'CT', 'NJ', 'DE', 'MD', 'DC'];
  var BASE_RGB = [13, 23, 34];
  var HOT_RGB = [53, 224, 255];

  function reduced() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /* ------------------------------------------------------------- choropleth */
  function value(code) {
    if (!index) return 0;
    var r = index.states[code];
    if (!r) return 0;
    if (metric === 'lens') return r.lens ? r.lens.strong : 0;
    if (metric === 'institutions') {
      return family ? (r.by_family_institutions[family] || 0) : r.institutions_in_scope;
    }
    return family ? (r.by_family[family] || 0) : r.programs;
  }

  function maxValue() {
    var m = 0;
    for (var c in index.states) m = Math.max(m, value(c));
    return m;
  }

  function fillFor(v, max) {
    if (!v) return 'var(--panel2)';
    var t = 0.22 + 0.78 * Math.sqrt(v / (max || 1));
    var rgb = BASE_RGB.map(function (b, i) { return Math.round(b + (HOT_RGB[i] - b) * t); });
    return 'rgb(' + rgb.join(',') + ')';
  }

  function unitLabel() {
    if (metric === 'lens') return 'strong-fit faculty (fit \u2265 4)';
    return metric === 'institutions' ? 'institutions' : 'programs on file';
  }

  /* ------------------------------------------------------------------ build */
  function build(geoDoc, indexDoc, selectCb) {
    geo = geoDoc; index = indexDoc; onSelect = selectCb;
    canvas = geo.canvas;
    view = { x: 0, y: 0, w: canvas.width, h: canvas.height };

    svg = document.getElementById('map');
    gStates = document.getElementById('layer-states');
    gLabels = document.getElementById('layer-labels');
    gMarkers = document.getElementById('layer-markers');
    gSites = document.getElementById('layer-sites');
    gBox = document.getElementById('layer-box');
    tip = document.getElementById('tip');
    chipbox = document.getElementById('smallchips');
    zoomBtn = document.getElementById('zoomout');
    wrap = document.getElementById('mapwrap');
    menu = document.getElementById('ctxmenu');

    Object.keys(geo.states).sort().forEach(function (code) {
      var s = geo.states[code];
      var p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      p.setAttribute('d', s.d);
      p.setAttribute('class', 'st');
      p.setAttribute('data-code', code);
      p.setAttribute('tabindex', '0');
      p.setAttribute('role', 'button');
      p.setAttribute('vector-effect', 'non-scaling-stroke');
      p.setAttribute('aria-label', s.name);
      p.addEventListener('click', function (e) {
        e.stopPropagation();
        if (suppressClick) return;
        select(code);
      });
      p.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(code); }
      });
      p.addEventListener('mousemove', function (e) { if (!drag) showTip(code, e); });
      p.addEventListener('mouseleave', hideTip);
      p.addEventListener('focus', function () { showTip(code, null); });
      p.addEventListener('blur', hideTip);
      gStates.appendChild(p);

      var w = s.bbox[2] - s.bbox[0], h = s.bbox[3] - s.bbox[1];
      if (SMALL.indexOf(code) === -1 && w > 24 && h > 15) {
        var t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('class', 'stlabel');
        t.setAttribute('x', s.centroid[0]);
        t.setAttribute('y', s.centroid[1] + 3);
        t.setAttribute('data-code', code);
        t.textContent = code;
        gLabels.appendChild(t);
      }
    });

    SMALL.forEach(function (code) {
      if (!geo.states[code]) return;
      var b = document.createElement('button');
      b.textContent = code;
      b.setAttribute('data-code', code);
      b.addEventListener('click', function () { select(code); });
      b.addEventListener('mousemove', function (e) { showTip(code, e); });
      b.addEventListener('mouseleave', hideTip);
      chipbox.appendChild(b);
    });

    svg.addEventListener('click', function () { if (!suppressClick) clear(); });
    zoomBtn.addEventListener('click', function () { clear(); });

    wireZoom();
    wireMenu();
    paint();
    legend();
  }

  /* ------------------------------------------------------------------ paint */
  function paint() {
    var max = maxValue();
    Array.prototype.forEach.call(gStates.children, function (p) {
      var code = p.getAttribute('data-code');
      var v = value(code);
      p.style.fill = fillFor(v, max);
      p.classList.toggle('has-data', v > 0);
      // Neighbours keep their outline when one state is selected; only the fill
      // recedes. A greyed-out border loses the geographic context of the zoom.
      p.classList.toggle('context', !!selected && selected !== code);
      p.classList.toggle('selected', selected === code);
    });
    Array.prototype.forEach.call(gLabels.children, function (t) {
      var code = t.getAttribute('data-code');
      t.classList.toggle('on', value(code) > 0);
      t.style.display = (selected === code) ? 'none' : '';
    });
    Array.prototype.forEach.call(chipbox.children, function (b) {
      b.classList.toggle('has-data', value(b.getAttribute('data-code')) > 0);
    });
    legend();
  }

  function legend() {
    var box = document.getElementById('legend');
    if (!box || !index) return;
    var max = maxValue();
    var steps = [0, 0.25, 0.5, 0.75, 1].map(function (t) {
      return '<i style="background:' + fillFor(t * max, max) + '"></i>';
    }).join('');
    box.innerHTML = '<div class="ramp">' + steps + '</div>0 &nbsp;\u2192&nbsp; ' + max + ' ' +
      unitLabel() + (family && metric !== 'lens' ? ' in this family' : '') +
      (metric === 'lens' ? '<div class="hint">Arizona was swept by department; other states only via papers. Not comparable \u2014 read best fit.</div>' : '') +
      '<div class="hint">wheel to zoom &middot; drag to pan &middot; right click for options</div>';
  }

  /* -------------------------------------------------------------------- tip */
  function showTip(code, e) {
    var r = index.states[code];
    if (!r) return;
    var rows;
    if (r.status === 'loaded') {
      rows = '<div class="row">institutions <span>' + r.institutions_in_scope + '</span></div>' +
             '<div class="row">programs on file <span>' +
                (family ? (r.by_family[family] || 0) : r.programs) + '</span></div>' +
             '<div class="row">stage <span>' + (r.stage || '\u2014') + '</span></div>';
      tip.classList.remove('empty');
    } else {
      rows = '<div class="row">no data pack yet</div>';
      tip.classList.add('empty');
    }
    if (r.lens) {
      rows += '<div class="row lensrow">faculty lens <span>' + r.lens.faculty + ' found \u00b7 ' +
        r.lens.physics + ' physics \u00b7 best ' + r.lens.best_fit + '/5</span></div>';
      tip.classList.remove('empty');
    }
    tip.innerHTML = '<b>' + r.name + '</b>' + rows;
    tip.style.display = 'block';
    var box = wrap.getBoundingClientRect();
    var x = e ? (e.clientX - box.left + 14) : 20;
    var y = e ? (e.clientY - box.top + 14) : 20;
    tip.style.left = Math.min(x, box.width - tip.offsetWidth - 12) + 'px';
    tip.style.top = Math.min(y, box.height - tip.offsetHeight - 12) + 'px';
  }

  function hideTip() { tip.style.display = 'none'; }

  /* ------------------------------------------------------------ view engine */
  function setView(v) {
    var w = Math.max(MIN_W, Math.min(v.w, canvas.width * 1.4));
    var h = w * (canvas.height / canvas.width);
    var x = Math.max(-canvas.width * 0.25, Math.min(v.x, canvas.width * 1.25 - w));
    var y = Math.max(-canvas.height * 0.25, Math.min(v.y, canvas.height * 1.25 - h));
    view = { x: x, y: y, w: w, h: h };
    svg.setAttribute('viewBox', view.x + ' ' + view.y + ' ' + view.w + ' ' + view.h);
    scaleMarkers();
    zoomBtn.classList.toggle('on', view.w < canvas.width * 0.98 || !!selected);
  }

  function scale() { return canvas.width / view.w; }

  /* Markers counter-scale so they stay a constant size on screen. Labels do not
     stack: institutions are laid out in program-count order and a label is drawn
     only where it does not collide with one already drawn. The suppressed ones
     reveal on hover, focus, or when their panel card is open. Stacking them was
     the alternative and it built a 14-row tower over the Bay Area. */
  function scaleMarkers() {
    var k = scale();
    var drawn = [];
    markerRecs.concat(siteRecs.filter(function (s) { return !s.hidden; })).forEach(function (m) {
      m.g.setAttribute('transform', 'translate(' + m.x + ',' + m.y + ') scale(' + (1 / k) + ')');
      var sx = m.x * k, sy = m.y * k;
      var clash = drawn.some(function (d) {
        return Math.abs(d[0] - sx) < m.labelWidth && Math.abs(d[1] - sy) < 11;
      });
      if (clash) {
        m.g.classList.add('nolabel');
      } else {
        m.g.classList.remove('nolabel');
        drawn.push([sx, sy]);
      }
    });
  }

  function tweenTo(target, ms) {
    if (anim) cancelAnimationFrame(anim);
    if (reduced()) { setView(target); return; }
    var from = { x: view.x, y: view.y, w: view.w, h: view.h }, t0 = performance.now();
    function frame(now) {
      var t = Math.min((now - t0) / ms, 1);
      var e = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      setView({
        x: from.x + (target.x - from.x) * e,
        y: from.y + (target.y - from.y) * e,
        w: from.w + (target.w - from.w) * e,
        h: from.h + (target.h - from.h) * e
      });
      if (t < 1) anim = requestAnimationFrame(frame);
    }
    anim = requestAnimationFrame(frame);
  }

  /* Screen point -> canvas coordinate, honouring preserveAspectRatio letterboxing. */
  function toCanvas(clientX, clientY) {
    var r = svg.getBoundingClientRect();
    var s = Math.min(r.width / view.w, r.height / view.h);
    var offX = (r.width - view.w * s) / 2, offY = (r.height - view.h * s) / 2;
    return {
      x: view.x + (clientX - r.left - offX) / s,
      y: view.y + (clientY - r.top - offY) / s
    };
  }

  function zoomAt(factor, clientX, clientY) {
    var p = toCanvas(clientX, clientY);
    var w = Math.max(MIN_W, view.w / factor);
    var ratio = w / view.w;
    setView({ x: p.x - (p.x - view.x) * ratio, y: p.y - (p.y - view.y) * ratio, w: w, h: 0 });
  }

  function fitBox(b, padFrac) {
    var pad = (padFrac === undefined ? 0.12 : padFrac);
    var ar = canvas.width / canvas.height;
    var w = Math.max(b.w, b.h * ar) * (1 + pad);
    var h = w / ar;
    return { x: b.x + b.w / 2 - w / 2, y: b.y + b.h / 2 - h / 2, w: w, h: h };
  }

  function boxForState(code) {
    var b = geo.states[code].bbox;
    return fitBox({ x: b[0], y: b[1], w: b[2] - b[0], h: b[3] - b[1] }, 0.45);
  }

  function resetView() { tweenTo({ x: 0, y: 0, w: canvas.width, h: canvas.height }, 520); }

  /* ------------------------------------------------------ pan / wheel / box */
  function wireZoom() {
    svg.addEventListener('wheel', function (e) {
      e.preventDefault();
      hideTip();
      zoomAt(e.deltaY < 0 ? 1.18 : 1 / 1.18, e.clientX, e.clientY);
    }, { passive: false });

    svg.addEventListener('mousedown', function (e) {
      if (e.button === 2) return;                       // right button opens the menu
      hideMenu();
      var box = armedBox || e.shiftKey;
      drag = {
        box: box,
        startClient: [e.clientX, e.clientY],
        start: toCanvas(e.clientX, e.clientY),
        view0: { x: view.x, y: view.y, w: view.w, h: view.h },
        moved: false
      };
      if (box) {
        wrap.classList.add('boxing');
        gBox.innerHTML = '<rect class="boxsel" x="0" y="0" width="0" height="0" />';
      }
      e.preventDefault();
    });

    window.addEventListener('mousemove', function (e) {
      if (!drag) return;
      var dxs = e.clientX - drag.startClient[0], dys = e.clientY - drag.startClient[1];
      if (!drag.moved && Math.abs(dxs) + Math.abs(dys) > 3) { drag.moved = true; hideTip(); }
      if (!drag.moved) return;

      if (drag.box) {
        var p = toCanvas(e.clientX, e.clientY);
        var r = gBox.firstChild;
        r.setAttribute('x', Math.min(drag.start.x, p.x));
        r.setAttribute('y', Math.min(drag.start.y, p.y));
        r.setAttribute('width', Math.abs(p.x - drag.start.x));
        r.setAttribute('height', Math.abs(p.y - drag.start.y));
      } else {
        var rect = svg.getBoundingClientRect();
        var s = Math.min(rect.width / drag.view0.w, rect.height / drag.view0.h);
        setView({ x: drag.view0.x - dxs / s, y: drag.view0.y - dys / s, w: drag.view0.w, h: 0 });
        wrap.classList.add('panning');
      }
    });

    window.addEventListener('mouseup', function (e) {
      if (!drag) return;
      var d = drag; drag = null;
      wrap.classList.remove('panning', 'boxing');
      if (d.box) {
        var p = toCanvas(e.clientX, e.clientY);
        var w = Math.abs(p.x - d.start.x), h = Math.abs(p.y - d.start.y);
        gBox.innerHTML = '';
        armedBox = false;
        if (d.moved && w > 6 && h > 6) {
          tweenTo(fitBox({ x: Math.min(d.start.x, p.x), y: Math.min(d.start.y, p.y), w: w, h: h }, 0.05), 420);
          GF.ui.say('zoomed to selection');
        }
      }
      if (d.moved) {
        suppressClick = true;
        setTimeout(function () { suppressClick = false; }, 0);
      }
    });

    svg.addEventListener('dblclick', function (e) { zoomAt(1.9, e.clientX, e.clientY); });
  }

  /* ------------------------------------------------------------ right click */
  function wireMenu() {
    svg.addEventListener('contextmenu', function (e) {
      e.preventDefault();
      var code = e.target && e.target.getAttribute ? e.target.getAttribute('data-code') : null;
      openMenu(e.clientX, e.clientY, code);
    });
    document.addEventListener('click', hideMenu);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') hideMenu(); });
  }

  function openMenu(clientX, clientY, code) {
    var name = code && geo.states[code] ? geo.states[code].name : null;
    var loaded = code && index.states[code] && index.states[code].status === 'loaded';
    var items = [];

    if (name) {
      items.push({ label: (loaded ? 'Open ' : 'Zoom to ') + name, act: function () { select(code); } });
      if (!loaded) items.push({ label: 'No data pack for ' + code + ' yet', disabled: true });
      items.push({ sep: true });
    }
    items.push({
      label: 'Box zoom \u2014 drag a rectangle', key: 'shift+drag',
      act: function () {
        armedBox = true;
        wrap.classList.add('armed');
        GF.ui.say('box zoom armed \u2014 drag a rectangle on the map');
        setTimeout(function () { wrap.classList.remove('armed'); }, 1600);
      }
    });
    items.push({ label: 'Zoom in here', key: 'wheel', act: function () { zoomAt(1.6, clientX, clientY); } });
    items.push({ label: 'Zoom out', key: 'wheel', act: function () { zoomAt(1 / 1.6, clientX, clientY); } });
    items.push({ sep: true });
    items.push({ label: 'Reset view', key: 'Esc', act: function () { clear(); resetView(); } });

    menu.innerHTML = items.map(function (it, i) {
      if (it.sep) return '<div class="sep"></div>';
      return '<button data-i="' + i + '"' + (it.disabled ? ' disabled' : '') + '>' +
        '<span>' + it.label + '</span>' + (it.key ? '<em>' + it.key + '</em>' : '') + '</button>';
    }).join('');

    Array.prototype.forEach.call(menu.querySelectorAll('button'), function (b) {
      b.addEventListener('click', function (ev) {
        ev.stopPropagation();
        var it = items[parseInt(b.getAttribute('data-i'), 10)];
        hideMenu();
        if (it && it.act) it.act();
      });
    });

    var box = wrap.getBoundingClientRect();
    menu.style.display = 'block';
    menu.style.left = Math.max(4, Math.min(clientX - box.left, box.width - menu.offsetWidth - 8)) + 'px';
    menu.style.top = Math.max(4, Math.min(clientY - box.top, box.height - menu.offsetHeight - 8)) + 'px';
    hideTip();
  }

  function hideMenu() { if (menu) menu.style.display = 'none'; }

  /* -------------------------------------------------------------- selection */
  function select(code) {
    selected = code;
    paint();
    tweenTo(boxForState(code), 620);
    hideTip();
    if (onSelect) onSelect(code);
  }

  function clear() {
    hideMenu();
    if (!selected) { resetView(); return; }
    selected = null;
    gMarkers.innerHTML = '';
    markerRecs = [];
    siteRecs.forEach(function (s) { s.hidden = false; s.g.style.display = sitesOn ? '' : 'none'; });
    highlightSite(null);
    paint();
    resetView();
    if (onSelect) onSelect(null);
  }

  /* ---------------------------------------------------------------- markers */
  function markers(detail, onPick) {
    gMarkers.innerHTML = '';
    markerRecs = [];
    var ids = {};
    if (detail && detail.institutions) detail.institutions.forEach(function (i) { ids[i.id] = 1; });
    siteRecs.forEach(function (s) {
      s.hidden = !!(s.site.inst_id && ids[s.site.inst_id]);
      s.g.style.display = (s.hidden || !sitesOn) ? 'none' : '';
    });
    if (!detail || !detail.institutions) { scaleMarkers(); return; }
    var NS = 'http://www.w3.org/2000/svg';
    detail.institutions.forEach(function (inst) {
      var g = document.createElementNS(NS, 'g');
      g.setAttribute('class', 'marker' + (inst.status === 'boundary' ? ' boundary' : ''));
      g.setAttribute('data-x', inst.xy[0]);
      g.setAttribute('data-y', inst.xy[1]);
      g.setAttribute('data-id', inst.id);
      g.setAttribute('tabindex', '0');
      g.setAttribute('role', 'button');
      g.setAttribute('aria-label', inst.name + ', ' + inst.program_count + ' programs');

      var halo = document.createElementNS(NS, 'circle');
      halo.setAttribute('class', 'halo');
      halo.setAttribute('r', 4 + Math.sqrt(inst.program_count) * 1.9);
      var dot = document.createElementNS(NS, 'circle');
      dot.setAttribute('class', 'dot');
      dot.setAttribute('r', 3.2);
      var label = document.createElementNS(NS, 'text');
      label.setAttribute('x', 9);
      label.setAttribute('y', 3.4);
      label.textContent = (inst.short || inst.name) + '  \u00b7  ' + inst.program_count;

      g.appendChild(halo); g.appendChild(dot); g.appendChild(label);
      markerRecs.push({
        g: g, label: label, x: inst.xy[0], y: inst.xy[1],
        labelWidth: 18 + label.textContent.length * 5.2   // 8.5px mono, plus the dot offset
      });
      g.addEventListener('click', function (e) { e.stopPropagation(); if (onPick) onPick(inst.id); });
      g.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); if (onPick) onPick(inst.id); }
      });
      gMarkers.appendChild(g);
    });
    scaleMarkers();
  }

  function highlight(id) {
    Array.prototype.forEach.call(gMarkers.children, function (g) {
      g.classList.toggle('active', g.getAttribute('data-id') === id);
    });
  }

  /* ------------------------------------------------------ faculty sites
     One lime diamond per university the paper trace reached. Size follows the
     number of faculty found there, opacity the best fit. Drawn under the
     institution markers and hidden where a pack marker already sits. */
  function sites(list, onPick) {
    gSites.innerHTML = '';
    siteRecs = [];
    var NS = 'http://www.w3.org/2000/svg';
    (list || []).forEach(function (s) {
      if (!s.xy) return;
      var g = document.createElementNS(NS, 'g');
      g.setAttribute('class', 'site fit' + s.best_fit);
      g.setAttribute('tabindex', '0');
      g.setAttribute('role', 'button');
      g.setAttribute('aria-label', s.university + ', ' + s.faculty + ' faculty, best fit ' + s.best_fit);
      var r = 3.4 + Math.sqrt(s.faculty) * 1.5;
      var dia = document.createElementNS(NS, 'path');
      dia.setAttribute('class', 'dia');
      dia.setAttribute('d', 'M0,' + (-r) + ' L' + r + ',0 L0,' + r + ' L' + (-r) + ',0 Z');
      var label = document.createElementNS(NS, 'text');
      label.setAttribute('x', r + 4);
      label.setAttribute('y', 3.2);
      label.textContent = s.short + '  ' + s.best_fit + '/5';
      g.appendChild(dia); g.appendChild(label);
      g.addEventListener('click', function (e) { e.stopPropagation(); if (onPick) onPick(s); });
      g.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); if (onPick) onPick(s); }
      });
      g.addEventListener('mousemove', function (e) { showSiteTip(s, e); });
      g.addEventListener('mouseleave', hideTip);
      gSites.appendChild(g);
      siteRecs.push({ g: g, label: label, x: s.xy[0], y: s.xy[1], site: s, hidden: false,
                      labelWidth: r + 10 + label.textContent.length * 5.2 });
    });
    scaleMarkers();
  }

  function showSiteTip(s, e) {
    var rows = '<div class="row">' + esc(s.city || '') + ', ' + s.state + '</div>' +
      '<div class="row">faculty found <span>' + s.faculty + '</span></div>' +
      '<div class="row">in physics <span>' + s.physics + '</span></div>' +
      '<div class="row">best fit <span>' + s.best_fit + '/5</span></div>' +
      s.top.map(function (f) { return '<div class="row lensrow">' + esc(f.name) + ' <span>' + f.fit + '/5</span></div>'; }).join('');
    tip.classList.remove('empty');
    tip.innerHTML = '<b>' + esc(s.university) + '</b>' + rows;
    tip.style.display = 'block';
    var box = wrap.getBoundingClientRect();
    tip.style.left = Math.min(e.clientX - box.left + 14, box.width - tip.offsetWidth - 12) + 'px';
    tip.style.top = Math.min(e.clientY - box.top + 14, box.height - tip.offsetHeight - 12) + 'px';
  }

  function esc(t) {
    return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function setSites(on) {
    sitesOn = !!on;
    siteRecs.forEach(function (s) { s.g.style.display = (s.hidden || !sitesOn) ? 'none' : ''; });
    scaleMarkers();
  }

  function highlightSite(name) {
    siteRecs.forEach(function (s) { s.g.classList.toggle('active', s.site.university === name); });
  }

  function setIndex(doc) { index = doc; paint(); }
  function setFamily(key) { family = key || ''; paint(); }
  function setMetric(key) { metric = key; paint(); }

  return {
    build: build, select: select, clear: clear, markers: markers, highlight: highlight,
    setIndex: setIndex, setFamily: setFamily, setMetric: setMetric, reset: resetView,
    sites: sites, setSites: setSites, highlightSite: highlightSite,
    get selected() { return selected; },
    get metric() { return metric; }
  };
})();
