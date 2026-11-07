"""
Addon page renderer.

Renders /addon/<module_id> inside the main dashboard chrome. The page is
generic: it shows licence state, missing Python packages, live status and
activity, the module's global settings, its per-camera settings and any
extra dashboard HTML the module provides. Saving goes through the generic
addon API (/api/addons/<id>/config and /api/addons/<id>/cameras/<cam>/config)
so modules never have to touch the core camera or settings endpoints.
"""

import html
import json


def _json_for_script(data):
    """JSON that is safe to embed inside a <script> element."""
    return (json.dumps(data)
            .replace('<', '\\u003c')
            .replace('>', '\\u003e')
            .replace('&', '\\u0026')
            .replace(' ', '\\u2028')
            .replace(' ', '\\u2029'))


_PAGE_CSS = """
.addon-page { max-width: 1100px; margin: 0 auto; padding: 20px; text-align: left; }
.addon-page .ad-card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; margin-bottom: 18px; overflow: hidden; }
.addon-page .ad-card-h { padding: 12px 16px; font-weight: 700; color: var(--text-title); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; gap: 8px; justify-content: space-between; }
.addon-page .ad-card-b { padding: 16px; color: var(--text-body); }
.addon-page .ad-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
.addon-page .ad-icon { width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
.addon-page h1 { margin: 0; font-size: 22px; color: var(--text-title); }
.addon-page .ad-muted { color: var(--text-muted); font-size: 13px; }
.addon-page .ad-badge { font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 700; letter-spacing: .5px; color: #fff; text-transform: uppercase; }
.addon-page label.ad-label { display: block; font-size: 12.5px; font-weight: 600; color: var(--text-title); margin-bottom: 5px; }
.addon-page input[type=text], .addon-page input[type=number], .addon-page input[type=password], .addon-page input[type=time],
.addon-page input[type=url], .addon-page input[type=email], .addon-page select, .addon-page textarea {
  width: 100%; box-sizing: border-box; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--input-border, var(--border-color));
  background: var(--input-bg); color: var(--input-text, var(--text-body)); font-size: 13px; }
.addon-page textarea { min-height: 70px; font-family: inherit; }
.addon-page .ad-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; }
.addon-page .ad-field { margin-bottom: 12px; }
.addon-page .ad-hint { font-size: 11.5px; color: var(--text-muted); margin-top: 4px; }
.addon-page .ad-check { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13.5px; color: var(--text-title); font-weight: 600; }
.addon-page .ad-check input { width: auto; }
.addon-page .ad-chips { display: flex; flex-wrap: wrap; gap: 8px 16px; }
.addon-page .ad-chips label { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }
.addon-page .ad-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.addon-page .ad-stat { background: rgba(127,127,127,.06); border: 1px solid var(--border-color); border-radius: 10px; padding: 10px 12px; }
.addon-page .ad-stat .k { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .4px; }
.addon-page .ad-stat .v { font-size: 15px; font-weight: 700; color: var(--text-title); margin-top: 3px; word-break: break-word; }
.addon-page .ad-log { max-height: 220px; overflow: auto; font-family: ui-monospace, Consolas, monospace; font-size: 12px; background: rgba(0,0,0,.18); border-radius: 8px; padding: 8px 10px; white-space: pre-wrap; }
.addon-page .ad-log .warning { color: #d69e2e; } .addon-page .ad-log .error { color: #e53e3e; }
.addon-page table.ad-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.addon-page table.ad-table th, .addon-page table.ad-table td { padding: 7px 8px; border-bottom: 1px solid var(--border-color); text-align: left; vertical-align: middle; }
.addon-page table.ad-table th { color: var(--text-muted); font-size: 11.5px; text-transform: uppercase; letter-spacing: .4px; }
.addon-page .ad-tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border-color); margin: 14px 0; flex-wrap: wrap; }
.addon-page .ad-tab { background: none; border: none; padding: 8px 14px; cursor: pointer; color: var(--text-muted); font-weight: 600; border-bottom: 2px solid transparent; }
.addon-page .ad-tab.active { color: var(--text-title); border-bottom-color: var(--btn-primary); }
.addon-page .ad-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.addon-page .btn-sm { padding: 5px 10px; font-size: 12px; }
.addon-page .ad-empty { text-align: center; padding: 18px; color: var(--text-muted); font-size: 13px; }
"""


