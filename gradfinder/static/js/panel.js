/* Right-hand panel. Renders one state's pack; renders an actionable empty
   state for the 50 jurisdictions that do not have one yet. */
window.GF = window.GF || {};

GF.panel = (function () {
  var root, families = [], onPick = null, lensDoc = null;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function init(familyList, pickCb) {
    root = document.getElementById('panel');
    families = familyList;
    onPick = pickCb;
  }

  function idle() {
    root.innerHTML = '<div class="empty"><b>Pick a state</b>Hover to read the totals, click to ' +
      'open the institutions. Four states have data packs; the rest are outlines waiting on one. ' +
      'Lime diamonds are universities found by the paper trace \u2014 click one, or pick it from ' +
      'the list in the left rail, to open its faculty.</div>';
  }

  function empty(doc, lens) {
    root.innerHTML =
      '<h2>' + esc(doc.name) + '</h2>' +
      '<div class="sub">' + esc(doc.state) + ' &middot; no pack on file</div>' +
      '<div class="empty"><b>Nothing collected yet</b>' +
      esc(doc.message || '') + '<br><br>Next step: create <code>data/institutions/' +
      esc(doc.state) + '.json</code> against the same schema as the Arizona pack, then reload. ' +
      'The map picks it up without a restart.</div>' + lensSection(lens);
  }

  function famBars(rollup) {
    var max = 1;
    families.forEach(function (f) { max = Math.max(max, rollup.by_family[f.key] || 0); });
    return families.map(function (f) {
      var v = rollup.by_family[f.key] || 0;
      return '<div class="fambar' + (v ? '' : ' zero') + '">' +
        '<div class="track"><i style="width:' + (100 * v / max) + '%"></i><u>' + esc(f.label) + '</u></div>' +
        '<em>' + v + '</em></div>';
    }).join('');
  }

  /* A program row links to the program's own page when the pack carries a verified
     URL. It usually does not, so the fallback is a site-scoped search on the
     institution's own domain. That is a search, not a deep link, and it is
     labelled as one -- inventing plausible department URLs would be worse than
     making the user click through a search. */
  function programLink(inst, p) {
    if (p.url) return { href: p.url, kind: 'direct' };
    if (!inst.domain) return null;
    var q = 'site:' + inst.domain + ' "' + p.name + '" PhD graduate';
    return { href: 'https://duckduckgo.com/?q=' + encodeURIComponent(q), kind: 'search' };
  }

  var GPA_TONE = { 'floor': 'hard', 'recommended': 'soft', 'reported typical': 'soft' };

  function gpaChip(g, compact) {
    if (!g) return '';
    var tone = GPA_TONE[g.type] || 'soft';
    var label = g.value.toFixed(2) + (g.scale ? '/' + g.scale.toFixed(1) : '');
    if (compact) {
      return '<a class="gpa ' + tone + '" href="' + esc(g.source_url) + '" target="_blank" ' +
        'rel="noopener" title="' + esc(g.type + ' \u2014 ' + g.basis) + '">' + label + '</a>';
    }
    return '<div class="gpa-row">' +
      '<span class="gpa ' + tone + '">' + label + '</span>' +
      '<span class="gpa-meta"><b>' + esc(g.type) + '</b>, ' + esc(g.scope) + '-wide' +
        '<br>basis: ' + esc(g.basis) +
        (g.waiver ? '<br>waiver: ' + esc(g.waiver) : '') +
        (g.note ? '<br>' + esc(g.note) : '') +
        '<br><a href="' + esc(g.source_url) + '" target="_blank" rel="noopener">source</a>' +
        ' &middot; read ' + esc(g.as_of) +
      '</span></div>';
  }

  function admissionsBlock(inst) {
    var a = inst.admissions;
    if (!a) return '';
    if (!a.gpa_min) {
      return '<div class="adm empty-adm">Minimum GPA not collected for this institution. ' +
        'The field is empty rather than assuming the usual 3.0 &mdash; a missing value and a ' +
        'known value have to look different.</div>';
    }
    return '<div class="adm">' + gpaChip(a.gpa_min, false) + '</div>';
  }

  function institution(inst) {
    var anySearch = false;
    var progs = (inst.programs || []).map(function (p) {
      var fam = families.filter(function (f) { return f.key === p.family; })[0];
      var link = programLink(inst, p);
      var name = esc(p.name) + (p.flag ? ' \u2014 ' + esc(p.flag) : '');
      if (link) {
        if (link.kind === 'search') anySearch = true;
        name = '<a href="' + esc(link.href) + '" target="_blank" rel="noopener" class="' +
          link.kind + '" title="' + (link.kind === 'direct'
            ? 'Program page from the data pack'
            : 'Site search on ' + esc(inst.domain) + ' \u2014 not a verified link') +
          '">' + name + '</a>';
      }
      var pg = (p.admissions && p.admissions.gpa_min) ? gpaChip(p.admissions.gpa_min, true) : '';
      return '<li' + (p.flag ? ' class="flagged"' : '') + '><span>' + name + pg + '</span>' +
        '<em>' + esc(fam ? fam.label : p.family) + '</em></li>';
    }).join('');

    var meta = [inst.city, inst.control, inst.carnegie].filter(Boolean).map(esc).join(' &middot; ');
    var badge = inst.status === 'boundary'
      ? '<span class="badge warn">boundary</span>'
      : (inst.program_list_complete ? '<span class="badge ok">list complete</span>' : '<span class="badge">partial list</span>');

    return '<div class="inst' + (inst.status === 'boundary' ? ' boundary' : '') + '" data-id="' + esc(inst.id) + '">' +
      '<button class="head" aria-expanded="false">' +
        '<span><span class="nm">' + esc(inst.name) + '</span>' + badge +
        '<br><span class="meta">' + meta + '</span></span>' +
        '<span class="n">' + inst.program_count + '<span>programs</span></span>' +
      '</button>' +
      '<div class="drawer">' +
        (inst.notes ? '<div class="note">' + esc(inst.notes) + '</div>' : '') +
        admissionsBlock(inst) +
        instFaculty(inst) +
        '<div class="links">' +
          (inst.website ? '<a href="' + esc(inst.website) + '" target="_blank" rel="noopener">Graduate catalogue</a>' : '') +
          (inst.domain ? '<a href="https://' + esc(inst.domain) + '" target="_blank" rel="noopener">' + esc(inst.domain) + '</a>' : '') +
          (inst.domain ? '<a href="https://duckduckgo.com/?q=' +
            encodeURIComponent('site:' + inst.domain + ' PhD programs graduate') +
            '" target="_blank" rel="noopener">All doctoral programs</a>' : '') +
        '</div>' +
        '<ul class="progs">' + progs + '</ul>' +
        (anySearch ? '<div class="linknote">Program names run a site search on ' +
          esc(inst.domain) + '. The pack does not carry verified program URLs yet, so these ' +
          'are searches rather than deep links.</div>' : '') +
      '</div></div>';
  }

  /* ---------------------------------------------------------- faculty lens
     Faculty found top-down: a paper, its senior author, that author's current
     university. Independent of the state pack, so it shows for states with no
     pack at all. The fit number is a hand judgment, and says so. */
  var PHYS = { yes: ['ok', 'physics'], joint: ['warn', 'joint physics'], no: ['', 'other dept'] };

  function fitPips(n) {
    var out = '';
    for (var i = 1; i <= 5; i++) out += '<i class="' + (i <= n ? 'on' : '') + '"></i>';
    return '<span class="pips" title="fit ' + n + '/5 (hand-assigned)">' + out + '</span>';
  }

  function facultyRow(f) {
    var ph = PHYS[f.physics_dept] || PHYS.no;
    var papers = (f.papers || []).map(function (p) {
      return '<li><a href="' + esc(p.url) + '" target="_blank" rel="noopener">' + esc(p.title) + '</a>' +
        '<em>' + esc(p.year) + ' \u00b7 ' + esc(p.venue) + '</em></li>';
    }).join('');
    var flag = f.note && /FLAG|NOT verified|RECRUITING|SEED/i.test(f.note);
    return '<div class="fac">' +
      '<div class="fac-head">' + fitPips(f.fit) +
        '<a class="fac-nm" href="' + esc(f.page) + '" target="_blank" rel="noopener">' + esc(f.name) + '</a>' +
        '<span class="badge ' + ph[0] + '">' + ph[1] + '</span></div>' +
      '<div class="fac-dept">' + esc(f.department) + '</div>' +
      (f.note ? '<div class="fac-note' + (flag ? ' hot' : '') + '">' + esc(f.note) + '</div>' : '') +
      (papers ? '<ul class="fac-papers">' + papers + '</ul>' : '') +
      '</div>';
  }

  function lensSection(lens) {
    if (!lens || !lens.universities || !lens.universities.length) {
      return '<div class="sect lens"><h3>Faculty lens</h3><div class="excl">No faculty in this state ' +
        'surfaced from the paper trace yet.</div></div>';
    }
    var r = lens.rollup, m = (lens.meta && lens.meta[0]) || {};
    var seed = m.seed ? '<div class="lens-seed">Seed: <a href="' + esc(m.seed.url) + '" target="_blank" rel="noopener">' +
      esc(m.seed.title) + '</a> \u2014 ' + esc(m.seed.venue) + '</div>' : '';
    var html = '<div class="sect lens"><h3>Faculty lens \u2014 traced from papers</h3>' + seed +
      '<div class="lens-stats"><span><b>' + r.faculty + '</b> faculty</span><span><b>' + r.physics +
      '</b> physics</span><span><b>' + r.strong + '</b> fit \u2265 4</span><span><b>' + r.best_fit +
      '</b>/5 best</span></div>';
    if (lens.state === 'AZ') {
      html += '<div class="lens-warn">Arizona was swept department by department; every other state entered ' +
        'only through papers. Counts here are inflated relative to other states.</div>';
    }
    html += lens.universities.map(function (u) {
      var top = u.faculty.slice(0, 3).map(function (f) { return esc(f.name); }).join(', ');
      return '<details class="lens-uni" data-uni="' + esc(u.university) + '"' + (u.faculty.length <= 5 ? ' open' : '') + '>' +
        '<summary class="lens-uni-h">' + esc(u.university) +
        '<span>best ' + u.best_fit + '/5 \u00b7 ' + u.faculty.length + ' found</span>' +
        (u.faculty.length > 5 ? '<div class="lens-top">top: ' + top + ' \u2014 click to expand</div>' : '') +
        '</summary>' +
        u.faculty.map(facultyRow).join('') + '</details>';
    }).join('');
    return html + '</div>';
  }

  function instFaculty(inst) {
    if (!lensDoc || !lensDoc.universities) return '';
    var u = lensDoc.universities.filter(function (x) { return x.inst_id === inst.id; })[0];
    if (!u) return '';
    return '<div class="inst-lens"><b>Faculty lens</b> ' + u.faculty.map(function (f) {
      return '<span>' + esc(f.name) + ' ' + f.fit + '/5</span>';
    }).join(' \u00b7 ') + '</div>';
  }

  function render(doc, lens) {
    lensDoc = lens || null;
    if (doc.__notfound || doc.status === 'empty') { empty(doc, lens); return; }
    var r = doc.rollup;
    var p = doc.provenance || {};
    var filtered = doc.filter && doc.filter.family;

    var html =
      '<h2>' + esc(r.name) + '<span class="badge">' + esc(r.stage || 'unstaged') + '</span></h2>' +
      '<div class="sub">' + r.institutions + ' institutions on file &middot; pack generated ' +
        esc(doc.generated || '\u2014') + '</div>';

    html += '<div class="stats">' +
      '<div class="stat"><b>' + r.institutions_in_scope + '</b><span>institutions in scope</span></div>' +
      '<div class="stat"><b>' + r.programs + '</b><span>doctoral programs on file</span></div>' +
      '<div class="stat"><b>' + r.stem_core_programs + '</b><span>in core STEM families</span></div>' +
      '<div class="stat muted"><b>' + r.excluded + '</b><span>institutions screened out</span></div>' +
      '</div>';

    if (p.note) {
      html += '<div class="sect"><h3>How to read these</h3><div class="excl">' + esc(p.note) + '</div></div>';
    }

    html += lensSection(lens);

    html += '<div class="sect"><h3>Programs by family</h3><div class="fambars">' + famBars(r) + '</div></div>';

    html += '<div class="sect"><h3>Institutions' +
      (filtered ? ' \u2014 filtered' : '') + '</h3>' +
      (doc.institutions.length ? doc.institutions.map(institution).join('')
        : '<div class="empty">No institution in this state lists a program in that family.</div>') +
      '</div>';

    if (doc.excluded && doc.excluded.length) {
      html += '<div class="sect"><h3>Screened out</h3><ul class="excl" style="padding-left:16px">' +
        doc.excluded.map(function (x) {
          return '<li><b>' + esc(x.name) + '</b> (' + esc(x.city) + ') &mdash; ' + esc(x.reason) + '</li>';
        }).join('') + '</ul></div>';
    }

    if (doc.open_questions && doc.open_questions.length) {
      html += '<div class="sect"><h3>Open against this pack</h3><ul class="qlist">' +
        doc.open_questions.map(function (q) { return '<li>' + esc(q) + '</li>'; }).join('') +
        '</ul></div>';
    }

    if (doc.sources && doc.sources.length) {
      html += '<div class="sect"><h3>Sources</h3><ul class="qlist">' +
        doc.sources.map(function (s) {
          return '<li><a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.label) +
            '</a> &mdash; ' + esc(s.used_for) + '</li>';
        }).join('') + '</ul></div>';
    }

    root.innerHTML = html;
    root.scrollTop = 0;

    Array.prototype.forEach.call(root.querySelectorAll('.inst > button.head'), function (btn) {
      btn.addEventListener('click', function () {
        var card = btn.parentNode;
        var open = card.classList.toggle('open');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
        setActive(open ? card.getAttribute('data-id') : null);
        if (onPick) onPick(open ? card.getAttribute('data-id') : null);
      });
    });
  }

  /* One institution is "active" at a time. The card takes an amber outline that
     matches the selected-state outline on the map, so the marker you clicked and the
     card you are reading are visibly the same object. */
  function setActive(id) {
    Array.prototype.forEach.call(root.querySelectorAll('.inst'), function (c) {
      c.classList.toggle('active', !!id && c.getAttribute('data-id') === id);
    });
  }

  function openInstitution(id) {
    var card = root.querySelector('.inst[data-id="' + id + '"]');
    if (!card) return;
    Array.prototype.forEach.call(root.querySelectorAll('.inst'), function (c) {
      c.classList.toggle('open', c === card);
      var b = c.querySelector('button.head');
      if (b) b.setAttribute('aria-expanded', c === card ? 'true' : 'false');
    });
    setActive(id);
    card.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  function openLensUniversity(name) {
    var hit = null;
    Array.prototype.forEach.call(root.querySelectorAll('details.lens-uni'), function (d) {
      var me = d.getAttribute('data-uni') === name;
      d.classList.toggle('active', me);
      if (me) { d.open = true; hit = d; }
    });
    if (hit) hit.scrollIntoView({ block: 'start', behavior: 'smooth' });
  }

  return { init: init, openLensUniversity: openLensUniversity, render: render, idle: idle, empty: empty,
           openInstitution: openInstitution, setActive: setActive };
})();
