/* Page zoom (Tony 2026-11-02: wants the whole site at 140%, like Firefox zoom).
 * refined.css sets `zoom` on <html> (wide screens only). CSS zoom reports element
 * boxes and mouse positions in zoomed screen pixels, while the pages' scripts
 * position things in CSS pixels, so translate those APIs back to CSS pixels.
 * That is the same model the browser's own zoom gives scripts. vh/vw lengths
 * are also divided by the zoom so full-height panels still fit the window. */
(function () {
  'use strict';
  var H = document.documentElement;
  if (!H.classList.contains('ui-refined') || window.__rfZoomDone) return;
  window.__rfZoomDone = true;
  var origRect = Element.prototype.getBoundingClientRect;
  var Z = 1, F = 1;
  function measure() {
    Z = parseFloat(getComputedStyle(H).zoom) || 1;
    F = 1;
    if (Z !== 1 && document.body) {
      var d = document.createElement('div');
      d.style.cssText = 'position:absolute;left:0;top:0;width:100px;height:1px;visibility:hidden;pointer-events:none';
      document.body.appendChild(d);
      F = (origRect.call(d).width / 100) || 1;
      d.remove();
      if (Math.abs(F - 1) < 0.01) F = 1;
    }
    H.classList.toggle('rf-zoomed', Z !== 1);
  }
  window.__rfZoom = function () { return F; };
  function wrapGetter(proto, name) {
    var d = proto && Object.getOwnPropertyDescriptor(proto, name);
    if (!d || !d.get || !d.configurable) return;
    Object.defineProperty(proto, name, { configurable: true, enumerable: d.enumerable, get: function () { var v = d.get.call(this); return F === 1 ? v : v / F; } });
  }
  Element.prototype.getBoundingClientRect = function () {
    var r = origRect.call(this);
    return F === 1 ? r : new DOMRect(r.x / F, r.y / F, r.width / F, r.height / F);
  };
  var origRects = Element.prototype.getClientRects;
  Element.prototype.getClientRects = function () {
    var l = origRects.call(this);
    if (F === 1) return l;
    var out = [];
    for (var i = 0; i < l.length; i++) out.push(new DOMRect(l[i].x / F, l[i].y / F, l[i].width / F, l[i].height / F));
    out.item = function (i) { return out[i] || null; };
    return out;
  };
  ['clientX', 'clientY', 'pageX', 'pageY', 'x', 'y'].forEach(function (n) { wrapGetter(MouseEvent.prototype, n); });
  if (window.Touch) ['clientX', 'clientY', 'pageX', 'pageY'].forEach(function (n) { wrapGetter(Touch.prototype, n); });
  ['innerWidth', 'innerHeight'].forEach(function (n) {
    var d = Object.getOwnPropertyDescriptor(window, n);
    if (d && d.get && d.configurable) Object.defineProperty(window, n, { configurable: true, enumerable: d.enumerable, get: function () { var v = d.get.call(window); return F === 1 ? v : Math.round(v / F); }, set: d.set });
  });
  var origEFP = Document.prototype.elementFromPoint;
  Document.prototype.elementFromPoint = function (x, y) { return origEFP.call(this, x * F, y * F); };
  var origEsFP = Document.prototype.elementsFromPoint;
  if (origEsFP) Document.prototype.elementsFromPoint = function (x, y) { return origEsFP.call(this, x * F, y * F); };

  // vh / vw lengths -> divided by the zoom
  var VRE = /(-?[\d.]+)(vh|vw|dvh|svh|lvh)\b/g;
  function fixVal(v) { return v.replace(VRE, function (m, n, u) { return 'calc(' + n + u + ' / var(--rf-z, 1))'; }); }
  var memo = typeof WeakMap === 'function' ? new WeakMap() : null;
  function fixDecl(st, owner) {
    var m = owner && memo ? (memo.get(owner) || {}) : null;
    for (var i = 0; i < st.length; i++) {
      var prop = st[i], val = st.getPropertyValue(prop);
      if (!val || !/v[hw]\b/.test(val)) continue;
      if (m && m[prop] === val) continue;          // already converted by us
      st.setProperty(prop, fixVal(val), st.getPropertyPriority(prop));
      if (m) m[prop] = st.getPropertyValue(prop);
    }
    if (m) memo.set(owner, m);
  }
  var doneRules = typeof WeakSet === 'function' ? new WeakSet() : null;
  function walk(rules) {
    for (var i = 0; i < rules.length; i++) {
      var r = rules[i];
      try {
        if (r.cssRules && !r.style) { walk(r.cssRules); continue; }
        if (!r.style || (doneRules && doneRules.has(r))) continue;
        if (doneRules) doneRules.add(r);
        if (/v[hw]\b/.test(r.style.cssText)) fixDecl(r.style);
      } catch (e) {}
    }
  }
  function fixSheets() {
    for (var i = 0; i < document.styleSheets.length; i++) {
      var rules; try { rules = document.styleSheets[i].cssRules; } catch (e) { continue; }
      if (rules) walk(rules);
    }
  }
  function fixInline(root) {
    var list = (root || document).querySelectorAll ? (root || document).querySelectorAll('[style*="vh"],[style*="vw"]') : [];
    for (var i = 0; i < list.length; i++) fixDecl(list[i].style, list[i]);
    if (root && root.nodeType === 1 && root.getAttribute('style') && /v[hw]\b/.test(root.getAttribute('style'))) fixDecl(root.style, root);
  }
  function fixAll() { if (Z === 1 && !H.classList.contains('rf-nozoom')) return; fixSheets(); fixInline(); }
  function start() {
    // Live View (matrix overlay on the dashboard) runs at 100%
    var mx = document.getElementById('matrix-overlay');
    var syncMx = function () {
      var off = !!(mx && mx.classList.contains('active'));
      if (H.classList.contains('rf-nozoom') !== off) { H.classList.toggle('rf-nozoom', off); measure(); }
    };
    if (mx) new MutationObserver(syncMx).observe(mx, { attributes: true, attributeFilter: ['class'] });
    syncMx();
    measure();
    if (Z === 1 && !mx) return;
    fixAll();
    var pending = false;
    new MutationObserver(function () {
      if (pending) return; pending = true;
      setTimeout(function () { pending = false; fixAll(); }, 50);
    }).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['style'] });
  }
  if (document.body) start(); else document.addEventListener('DOMContentLoaded', start);
  window.addEventListener('load', fixAll);
  window.addEventListener('resize', function () { var z = Z; measure(); if (Z !== z) fixAll(); });
})();
/* Refined interface layout script.
 * Moves the page's EXISTING controls into a left navigation rail and a slim
 * top bar. Nothing is cloned or removed, so every id, handler and feature is
 * preserved. Runs only when the interface style is "refined". */