_PAGE_JS = r"""
(function () {
  const ADDON = JSON.parse(document.getElementById('addon-page-data').textContent);
  window.ADDON = ADDON;

  window.addonApi = async function (path, method = 'GET', body = undefined) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
      if (body instanceof FormData) { opts.body = body; }
      else { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
    }
    const res = await fetch(`/api/addons/${ADDON.id}${path}`, opts);
    let data = null;
    try { data = await res.json(); } catch (e) { data = {}; }
    if (!res.ok) {
      const msg = (data && (data.error || data.message)) || `Request failed (${res.status})`;
      throw new Error(msg);
    }
    return data;
  };

  window.addonToast = function (msg, type = 'success') {
    if (typeof showToast === 'function') { showToast(msg, type); } else { alert(msg); }
  };

  window.addonEsc = function (s) {
    return String(s === undefined || s === null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  };

  window.addonFmtTime = function (ts) {
    if (!ts) return '—';
    const d = new Date(ts * 1000);
    return d.toLocaleString();
  };

  window.addonFmtBytes = function (b) {
    b = Number(b || 0);
    const u = ['B', 'KB', 'MB', 'GB', 'TB']; let i = 0;
    while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
    return (i ? b.toFixed(1) : b) + ' ' + u[i];
  };

  // ---- generic data-field binding -------------------------------------
  function getPath(obj, path) {
    return path.split('.').reduce((o, k) => (o && typeof o === 'object') ? o[k] : undefined, obj);
  }
  function setPath(obj, path, value) {
    const keys = path.split('.'); let o = obj;
    keys.slice(0, -1).forEach(k => { if (typeof o[k] !== 'object' || o[k] === null) o[k] = {}; o = o[k]; });
    o[keys[keys.length - 1]] = value;
  }

  window.addonPopulate = function (root, data) {
    root.querySelectorAll('[data-field]').forEach(el => {
      const key = el.dataset.field; const type = el.dataset.type || '';
      let val = getPath(data, key);
      if (el.type === 'checkbox' && el.dataset.value !== undefined) {
        const arr = Array.isArray(val) ? val : [];
        el.checked = arr.map(String).includes(el.dataset.value);
        return;
      }
      if (val === undefined) return;
      if (el.type === 'checkbox') { el.checked = !!val; }
      else if (el.tagName === 'SELECT' && el.multiple) {
        const arr = Array.isArray(val) ? val.map(String) : [];
        Array.from(el.options).forEach(o => o.selected = arr.includes(o.value));
      }
      else if (type === 'json') { el.value = JSON.stringify(val, null, 2); }
      else if (type === 'list') { el.value = Array.isArray(val) ? val.join(', ') : (val || ''); }
      else if (type === 'lines') { el.value = Array.isArray(val) ? val.join('\n') : (val || ''); }
      else { el.value = val === null ? '' : val; }
    });
    root.querySelectorAll('[data-show-if]').forEach(el => addonApplyShowIf(root, el));
  };

  window.addonCollect = function (root) {
    const out = {};
    const multiChecks = {};
    root.querySelectorAll('[data-field]').forEach(el => {
      const key = el.dataset.field; const type = el.dataset.type || '';
      if (el.type === 'checkbox' && el.dataset.value !== undefined) {
        multiChecks[key] = multiChecks[key] || [];
        if (el.checked) multiChecks[key].push(el.dataset.value);
        return;
      }
      let val;
      if (el.type === 'checkbox') val = el.checked;
      else if (el.tagName === 'SELECT' && el.multiple) val = Array.from(el.selectedOptions).map(o => o.value);
      else if (el.type === 'number' || type === 'number') val = el.value === '' ? null : Number(el.value);
      else if (type === 'json') {
        try { val = el.value.trim() ? JSON.parse(el.value) : null; }
        catch (e) { throw new Error(`Invalid JSON in "${key}"`); }
      }
      else if (type === 'list') val = el.value.split(',').map(s => s.trim()).filter(Boolean);
      else if (type === 'lines') val = el.value.split('\n').map(s => s.trim()).filter(Boolean);
      else val = el.value;
      setPath(out, key, val);
    });
    Object.entries(multiChecks).forEach(([k, v]) => setPath(out, k, v));
    return out;
  };

  window.addonApplyShowIf = function (root, el) {
    // data-show-if="field=value1|value2" or "field" (checkbox truthy)
    const spec = el.dataset.showIf; const [field, values] = spec.split('=');
    const src = root.querySelector(`[data-field="${field}"]`);
    if (!src) return;
    let current = src.type === 'checkbox' ? (src.checked ? 'true' : 'false') : src.value;
    const ok = values === undefined ? (src.type === 'checkbox' ? current === 'true' : !!current) : values.split('|').includes(current);
    el.style.display = ok ? '' : 'none';
  };
  document.addEventListener('change', (e) => {
    const root = e.target.closest('.addon-page');
    if (root && e.target.dataset && e.target.dataset.field) {
      root.querySelectorAll('[data-show-if]').forEach(el => addonApplyShowIf(root, el));
    }
  });

  // ---- license gate ----------------------------------------------------
  window.addonStartTrial = async function () {
    if (!confirm(`Start the free ${ADDON.trial_days}-day trial of ${ADDON.name}?`)) return;
    const r = await fetch(`/api/modules/${ADDON.id}/activate-trial`, { method: 'POST' });
    const d = await r.json(); alert(d.message); if (d.success) location.reload();
  };
  window.addonEnterLicense = async function () {
    const key = prompt('Enter the license key from your purchase email (or an offline activation token):'); if (!key) return;
    const r = await fetch(`/api/modules/${ADDON.id}/activate`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ license_key: key })
    });
    const d = await r.json(); alert(d.message); if (d.success) location.reload();
  };

  if (!ADDON.active) return;

  // ---- requirements ----------------------------------------------------
  async function loadRequirements() {
    const box = document.getElementById('addonReqs'); if (!box) return;
    try {
      const data = await addonApi('/requirements');
      const missing = data.requirements.filter(r => !r.installed);
      const job = data.install;
      if (!missing.length && !(job && job.running)) { box.style.display = 'none'; return; }
      box.style.display = '';
      const list = data.requirements.map(r => `<li><code>${addonEsc(r.pip)}</code> — ${r.installed ? '<span style="color:#38a169">installed</span>' : '<span style="color:#e53e3e">missing</span>'}${r.optional ? ' <span class="ad-muted">(optional)</span>' : ''}${r.purpose ? ' <span class="ad-muted">· ' + addonEsc(r.purpose) + '</span>' : ''}</li>`).join('');
      document.getElementById('addonReqList').innerHTML = `<ul style="margin:0 0 10px 18px; padding:0;">${list}</ul>`;
      const logEl = document.getElementById('addonReqLog');
      if (job && job.log) { logEl.style.display = ''; logEl.textContent = job.log; logEl.scrollTop = logEl.scrollHeight; }
      const btn = document.getElementById('addonReqBtn');
      btn.disabled = !!(job && job.running);
      btn.innerHTML = job && job.running ? '<i class="fas fa-spinner fa-spin"></i> Installing…' : '<i class="fas fa-download"></i> Install missing packages';
      if (job && job.running) setTimeout(loadRequirements, 2000);
    } catch (e) { console.error(e); }
  }
  window.addonInstallReqs = async function () {
    try { await addonApi('/requirements/install', 'POST', {}); } catch (e) { addonToast(e.message, 'error'); }
    loadRequirements();
  };

  // ---- status / activity -----------------------------------------------
  async function loadStatus() {
    const grid = document.getElementById('addonStatusGrid'); if (!grid) return;
    try {
      const data = await addonApi('/status');
      const entries = Object.entries(data.status || {});
      grid.innerHTML = entries.length ? entries.map(([k, v]) =>
        `<div class="ad-stat"><div class="k">${addonEsc(k)}</div><div class="v">${addonEsc(v)}</div></div>`).join('')
        : '<div class="ad-muted">No status information.</div>';
      const log = document.getElementById('addonActivity');
      const acts = data.activity || [];
      log.innerHTML = acts.length ? acts.map(a => `<div class="${a.level}">[${new Date(a.ts * 1000).toLocaleTimeString()}] ${addonEsc(a.message)}</div>`).join('')
        : '<span class="ad-muted">No activity yet.</span>';
      document.getElementById('addonRunning').innerHTML = data.running
        ? '<span class="ad-badge" style="background:#38a169">Running</span>'
        : '<span class="ad-badge" style="background:#718096">Stopped</span>';
    } catch (e) { grid.innerHTML = `<div class="ad-muted">${addonEsc(e.message)}</div>`; }
  }

  // ---- global settings -------------------------------------------------
  async function loadGlobal() {
    const form = document.getElementById('addonGlobalForm'); if (!form) return;
    try { addonPopulate(form, await addonApi('/config')); } catch (e) { addonToast(e.message, 'error'); }
    form.dispatchEvent(new CustomEvent('addon:populated'));
  }
  window.addonSaveGlobal = async function (ev) {
    if (ev) ev.preventDefault();
    const form = document.getElementById('addonGlobalForm');
    try {
      const payload = addonCollect(form);
      const res = await addonApi('/config', 'POST', payload);
      addonPopulate(form, res.config || {});
      addonToast('Settings saved');
      loadStatus();
    } catch (e) { addonToast(e.message, 'error'); }
  };

  // ---- per-camera settings ---------------------------------------------
  function camTabsRoot() { return document.getElementById('addonCamForm'); }
  window.addonSwitchCamTab = function (tabId) {
    document.querySelectorAll('.addon-cam-tab').forEach(t => t.style.display = (t.dataset.tab === tabId) ? '' : 'none');
    document.querySelectorAll('.ad-tab[data-tab]').forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
  };
  window.addonSelectCamera = async function (camId) {
    const area = document.getElementById('addonCamArea');
    if (!camId) { area.style.display = 'none'; return; }
    const cam = ADDON.cameras.find(c => String(c.id) === String(camId));
    let cfg = {};
    try { cfg = await addonApi(`/cameras/${camId}/config`); } catch (e) { addonToast(e.message, 'error'); return; }
    window.editingCameraId = parseInt(camId, 10);
    const merged = Object.assign({}, cam || {}, cfg);
    ADDON.tabs.forEach(tab => {
      const el = document.querySelector(`.addon-cam-tab[data-tab="${tab.id}"]`);
      if (tab.on_reset && typeof window[tab.on_reset] === 'function') window[tab.on_reset]();
      if (tab.on_populate && typeof window[tab.on_populate] === 'function') window[tab.on_populate](merged, cam);
      else if (el) addonPopulate(el, merged);
    });
    area.style.display = '';
    document.dispatchEvent(new CustomEvent('addon:camera-selected', { detail: { camera: cam, config: cfg } }));
  };
  window.addonSaveCamera = async function (ev) {
    if (ev) ev.preventDefault();
    const camId = document.getElementById('addonCameraSelect').value;
    if (!camId) return;
    const payload = {};
    try {
      ADDON.tabs.forEach(tab => {
        const el = document.querySelector(`.addon-cam-tab[data-tab="${tab.id}"]`);
        let data = null;
        if (tab.on_collect && typeof window[tab.on_collect] === 'function') data = window[tab.on_collect]();
        else if (el) data = addonCollect(el);
        if (data) Object.assign(payload, data);
      });
      const res = await addonApi(`/cameras/${camId}/config`, 'POST', payload);
      addonToast('Camera settings saved');
      document.dispatchEvent(new CustomEvent('addon:camera-saved', { detail: { cameraId: camId, config: res.config } }));
      loadStatus();
    } catch (e) { addonToast(e.message, 'error'); }
  };

  document.addEventListener('DOMContentLoaded', () => {
    loadRequirements();
    loadStatus();
    loadGlobal();
    if (ADDON.tabs.length) addonSwitchCamTab(ADDON.tabs[0].id);
    const sel = document.getElementById('addonCameraSelect');
    if (sel && ADDON.cameras.length === 1) { sel.value = ADDON.cameras[0].id; addonSelectCamera(sel.value); }
    setInterval(loadStatus, 5000);
  });
})();
"""


