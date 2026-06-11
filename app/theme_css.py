"""
Shared theme palette for standalone pages (GridFusion, IP Management, etc.)

These pages have their own local CSS variable names and hardcoded dark
palettes. To make them follow the dashboard theme WITHOUT rewriting their
layout, we expose a small canonical set of `--app-*` variables (one block per
dashboard theme) and let each page bridge its own variables to them, e.g.:

    body { --bg-primary: var(--app-bg, #0f172a); }

When no theme class is present the `--app-*` vars are undefined, so each bridge
falls back to the page's ORIGINAL color and nothing changes. When a theme class
is set on <body>, the page follows that theme.

The values below mirror the dashboard theme blocks in web_template.py.
"""


def body_theme_class(theme):
    """Map a saved theme name to the <body> class the dashboard would use."""
    css_theme = (theme or '').strip()
    if css_theme == 'dark':
        css_theme = 'dracula'
    elif css_theme == 'light':
        css_theme = 'ui'
    if css_theme and css_theme != 'classic':
        return f'theme-{css_theme}'
    return ''


# Canonical palette per theme. Keys: bg, card, header, title, body, muted,
# accent, accent2 (hover/secondary), success, danger, border, input.
_THEMES = {
    'dark':        ('#0d1117', '#161b22', '#161b22', '#f0f6fc', '#8b949e', '#484f58', '#238636', '#2ea043', '#238636', '#da3633', '#30363d', '#0d1117'),
    'nord':        ('#2e3440', '#3b4252', '#3b4252', '#eceff4', '#d8dee9', '#7b88a1', '#88c0d0', '#81a1c1', '#a3be8c', '#bf616a', '#434c5e', '#2e3440'),
    'dracula':     ('#1e1f29', '#282a36', '#282a36', '#f8f8f2', '#e2e2e9', '#6272a4', '#bd93f9', '#ff79c6', '#50fa7b', '#ff5555', '#44475a', '#1e1f29'),
    'solar-light': ('#fdf6e3', '#eee8d5', '#eee8d5', '#073642', '#586e75', '#93a1a1', '#268bd2', '#2aa198', '#859900', '#dc322f', '#dcdccc', '#fdf6e3'),
    'midnight':    ('#050a14', '#0d1829', '#0d1829', '#e6f1ff', '#a8b2d1', '#495670', '#64ffda', '#52d8c0', '#64ffda', '#f56565', '#1d2d50', '#050a14'),
    'emerald':     ('#064e3b', '#065f46', '#065f46', '#ecfdf5', '#a7f3d0', '#5eba9a', '#10b981', '#059669', '#34d399', '#ef4444', '#047857', '#064e3b'),
    'sunset':      ('#3a2230', '#ffffff', '#ffffff', '#1a202c', '#4a5568', '#718096', '#fa5252', '#e03131', '#fab005', '#e03131', '#e2e8f0', '#ffffff'),
    'matrix':      ('#000000', '#0a0a0a', '#0a0a0a', '#00ff41', '#10b021', '#0a6a14', '#00ff41', '#008f11', '#00ff41', '#ff0000', '#00521a', '#000000'),
    'slate':       ('#334155', '#1e293b', '#1e293b', '#f8fafc', '#94a3b8', '#64748b', '#38bdf8', '#0ea5e9', '#22c55e', '#f43f5e', '#475569', '#0f172a'),
    'cyberpunk':   ('#101010', '#000000', '#000000', '#00f0ff', '#d8cf08', '#888888', '#ff003c', '#d6002f', '#00f0ff', '#ff003c', '#00f0ff', '#000000'),
    'amoled':      ('#000000', '#0a0a0a', '#0a0a0a', '#ffffff', '#dddddd', '#888888', '#ffffff', '#cccccc', '#00ff00', '#ff0000', '#333333', '#000000'),
    'ui':          ('#f4f5f7', '#ffffff', '#ffffff', '#0f172a', '#475569', '#5e6e82', '#0055ff', '#0044cc', '#10b981', '#ef4444', '#cbd5e1', '#ffffff'),
}

_KEYS = ('bg', 'card', 'header', 'title', 'body', 'muted',
         'accent', 'accent2', 'success', 'danger', 'border', 'input')


def _build_css():
    blocks = []
    for name, vals in _THEMES.items():
        decls = ' '.join(f'--app-{k}: {v};' for k, v in zip(_KEYS, vals))
        blocks.append(f'        body.theme-{name} {{ {decls} }}')
    return '\n'.join(blocks)


# Ready-to-embed <style> contents (no surrounding <style> tag).
APP_THEME_CSS = _build_css()