(function () {
  'use strict';
  var H = document.documentElement;
  if (!H.classList.contains('ui-refined') || window.__rfLayoutDone) return;
  window.__rfLayoutDone = true;

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function el(tag, attrs, html) {
    var e = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (html != null) e.innerHTML = html;
    return e;
  }
  var path = location.pathname.replace(/\/+$/, '') || '/';
  H.classList.add('rf-page-' + ((path.split('/')[1] || 'home').replace(/[^a-z0-9-]/gi, '') || 'home'));

  // Original mark: a lens ring with a small status dot.
  var LOGO = '<svg viewBox="0 0 32 32" aria-hidden="true"><rect x="1" y="1" width="30" height="30" rx="9" fill="currentColor" opacity=".08"/>' +
    '<circle cx="16" cy="16" r="8.2" fill="none" stroke="currentColor" stroke-width="2.2"/>' +
    '<circle cx="16" cy="16" r="3.4" fill="currentColor"/><circle cx="24.6" cy="7.6" r="2.2" fill="#3fcf74"/></svg>';

  // Icons: make sure the icon font is present (a few pages don't load it themselves).
  if (!$('link[href*="font-awesome"], link[href*="fontawesome"]')) {
    document.head.appendChild(el('link', { rel: 'stylesheet', href: 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css' }));
  }

  // Auth pages get the palette only.
  if (path === '/login' || path === '/setup') { H.classList.add('rf-auth', 'rf-ready'); return; }

  var rail = el('aside', { id: 'rf-rail', 'aria-label': 'Main navigation' });
  var brand = el('a', { class: 'rf-brand', href: '/', title: 'Cameras' }, LOGO);
  var nav = el('nav', { class: 'rf-nav' });
  var bottom = el('div', { class: 'rf-rail-bottom' });
  rail.appendChild(brand); rail.appendChild(nav); rail.appendChild(bottom);

  function wrapLabel(btn) {
    // Put the button's text into a span so the rail can lay it out under the icon.
    var nodes = Array.prototype.slice.call(btn.childNodes);
    var span = btn.querySelector(':scope > span:not(.rf-label)');
    if (span && !span.querySelector('i')) { span.classList.add('rf-label'); return; }
    var text = '';
    nodes.forEach(function (n) { if (n.nodeType === 3 && n.textContent.trim()) { text += n.textContent.trim() + ' '; btn.removeChild(n); } });
    if (text) btn.appendChild(el('span', { class: 'rf-label' }, null)).textContent = text.trim();
  }
  function railItem(href, icon, label, extra) {
    var a = el('a', { class: 'rf-item', href: href }, '<i class="' + icon + '"></i><span class="rf-label"></span>');
    a.querySelector('.rf-label').textContent = label;
    if (extra) Object.keys(extra).forEach(function (k) { a.setAttribute(k, extra[k]); });
    return a;
  }
  function activeFor(p) {
    if (p === '/' ) return 'cameras';
    if (p === '/matrix') return 'matrix';
    if (p === '/onvif' || p === '/ai') return 'onvif';
    if (p === '/gridfusion') return 'gridfusion';
    if (p === '/alerts') return 'alerts';
    if (p === '/ip-management') return 'ip';
    if (p === '/diagnostics') return 'diagnostics';
    if (p === '/logs') return 'logs';
    if (p === '/server') return 'server';
    if (p === '/settings') return 'settings';
    if (p === '/about') return 'about';
    if (p === '/add-camera' || p.indexOf('/camera/') === 0) return 'cameras';
    if (p.indexOf('/addon/') === 0 || p === '/nvr') return 'addons';
    return '';
  }
  var current = activeFor(path);

  var container = $('.container');
  var header = container && $(':scope > .header', container);

  if (header && $('.actions', header)) {
    /* ---------------- Dashboard / addon-page frame ---------------- */
    H.classList.add('rf-shell');
    var actions = $('.actions', header);
    var addBtn = null;

    var home = railItem('/', 'fa-solid fa-video', 'Cameras', { 'data-rf': 'cameras' });
    if (!$('#camera-list.camera-grid')) home.setAttribute('href', '/');
    home.addEventListener('click', function (e) {
      // On the dashboard itself, just close any full-screen view.
      if (location.pathname === '/' || location.pathname === '/matrix' || location.pathname === '/onvif' || location.pathname === '/ai') {
        if ($('#camera-list.camera-grid')) {
          e.preventDefault();
          try { var mo = $('#matrix-overlay'); if (mo && mo.classList.contains('active')) toggleMatrixView(false); } catch (_) {}
          try { var ov = $('#onvif-overlay'); if (ov && ov.classList.contains('active')) toggleONVIFView(false); } catch (_) {}
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      }
    });
    nav.appendChild(home);

    var keyByHandler = [
      [/openAddModal/, 'add'], [/gridfusion/, 'gridfusion'], [/toggleMatrixView/, 'matrix'],
      [/toggleONVIFView/, 'onvif'], [/\/alerts/, 'alerts'], [/ip-management/, 'ip'],
      [/diagnostics/, 'diagnostics'], [/openSettingsModal/, 'settings'], [/openAboutModal/, 'about']
    ];
    $$(':scope > *', actions).forEach(function (child) {
      var btn = child.matches('.dropdown') ? $(':scope > .btn', child) : child;
      var oc = (btn && btn.getAttribute('onclick')) || '';
      var key = '';
      keyByHandler.forEach(function (m) { if (!key && m[0].test(oc)) key = m[1]; });
      if (child.matches('.dropdown')) key = $('#dynamic-nav-buttons', child) ? 'addons' : 'server';
      if (key === 'add') { addBtn = child; return; }
      if (btn) { wrapLabel(btn); btn.setAttribute('data-rf', key); }
      if (key === 'about') bottom.appendChild(child); else nav.appendChild(child);
    });
    // "Live View" is a clearer name for the matrix in a camera app; keep the original as tooltip.
    var mx = $('[data-rf="matrix"] .rf-label', nav);
    if (mx) { mx.textContent = 'Live View'; mx.parentNode.title = 'Matrix View'; }

    var themeBox = $('.theme-select-container', header);
    var logout = $('#logoutBtn', header);
    if (themeBox) { themeBox.title = 'Light / dark'; bottom.insertBefore(themeBox, bottom.firstChild); }
    if (logout) { wrapLabel(logout); bottom.appendChild(logout); }

    // Top bar
    var top = el('header', { id: 'rf-topbar' });
    var titleWrap = el('div', { class: 'rf-top-title' });
    var titleArea = $('.header-title-area', header);
    if (titleArea) titleWrap.appendChild(titleArea);
    var count = el('span', { class: 'rf-count', id: 'rf-count' });
    top.appendChild(titleWrap);

    var tools = el('div', { class: 'rf-top-tools' });
    var toggles = $('.control-toggles', header);
    var grid = $('#camera-list.camera-grid');
    if (grid) {
      // Page heading row above the camera grid: title + count, view toggles on the right.
      var ph = el('div', { class: 'rf-pagehead' });
      var phl = el('div', { class: 'rf-pagehead-l' }, '<h2>Cameras</h2>');
      phl.appendChild(count);
      ph.appendChild(phl);
      // Right side: view toggles, then a compact Add Camera just right of Links.
      var phr = el('div', { class: 'rf-pagehead-r' });
      if (toggles) phr.appendChild(toggles);
      if (addBtn) { addBtn.classList.add('rf-add-btn'); phr.appendChild(addBtn); addBtn = null; }
      ph.appendChild(phr);
      grid.parentNode.insertBefore(ph, grid);
    } else if (toggles) { toggles.style.display = 'none'; tools.appendChild(toggles); }
    var stats = $('.stats-container', header);
    if (stats) tools.appendChild(stats);
    if (addBtn) { addBtn.classList.add('rf-add-btn'); tools.appendChild(addBtn); }
    top.appendChild(tools);
    container.insertBefore(top, container.firstChild);

    // Make the whole toggle row clickable, not just the tiny switch.
    $$('.toggle-group', toggles || document.createElement('div')).forEach(function (g) {
      g.addEventListener('click', function (e) {
        if (e.target.closest('label, input')) return;
        var cb = $('input[type=checkbox]', g); if (cb) cb.click();
      });
    });

    // Camera count in the title
    function updateCount() {
      var cards = $$('#camera-list .camera-card');
      if (!cards.length) { count.textContent = ''; return; }
      var on = cards.filter(function (c) { return c.classList.contains('running'); }).length;
      count.innerHTML = cards.length + ' camera' + (cards.length === 1 ? '' : 's') + ' &middot; <b>' + on + '</b> online';
    }
    var list = $('#camera-list');
    if (list) { new MutationObserver(updateCount).observe(list, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] }); updateCount(); }

    // Light/dark toggle: in Refined there are only two looks, so flip directly.
    if (typeof window.toggleSimpleTheme === 'function' && typeof window.changeTheme === 'function') {
      window.toggleSimpleTheme = function () {
        var light = /theme-(ui|protect-light|solar-light|sunset)\b/.test(document.body.className);
        window.changeTheme(light ? 'protect-dark' : 'protect-light');
      };
    }

    // Server: a full page inside the frame instead of the hover popup.
    // The popup's own elements are moved (not copied), so the live stats and
    // every action button keep working exactly as before.
    var srvBtn = $('[data-rf="server"]', nav);
    var srvDrop = srvBtn && srvBtn.parentNode;
    var srvInfo = srvDrop && $('.dropdown-sysinfo', srvDrop);
    var srvActions = srvDrop && $('.dropdown-content-inner', srvDrop);
    if (srvBtn && srvInfo && srvActions) {
      var panel = el('section', { id: 'rf-server-panel', 'aria-label': 'Server' });
      panel.innerHTML =
        '<div class="rf-panel-head"><div><h2>Server</h2><p>Host status, live load and server controls</p></div></div>' +
        '<div class="rf-server-grid"><div class="rf-card rf-srv-status"><h3>Status</h3></div>' +
        '<div class="rf-card rf-srv-actions"><h3>Actions</h3></div></div>' +
        '<div class="rf-server-grid rf-server-grid2">' +
        '<div class="rf-card rf-srv-procs"><h3>Top processes by memory <span class="rf-muted" id="rf-proc-count"></span></h3>' +
        '<div class="rf-table-wrap"><table class="rf-table"><thead><tr><th>Process</th><th class="num">PID</th><th class="num">Memory</th><th class="num">% RAM</th><th class="num">CPU</th></tr></thead>' +
        '<tbody id="rf-proc-body"><tr><td colspan="5" class="rf-muted">Loading…</td></tr></tbody></table></div></div>' +
        '<div class="rf-card rf-srv-mem"><h3>Memory</h3><div class="rf-membar"><span id="rf-mem-used"></span><span id="rf-mem-cache"></span></div>' +
        '<dl class="rf-kv" id="rf-mem-kv"></dl></div></div>';
      $('.rf-srv-status', panel).appendChild(srvInfo);
      $('.rf-srv-actions', panel).appendChild(srvActions);
      var srvMenu = $('.dropdown-content', srvDrop);
      if (srvMenu) srvMenu.classList.add('rf-emptied');
      container.appendChild(panel);
      var openServer = function (on) {
        if (on) closeModalPages('server');
        H.classList.toggle('rf-server-open', on);
        if (on) {
          try { var mo = $('#matrix-overlay'); if (mo && mo.classList.contains('active')) toggleMatrixView(false); } catch (_) {}
          try { var ov = $('#onvif-overlay'); if (ov && ov.classList.contains('active')) toggleONVIFView(false); } catch (_) {}
          if (location.pathname !== '/server') history.replaceState(null, '', '/server');
        } else if (location.pathname === '/server') {
          history.replaceState(null, '', '/');
        }
        $$('[data-rf]', rail).forEach(function (n) {
          var k = n.getAttribute('data-rf');
          n.classList.toggle('rf-active', on ? k === 'server' : k === (activeFor(location.pathname) || 'cameras'));
        });
      };
      // Memory + top processes, refreshed while the page is open.
      var fmtB = function (b) {
        if (b == null) return '-';
        var u = ['B', 'KB', 'MB', 'GB', 'TB'], i = 0;
        while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
        return (i >= 3 ? b.toFixed(1) : Math.round(b)) + ' ' + u[i];
      };
      var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
      var detailTimer = null;
      var loadDetails = function () {
        fetch('/api/ui/server-details?limit=12', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
          if (!d || !d.memory) return;
          var m = d.memory, t = m.total || 1;
          var usedEl = $('#rf-mem-used'), cacheEl = $('#rf-mem-cache');
          if (usedEl) usedEl.style.width = (m.used * 100 / t).toFixed(1) + '%';
          if (cacheEl) cacheEl.style.width = Math.max(0, Math.min(100 - m.used * 100 / t, (m.cached || 0) * 100 / t)).toFixed(1) + '%';
          var kv = [['Used', fmtB(m.used) + ' (' + (m.percent != null ? m.percent : Math.round(m.used * 100 / t)) + '%)'],
            ['Available', fmtB(m.available)], ['Cache / buffers', fmtB(m.cached)], ['Total', fmtB(m.total)],
            ['Swap', m.swap_total ? fmtB(m.swap_used) + ' of ' + fmtB(m.swap_total) : 'None']];
          var kvEl = $('#rf-mem-kv');
          if (kvEl) kvEl.innerHTML = kv.map(function (r) { return '<dt>' + r[0] + '</dt><dd>' + r[1] + '</dd>'; }).join('');
          var pc = $('#rf-proc-count'); if (pc && d.process_count) pc.textContent = '· ' + d.process_count + ' running';
          var bodyEl = $('#rf-proc-body');
          if (bodyEl) bodyEl.innerHTML = (d.processes || []).map(function (p) {
            return '<tr title="' + esc(p.cmd) + '"><td><div class="rf-pname">' + esc(p.name) + '</div><div class="rf-pcmd">' + esc(p.cmd) + '</div></td>' +
              '<td class="num">' + p.pid + '</td><td class="num">' + fmtB(p.rss) + '</td><td class="num">' + (p.mem_percent != null ? p.mem_percent + '%' : '-') + '</td>' +
              '<td class="num">' + (p.cpu_percent != null ? p.cpu_percent + '%' : '-') + '</td></tr>';
          }).join('') || '<tr><td colspan="5" class="rf-muted">No process data</td></tr>';
        }).catch(function () {});
      };
      var watchDetails = function (on) {
        clearInterval(detailTimer); detailTimer = null;
        if (on) { loadDetails(); detailTimer = setInterval(function () { if (!document.hidden) loadDetails(); }, 3000); }
      };
      var openServerBase = openServer;
      openServer = function (on) { openServerBase(on); watchDetails(on); };
      window.rfOpenServerPage = openServer;
      srvBtn.addEventListener('click', function (e) { e.preventDefault(); openServer(true); });
      // Any other rail entry closes the Server page first.
      $$('[data-rf]', rail).forEach(function (n) {
        if (n.getAttribute('data-rf') !== 'server') n.addEventListener('click', function () { if (H.classList.contains('rf-server-open')) openServer(false); }, true);
      });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && H.classList.contains('rf-server-open') && !$('.modal.active')) openServer(false); });
    }

    // Settings and About: shown as pages inside the frame instead of popups.
    // The original modals and their open/close functions are kept; CSS turns
    // each modal into a page while html.rf-<key>-open is set.
    var markRail = function (key) {
      $$('[data-rf]', rail).forEach(function (n) { n.classList.toggle('rf-active', n.getAttribute('data-rf') === key); });
    };
    var modalPages = [];
    function closeModalPages(except) {
      modalPages.forEach(function (pg) { if (pg.key !== except && H.classList.contains('rf-' + pg.key + '-open')) window[pg.close](); });
    }
    // opts: { modal, opens: [[fnName, pathFn]], close, rail, title, sub }
    function modalPage(key, o) {
      var m = $('#' + o.modal);
      if (!m || typeof window[o.close] !== 'function') return;
      var origClose = window[o.close], cls = 'rf-' + key + '-open', railKey = o.rail || key, curPath = null;
      m.classList.add('rf-modal-page');
      modalPages.push({ key: key, close: o.close });
      o.opens.forEach(function (pair) {
        var openName = pair[0], pathFn = pair[1], origOpen = window[openName];
        if (typeof origOpen !== 'function') return;
        window[openName] = function () {
          closeModalPages(key);
          if (H.classList.contains('rf-server-open') && window.rfOpenServerPage) window.rfOpenServerPage(false);
          try { var mo = $('#matrix-overlay'); if (mo && mo.classList.contains('active')) toggleMatrixView(false); } catch (_) {}
          try { var ov = $('#onvif-overlay'); if (ov && ov.classList.contains('active')) toggleONVIFView(false); } catch (_) {}
          H.classList.add(cls);
          var r = origOpen.apply(this, arguments);
          curPath = pathFn.apply(null, arguments);
          if (curPath && location.pathname !== curPath) history.replaceState(null, '', curPath);
          markRail(railKey);
          m.scrollTop = 0;
          // If the page's own open function bailed out (e.g. unknown camera), undo the page state.
          var verify = function () { if (!m.classList.contains('active') && H.classList.contains(cls)) window[o.close](); };
          if (r && typeof r.then === 'function') r.then(verify, verify); else setTimeout(verify, 0);
          return r;
        };
      });
      window[o.close] = function () {
        var r = origClose.apply(this, arguments);
        H.classList.remove(cls);
        if (curPath && location.pathname === curPath) history.replaceState(null, '', '/');
        curPath = null;
        if (!H.classList.contains('rf-server-open') && !modalPages.some(function (pg) { return H.classList.contains('rf-' + pg.key + '-open'); }))
          markRail(activeFor(location.pathname) || 'cameras');
        return r;
      };
      $$('[data-rf]', rail).forEach(function (n) {
        n.addEventListener('click', function () { if (H.classList.contains(cls)) window[o.close](); }, true);
      });
      document.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape' || !H.classList.contains(cls)) return;
        if (!$$('.modal.active').some(function (x) { return x !== m; })) window[o.close]();
      });
      var hd = $('.modal-header', m), t = hd && $('.modal-title', hd);
      if (hd && !$('.rf-page-sub', hd)) {
        if (t && o.title) { t.setAttribute('data-rf-orig', t.textContent); t.textContent = o.title; }
        if (t) t.insertAdjacentHTML('afterend', '<p class="rf-page-sub">' + o.sub + '</p>');
      }
    }
    var fixed = function (p) { return function () { return p; }; };
    modalPage('settings', { modal: 'settings-modal', opens: [['openSettingsModal', fixed('/settings')]], close: 'closeSettingsModal',
      title: 'Settings', sub: 'Server, security, engine, addons, notifications and maintenance' });
    modalPage('about', { modal: 'about-modal', opens: [['openAboutModal', fixed('/about')]], close: 'closeAboutModal',
      title: 'About', sub: 'Tonys Onvif-RTSP-AI Server: versions, updates and credits' });
    modalPage('camera', { modal: 'camera-modal', rail: 'cameras', close: 'closeModal',
      opens: [['openAddModal', fixed('/add-camera')], ['openEditModal', function (id) { return id != null ? '/camera/' + encodeURIComponent(id) : null; }]],
      sub: 'Stream, audio, AI detection and network settings for this camera' });

    // Deep links from the standalone pages (e.g. /#settings)
    var hashActions = { '#settings': 'openSettingsModal', '#about': 'openAboutModal', '#add-camera': 'openAddModal', '#logs': 'openLogsModal', '#server': 'rfOpenServerPage' };
    function runHash() {
      var fn = hashActions[location.hash];
      var em = /^#edit-(.+)$/.exec(location.hash);
      if (em && typeof window.openEditModal === 'function') {
        history.replaceState(null, '', location.pathname + location.search);
        var id = decodeURIComponent(em[1]), tries = 0;
        (function waitCams() {
          var ready = document.querySelector('.camera-card[data-id="' + id + '"]');
          if (ready || ++tries > 40) { try { window.openEditModal(isNaN(+id) ? id : +id); } catch (_) {} return; }
          setTimeout(waitCams, 150);
        })();
        return;
      }
      if (fn === 'rfOpenServerPage' && window.rfOpenServerPage) { window.rfOpenServerPage(true); return; }
      if (fn && typeof window[fn] === 'function') {
        history.replaceState(null, '', location.pathname + location.search);
        setTimeout(function () { try { window[fn](); } catch (_) {} }, 50);
      }
    }
    if (document.readyState === 'complete') runHash(); else window.addEventListener('load', runHash);
    window.addEventListener('hashchange', runHash);
  } else {
    /* ---------------- Standalone pages ---------------- */
    H.classList.add('rf-standalone');
    // Some standalone pages (e.g. AI Alerts) never apply the saved theme, so
    // they always looked dark. Pick it up from the server settings.
    if (!/\btheme-/.test(document.body.className)) {
      try {
        var cachedTheme = localStorage.getItem('rf-theme');
        if (cachedTheme) document.body.classList.add('theme-' + cachedTheme);
      } catch (_) {}
      fetch('/api/settings', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (st) {
        if (!st || !st.theme) return;
        document.body.className = document.body.className.replace(/\btheme-[\w-]+/g, '').trim();
        document.body.classList.add('theme-' + st.theme);
        try { localStorage.setItem('rf-theme', st.theme); } catch (_) {}
      }).catch(function () {});
    }
    var items = [
      ['/', 'fa-solid fa-video', 'Cameras', 'cameras'],
      ['/gridfusion', 'fa-solid fa-grip', 'GridFusion', 'gridfusion'],
      ['/matrix', 'fa-solid fa-table-cells', 'Live View', 'matrix'],
      ['/onvif', 'fa-solid fa-brain', 'AI/ONVIF', 'onvif'],
      ['/alerts', 'fas fa-images', 'AI Alerts', 'alerts'],
      ['/ip-management', 'fa-solid fa-network-wired', 'IP Management', 'ip'],
      ['/diagnostics', 'fa-solid fa-gauge', 'Diagnostics', 'diagnostics']
    ];
    items.forEach(function (it) { nav.appendChild(railItem(it[0], it[1], it[2], { 'data-rf': it[3] })); });

    // Addons flyout, filled from the same API the dashboard uses.
    var dd = el('div', { class: 'dropdown' });
    var ddBtn = el('a', { class: 'rf-item', href: '/#settings', 'data-rf': 'addons' }, '<i class="fa-solid fa-puzzle-piece"></i><span class="rf-label">Addons</span>');
    var ddMenu = el('div', { class: 'dropdown-content', style: 'min-width: 200px; flex-direction: column; gap: 2px;' });
    dd.appendChild(ddBtn); dd.appendChild(ddMenu); nav.appendChild(dd);
    fetch('/api/modules/nav-items', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : []; }).then(function (navItems) {
      (navItems || []).forEach(function (item) {
        if (item.requires_active && item.module_status !== 'active' && item.module_status !== 'trial') return;
        if (!item.href) return;
        var b = el('button', { type: 'button' }, '<i class="' + (item.icon || 'fas fa-puzzle-piece') + '" style="width:20px;text-align:center;margin-right:8px"></i>');
        b.appendChild(document.createTextNode(item.label || 'Addon'));
        b.addEventListener('click', function () { location.href = item.href; });
        ddMenu.appendChild(b);
      });
      if (!ddMenu.children.length) ddMenu.innerHTML = '<div style="padding:8px 10px;font-size:12px;color:var(--rf-text-3)">No active addons</div>';
    }).catch(function () {});

    nav.appendChild(railItem('/settings', 'fa-solid fa-gear', 'Settings', { 'data-rf': 'settings' }));
    nav.appendChild(railItem('/server', 'fa-solid fa-server', 'Server', { 'data-rf': 'server' }));
    // Bottom of the rail matches the dashboard: theme toggle, About, Logout.
    var isLight = function () { return /theme-(ui|protect-light|solar-light|sunset|light)\b/.test(document.body.className); };
    var themeBox = el('div', { class: 'theme-select-container', title: 'Light / dark' },
      '<div role="button" tabindex="0" aria-label="Light / dark"><i id="themeToggleIcon" class="fas fa-moon"></i></div>');
    var themeIcon = $('i', themeBox);
    var syncIcon = function () { themeIcon.className = isLight() ? 'fas fa-moon' : 'fas fa-sun'; };
    new MutationObserver(syncIcon).observe(document.body, { attributes: true, attributeFilter: ['class'] });
    syncIcon();
    var flipTheme = function () {
      var next = isLight() ? 'protect-dark' : 'protect-light';
      document.body.className = document.body.className.replace(/\btheme-[\w-]+/g, '').trim();
      document.body.classList.add('theme-' + next);
      try { localStorage.setItem('rf-theme', next); } catch (_) {}
      // Save it the same way the dashboard does (full settings object).
      fetch('/api/settings', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (st) {
        if (!st) return;
        st.theme = next;
        return fetch('/api/settings', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(st) });
      }).catch(function () {});
    };
    themeBox.firstChild.addEventListener('click', flipTheme);
    themeBox.firstChild.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); flipTheme(); } });
    bottom.appendChild(themeBox);
    bottom.appendChild(railItem('/about', 'fa-solid fa-circle-info', 'About', { 'data-rf': 'about' }));
    var logoutItem = railItem('/logout', 'fas fa-sign-out-alt', 'Logout', { id: 'rf-logout' });
    logoutItem.style.display = 'none';
    bottom.appendChild(logoutItem);
    fetch('/api/settings', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (st) {
      if (st && st.authEnabled) logoutItem.style.display = '';
    }).catch(function () {});

    // Same top bar as the dashboard (title, GitHub, stars, version, live CPU/MEM/NET)
    // so the header is visible on every page (Tony, 2026-11-03).
    var verMeta = $('meta[name="rf-app-version"]');
    var sTop = el('header', { id: 'rf-topbar' });
    var sTitle = el('div', { class: 'rf-top-title' });
    sTitle.innerHTML = '<div class="header-title-area"><h1><span>Tonys Onvif-RTSP-AI Server</span>' +
      '<a href="https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server" target="_blank" rel="noopener" title="View on GitHub" style="color: inherit; text-decoration: none; display: inline-flex; align-items: center;"><i class="fa-brands fa-github"></i></a>' +
      (verMeta ? '<span class="version-badge"></span>' : '') + '</h1></div>';
    if (verMeta) $('.version-badge', sTitle).textContent = 'v' + verMeta.getAttribute('content');
    var sTools = el('div', { class: 'rf-top-tools' });
    var sStats = el('div', { class: 'stats-container' }, '<span class="stats-badge" id="rf-top-stats"><i class="fa-solid fa-microchip"></i> CPU: ... &nbsp;&nbsp;•&nbsp;&nbsp; <i class="fa-solid fa-memory"></i> MEM: ...</span>');
    sTools.appendChild(sStats);
    sTop.appendChild(sTitle); sTop.appendChild(sTools);
    document.body.insertBefore(sTop, document.body.firstChild);
    var statsEl = $('#rf-top-stats', sTop);
    var pollStats = function () {
      if (document.hidden) return;
      Promise.all([
        fetch('/api/stats', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; }),
        fetch('/api/analytics', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; })
      ]).then(function (res) {
        var st = res[0], an = res[1] || {};
        if (!st || st.cpu_percent === undefined) return;
        var total = 0;
        Object.keys(an).forEach(function (k) { total += (an[k] && an[k].bitrate) || 0; });
        var net = parseFloat((total / 1000).toFixed(1));
        statsEl.innerHTML = '<i class="fa-solid fa-microchip"></i> CPU: ' + st.cpu_percent + '% &nbsp;&nbsp;•&nbsp;&nbsp; ' +
          '<i class="fa-solid fa-memory"></i> MEM: ' + st.memory_mb + 'MB &nbsp;&nbsp;•&nbsp;&nbsp; ' +
          '<i class="fa-solid fa-network-wired"></i> NET: ' + net + ' Mbps';
      }).catch(function () {});
    };
    pollStats(); setInterval(pollStats, 3000);
  }

  // Keep the rail highlight in step with the AI/ONVIF log panel
  var onvifOv = document.getElementById('onvif-overlay');
  if (onvifOv && H.classList.contains('rf-shell')) {
    var syncOnvif = function () {
      var open = onvifOv.classList.contains('active');
      var cur = open ? 'onvif' : activeFor(location.pathname.replace(/\/+$/, '') || '/');
      if (cur === 'onvif' && !open) cur = 'cameras';
      $$('[data-rf]', rail).forEach(function (n) { n.classList.toggle('rf-active', n.getAttribute('data-rf') === cur); });
    };
    new MutationObserver(syncOnvif).observe(onvifOv, { attributes: true, attributeFilter: ['class'] });
    setTimeout(syncOnvif, 0);
  }

  // Highlight where we are
  $$('[data-rf]', rail).forEach(function (n) { if (current && n.getAttribute('data-rf') === current) n.classList.add('rf-active'); });

  document.body.insertBefore(rail, document.body.firstChild);
  H.classList.add('rf-ready');
})();
/* Dashboard title: bold "Tony's" + lighter product name (Tony's pick, 2026-11-03) */
(function () {
  'use strict';
  if (!document.documentElement.classList.contains('ui-refined')) return;
  function apply() {
    var h = document.querySelector('.header-title-area h1');
    var s = h && h.querySelector(':scope > span:not(.version-badge)');
    if (!s || s.getAttribute('data-rf-title')) return;
    if (!/onvif/i.test(s.textContent)) return;
    s.setAttribute('data-rf-title', '1');
    s.innerHTML = '<b class="rf-title-name">Tony’s</b> <span class="rf-title-product">ONVIF · RTSP · AI Server</span>';
    // GitHub stars badge next to the GitHub icon (count cached for an hour)
    var gh = h.querySelector('a[href*="github.com"]');
    if (gh && !h.querySelector('.rf-gh-stars')) {
      gh.classList.add('rf-gh-link');
      var repo = (gh.getAttribute('href').match(/github\.com\/([^\/]+\/[^\/?#]+)/) || [])[1];
      var badge = document.createElement('a');
      badge.className = 'rf-gh-stars';
      badge.href = 'https://github.com/' + repo;
      badge.target = '_blank'; badge.rel = 'noopener';
      badge.title = 'Like it? Star this project on GitHub';
      badge.innerHTML = '<i class="fa-regular fa-star"></i><b>\u2026</b>';
      gh.insertAdjacentElement('afterend', badge);
      var show = function (n) { var b = badge.querySelector('b'); if (b) b.textContent = n >= 1000 ? (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k' : String(n); };
      var key = 'rf-gh-stars:' + repo, cached = null;
      try { cached = JSON.parse(localStorage.getItem(key) || 'null'); } catch (_) {}
      if (cached && typeof cached.n === 'number') show(cached.n);
      if (repo && (!cached || Date.now() - cached.t > 3600000)) {
        fetch('https://api.github.com/repos/' + repo, { headers: { Accept: 'application/vnd.github+json' } })
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (d) {
            var b = badge.querySelector('b');
            if (!d || typeof d.stargazers_count !== 'number') { if (!cached && b) b.remove(); return; }
            show(d.stargazers_count);
            try { localStorage.setItem(key, JSON.stringify({ n: d.stargazers_count, t: Date.now() })); } catch (_) {}
          }).catch(function () { var b = badge.querySelector('b'); if (b && !cached) b.remove(); });
      }
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply); else apply();
})();
/* 2.1.0: small power button at the far right of the top bar with quick server actions (Tony, 2026-11-04).
   Uses the dashboard's own handlers (same confirmations); on standalone pages it calls the same APIs. */
(function () {
  'use strict';
  var H = document.documentElement;
  if (!H.classList.contains('ui-refined') || window.__rfPowerDone) return;
  window.__rfPowerDone = true;

  function toast(msg) {
    if (typeof window.showToast === 'function') { try { window.showToast(msg, 'info'); return; } catch (_) {} }
    var t = document.createElement('div');
    t.className = 'rf-power-toast'; t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 2600);
  }
  function post(url) { return fetch(url, { method: 'POST', credentials: 'same-origin' }); }
  function waitAndReload(msg) {
    var o = document.createElement('div');
    o.className = 'rf-power-wait';
    o.innerHTML = '<div><i class="fa-solid fa-rotate fa-spin"></i><p></p></div>';
    o.querySelector('p').textContent = msg;
    document.body.appendChild(o);
    var start = Date.now();
    setTimeout(function poll() {
      fetch('/api/health', { cache: 'no-store', credentials: 'same-origin' })
        .then(function (r) { if (r.ok) location.reload(); else throw 0; })
        .catch(function () { if (Date.now() - start < 180000) setTimeout(poll, 2000); });
    }, 3000);
  }

  var fallback = {
    startAll: function () { post('/api/cameras/start-all').then(function () { toast('Starting all cameras…'); }).catch(function () { alert('Error starting all cameras'); }); },
    stopAll: function () { post('/api/cameras/stop-all').then(function () { toast('Stopping all cameras…'); }).catch(function () { alert('Error stopping all cameras'); }); },
    restartServer: function () {
      if (!confirm('Are you sure you want to restart the server application?')) return;
      try { localStorage.removeItem('restartRequired'); } catch (_) {}
      post('/api/server/restart').then(function (r) { if (r.ok) waitAndReload('Server is restarting…'); else alert('Failed to restart server'); })
        .catch(function () { alert('Error restarting server'); });
    },
    stopServer: function () {
      if (!confirm('Are you sure you want to stop the server? This will shut down all camera streams and the web interface.')) return;
      post('/api/server/stop').then(function (r) {
        if (!r.ok) { alert('Failed to stop server'); return; }
        setTimeout(function () {
          document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;flex-direction:column;background:#1a202c;color:#fff;text-align:center;padding:20px;">' +
            '<i class="fas fa-power-off" style="font-size:64px;color:#f56565;margin-bottom:20px;"></i><h1>Server Stopped</h1>' +
            '<p style="font-size:18px;color:#a0aec0;">The ONVIF server has been shut down successfully.</p>' +
            '<p style="color:#a0aec0;margin-top:30px;font-size:14px;">You can safely close this browser tab.</p></div>';
        }, 1500);
      }).catch(function () { alert('Error stopping server'); });
    },
    openLogsModal: function () { location.href = '/logs'; },
    rebootServer: function () {
      if (!confirm('This will reboot the entire server. The system will be unavailable for a few minutes. Continue?')) return;
      post('/api/server/reboot').then(function (r) {
        if (r.ok) alert('Server is rebooting... The system will be back online in a few minutes.');
        else alert('Failed to reboot server. This feature only works on Linux.');
      }).catch(function () { alert('Error rebooting server'); });
    }
  };
  function run(name) {
    var fn = window[name];
    if (name === 'openLogsModal') { location.href = '/logs'; return; }
    if (typeof fn === 'function') fn();
    else fallback[name]();
  }

  var items = [
    ['Cameras'],
    ['startAll', 'fa-solid fa-play', 'Start All Cameras'],
    ['stopAll', 'fa-solid fa-stop', 'Stop All Cameras'],
    ['Server'],
    ['restartServer', 'fa-solid fa-rotate', 'Restart Server'],
    ['stopServer', 'fa-solid fa-circle-stop', 'Stop Server'],
    ['System'],
    ['openLogsModal', 'fa-solid fa-rectangle-list', 'System Logs'],
    ['rebootServer', 'fa-solid fa-power-off', 'Reboot Host', 'rf-pm-danger']
  ];

  function build() {
    var bar = document.getElementById('rf-topbar');
    var tools = bar && bar.querySelector('.rf-top-tools');
    if (!tools || tools.querySelector('.rf-power')) return !!tools;
    var wrap = document.createElement('div');
    wrap.className = 'rf-power';
    var btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'rf-power-btn'; btn.setAttribute('aria-label', 'Power & server actions');
    btn.setAttribute('aria-haspopup', 'menu'); btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = '<i class="fa-solid fa-power-off"></i>';
    var menu = document.createElement('div');
    menu.className = 'rf-power-menu'; menu.setAttribute('role', 'menu');
    items.forEach(function (it) {
      if (it.length === 1) { var h = document.createElement('div'); h.className = 'rf-pm-head'; h.textContent = it[0]; menu.appendChild(h); return; }
      var b = document.createElement('button');
      b.type = 'button'; b.setAttribute('role', 'menuitem');
      if (it[3]) b.className = it[3];
      b.innerHTML = '<i class="' + it[1] + '"></i><span></span>';
      b.querySelector('span').textContent = it[2];
      b.addEventListener('click', function () { close(); run(it[0]); });
      menu.appendChild(b);
    });
    function close() { wrap.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); }
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var on = !wrap.classList.contains('open');
      wrap.classList.toggle('open', on); btn.setAttribute('aria-expanded', on ? 'true' : 'false');
    });
    document.addEventListener('click', function (e) { if (!wrap.contains(e.target)) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    wrap.appendChild(btn); wrap.appendChild(menu);
    tools.appendChild(wrap);
    return true;
  }

  function init() {
    if (!build()) { var n = 0, iv = setInterval(function () { if (build() || ++n > 40) clearInterval(iv); }, 250); }
    // System Logs has its own page now; send old ?rf-logs=1 links there.
    if (/[?&]rf-logs=1\b/.test(location.search)) { location.replace('/logs'); return; }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