def _gate_html(module, module_manager):
    status = module_manager.get_module_status(module.module_id)
    enabled = module_manager._state.get(module.module_id, {}).get('enabled', True)
    try:
        from .module_manager import machine_fingerprint
        from .licensing import machine_id
        machine_code = machine_id.short_code(machine_fingerprint())
    except Exception:
        machine_code = ''
    if status in ('active', 'trial') and not enabled:
        msg = 'This addon is disabled. Enable it from Settings → Addons to use it.'
        actions = ''
    elif status == 'expired':
        msg = 'Your free trial has ended. Enter a license key to keep using this addon.'
        actions = '<button class="btn btn-primary" onclick="addonEnterLicense()"><i class="fas fa-key"></i> Enter License Key</button>'
    else:
        msg = f'This is a premium addon ({html.escape(str(module.price))}). Start a free {module.trial_days}-day trial or enter a license key to unlock it.'
        actions = (f'<button class="btn btn-primary" onclick="addonStartTrial()"><i class="fas fa-clock"></i> Start {module.trial_days}-Day Trial</button> '
                   '<button class="btn btn-grey" onclick="addonEnterLicense()"><i class="fas fa-key"></i> Enter License Key</button>')
    code_html = ''
    if machine_code and status != 'active':
        code_html = (f'<div class="ad-muted" style="margin-top:16px; font-size:12px;">'
                     f'No internet on this machine? Use offline activation with this computer code:'
                     f'<br><code style="font-size:13px; letter-spacing:1px;">{html.escape(machine_code)}</code></div>')
    return f'''
    <div class="ad-card"><div class="ad-card-b" style="text-align:center; padding: 34px 20px;">
        <i class="fas fa-lock" style="font-size: 34px; color: var(--text-muted); margin-bottom: 12px;"></i>
        <div style="font-size: 15px; color: var(--text-title); font-weight: 600; margin-bottom: 14px;">{msg}</div>
        <div class="ad-row" style="justify-content:center;">{actions}</div>
        {code_html}
    </div></div>'''


def get_addon_html(module_id, module_manager, settings, cameras, boot_id, is_linux):
    from .web_template import get_web_ui_html

    module = module_manager.modules.get(module_id)
    if not module:
        return "Module not found"

    active = module_manager.is_module_active(module_id)
    status = module_manager.get_module_status(module_id)
    trial = module_manager.get_trial_remaining(module_id)

    esc = html.escape
    color = esc(str(getattr(module, 'color', '#6366f1')))
    icon = esc(str(getattr(module, 'icon', 'fas fa-puzzle-piece')))

    if status == 'active':
        badge = '<span class="ad-badge" style="background:#38a169">Licensed</span>'
    elif status == 'trial':
        rem = f"{trial['days']}d {trial['hours']}h left" if trial else ''
        badge = f'<span class="ad-badge" style="background:#d69e2e">Trial {esc(rem)}</span>'
    elif status == 'expired':
        badge = '<span class="ad-badge" style="background:#e53e3e">Trial expired</span>'
    else:
        badge = '<span class="ad-badge" style="background:#2b6cb0">Addon</span>'

    body = ''
    tabs = []
    if not active:
        body = _gate_html(module, module_manager)
    else:
        # ---- requirements -------------------------------------------------
        body += '''
        <div class="ad-card" id="addonReqs" style="display:none;">
            <div class="ad-card-h"><span><i class="fas fa-box-open"></i> Required Python packages</span></div>
            <div class="ad-card-b">
                <div id="addonReqList"></div>
                <button id="addonReqBtn" class="btn btn-primary btn-sm" onclick="addonInstallReqs()"><i class="fas fa-download"></i> Install missing packages</button>
                <div id="addonReqLog" class="ad-log" style="display:none; margin-top:10px;"></div>
            </div>
        </div>'''

        # ---- status ---------------------------------------------------------
        body += '''
        <div class="ad-card">
            <div class="ad-card-h"><span><i class="fas fa-heart-pulse"></i> Status</span><span id="addonRunning"></span></div>
            <div class="ad-card-b">
                <div class="ad-stats" id="addonStatusGrid"><div class="ad-muted">Loading…</div></div>
                <details style="margin-top: 12px;"><summary class="ad-muted" style="cursor:pointer;">Activity log</summary>
                    <div class="ad-log" id="addonActivity" style="margin-top:8px;"></div>
                </details>
            </div>
        </div>'''

        # ---- global settings ------------------------------------------------
        try:
            sections = module.register_settings_sections() or []
        except Exception as e:
            sections = [{'label': 'Settings', 'html': f'<div class="ad-muted">Error: {esc(str(e))}</div>'}]
        if sections:
            inner = ''
            extra = ''
            for sec in sections:
                title = sec.get('label') or sec.get('title') or 'Settings'
                sec_icon = esc(sec.get('icon', 'fas fa-cogs'))
                inner += f'''
                <div class="addon-settings-section" style="margin-bottom: 16px;">
                    <div style="font-weight:700; color: var(--text-title); margin-bottom: 10px;"><i class="{sec_icon}"></i> {esc(title)}</div>
                    {sec.get('html', '')}
                </div>'''
                if sec.get('css'):
                    extra += f"<style>{sec['css']}</style>"
                if sec.get('js'):
                    extra += f"<script>{sec['js']}</script>"
            body += f'''
            <div class="ad-card">
                <div class="ad-card-h"><span><i class="fas fa-sliders"></i> Settings</span></div>
                <div class="ad-card-b">
                    <form id="addonGlobalForm" onsubmit="addonSaveGlobal(event)" autocomplete="off">
                        {inner}
                        <button type="submit" class="btn btn-success"><i class="fas fa-save"></i> Save Settings</button>
                    </form>
                </div>
            </div>{extra}'''

        # ---- camera settings ------------------------------------------------
        try:
            tabs = module.register_camera_tabs() or []
        except Exception as e:
            tabs = []
            body += f'<div class="ad-card"><div class="ad-card-b">Camera settings error: {esc(str(e))}</div></div>'
        if tabs:
            options = '<option value="">— Select a camera —</option>'
            for cam in cameras:
                state = '' if cam.get('status') == 'running' else ' (stopped)'
                options += f'<option value="{esc(str(cam["id"]))}">{esc(str(cam.get("name", "Camera")))}{state}</option>'
            tab_buttons = ''
            tab_bodies = ''
            extra = ''
            for tab in tabs:
                tid = esc(str(tab.get('id')))
                if len(tabs) > 1:
                    tab_buttons += f'<button type="button" class="ad-tab" data-tab="{tid}" onclick="addonSwitchCamTab(\'{tid}\')"><i class="{esc(tab.get("icon", ""))}"></i> {esc(tab.get("label", ""))}</button>'
                tab_bodies += f'<div class="addon-cam-tab" data-tab="{tid}">{tab.get("html", "")}</div>'
                if tab.get('css'):
                    extra += f"<style>{tab['css']}</style>"
                if tab.get('js'):
                    extra += f"<script>{tab['js']}</script>"
            tab_bar = f'<div class="ad-tabs">{tab_buttons}</div>' if tab_buttons else ''
            body += f'''
            <div class="ad-card">
                <div class="ad-card-h"><span><i class="fas fa-video"></i> Camera Settings</span></div>
                <div class="ad-card-b">
                    <div class="ad-field" style="max-width: 360px;">
                        <label class="ad-label" for="addonCameraSelect">Camera</label>
                        <select id="addonCameraSelect" onchange="addonSelectCamera(this.value)">{options}</select>
                    </div>
                    <div id="addonCamArea" style="display:none;">
                        <form id="addonCamForm" onsubmit="addonSaveCamera(event)" autocomplete="off">
                            {tab_bar}
                            {tab_bodies}
                            <button type="submit" class="btn btn-success" style="margin-top: 10px;"><i class="fas fa-save"></i> Save Camera Settings</button>
                        </form>
                    </div>
                    {'' if cameras else '<div class="ad-empty">No cameras configured yet.</div>'}
                </div>
            </div>{extra}'''

        # ---- module dashboard -----------------------------------------------
        try:
            body += module.get_page_html() or ''
        except Exception as e:
            body += f'<div class="ad-card"><div class="ad-card-b">Dashboard error: {esc(str(e))}</div></div>'

    page_data = {
        'id': module_id,
        'name': module.name,
        'active': active,
        'trial_days': module.trial_days,
        # Only what the page needs — never camera credentials
        'cameras': [{'id': c.get('id'), 'name': c.get('name'), 'status': c.get('status'),
                     'pathName': c.get('pathName')} for c in cameras],
        'tabs': [{k: t.get(k) for k in ('id', 'label', 'on_populate', 'on_reset', 'on_collect')} for t in tabs],
    }

    inner_content = f'''
    <style>{_PAGE_CSS}</style>
    <div class="addon-page">
        <div class="ad-head">
            <div style="display:flex; align-items:center; gap:14px;">
                <div class="ad-icon" style="background: {color}22; color: {color};"><i class="{icon}"></i></div>
                <div>
                    <h1>{esc(module.name)} {badge}</h1>
                    <div class="ad-muted" style="max-width: 720px; margin-top: 4px;">{esc(module.description)}</div>
                </div>
            </div>
            <button class="btn btn-grey" onclick="window.location.href='/'"><i class="fas fa-arrow-left"></i> Dashboard</button>
        </div>
        {body}
        <div class="ad-muted" style="text-align:center; margin-top: 30px;">{esc(module.name)} v{esc(str(module.version))} · by {esc(str(module.author))}</div>
    </div>
    <script type="application/json" id="addon-page-data">{_json_for_script(page_data)}</script>
    <script>{_PAGE_JS}</script>
    '''

    return get_web_ui_html(current_settings=settings, boot_id=boot_id, is_linux=is_linux,
                           nvr_pro_enabled=False, addon_html=inner_content)
