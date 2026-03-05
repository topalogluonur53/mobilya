import re
import os

html_path = r'c:\Kodlamalar\Mühendislik\Dolap\templates\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Define Theme Variables in CSS :root and [data-theme='light']
css_vars = """
        :root, [data-theme="dark"] {
            --cad-canvas-bg: #1e1e1e;
            --cad-panel-bg: #252526;
            --cad-toolbar-bg: #2d2d30;
            --cad-hover-bg: #3e3e42;
            --cad-border: #333333;
            --cad-border-light: #444444;
            --cad-input-border: #555555;
            --cad-text-main: #d4d4d4;
            --cad-text-muted: #aaaaaa;
            --cad-text-highlight: #ffffff;
            --cad-svg-color: rgba(255,255,255,0.1);
        }

        [data-theme="light"] {
            --cad-canvas-bg: #f3f4f6;
            --cad-panel-bg: #ffffff;
            --cad-toolbar-bg: #f8fafc;
            --cad-hover-bg: #e2e8f0;
            --cad-border: #e2e8f0;
            --cad-border-light: #cbd5e1;
            --cad-input-border: #cbd5e1;
            --cad-text-main: #1e293b;
            --cad-text-muted: #475569;
            --cad-text-highlight: #0f172a;
            --cad-svg-color: #f1f5f9;
        }
"""

html = html.replace(':root {\n            --primary: #4F46E5;', css_vars + '\n        :root {\n            --primary: #4F46E5;')

# Create a mapping for CSS replacements
# We first do CSS section then HTML inline styles
theme_map = [
    ('#1e1e1e', 'var(--cad-canvas-bg)'),
    ('#252526', 'var(--cad-panel-bg)'),
    ('#2d2d30', 'var(--cad-toolbar-bg)'),
    ('#3e3e42', 'var(--cad-hover-bg)'),
    ('#333333', 'var(--cad-border)'),
    ('#333', 'var(--cad-border)'),
    ('#444444', 'var(--cad-border-light)'),
    ('#444', 'var(--cad-border-light)'),
    ('#555555', 'var(--cad-input-border)'),
    ('#555', 'var(--cad-input-border)'),
    ('#d4d4d4', 'var(--cad-text-main)'),
    ('#cccccc', 'var(--cad-text-muted)'),
    ('#aaaaaa', 'var(--cad-text-muted)'),
    ('#888888', 'var(--cad-text-muted)'),
    ('#888', 'var(--cad-text-muted)'),
]

# We should be careful about replacing #fff or white because they're used generically.
# I'll replace color: #fff with color: var(--cad-text-highlight)
html = html.replace('color: #fff;', 'color: var(--cad-text-highlight);')
html = html.replace('color:#fff;', 'color:var(--cad-text-highlight);')
html = html.replace('color: white;', 'color: var(--cad-text-highlight);')
html = html.replace('color:white;', 'color:var(--cad-text-highlight);')

for old_val, new_val in theme_map:
    html = html.replace(old_val, new_val)

# Fix background hover mappings in SVG icons inline
html = html.replace('background:rgba(255,255,255,0.1);', 'background:var(--cad-svg-color);')

# 2. Add Theme Toggle Button to Top Menu
toggle_btn_str = """Birim: <strong>mm</strong> &nbsp;&nbsp;|&nbsp;&nbsp; Tema: Koyu"""
toggle_btn_new = """Birim: <strong>mm</strong> &nbsp;&nbsp;|&nbsp;&nbsp; Tema: <span id="theme-toggle-btn" style="cursor:pointer; color:var(--primary); font-weight:bold;">Koyu</span>"""

if toggle_btn_str in html:
    html = html.replace(toggle_btn_str, toggle_btn_new)
else:
    # Handle already modified ones
    pass

# Add Theme JS logic at the end of scripts.
theme_js = """
        // ==========================================
        // THEME TOGGLE LOGIC
        // ==========================================
        const themeBtn = document.getElementById('theme-toggle-btn');
        let currentTheme = localStorage.getItem('cad-theme') || 'dark';

        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            if (themeBtn) {
                themeBtn.textContent = theme === 'dark' ? 'Koyu 🌙' : 'Açık ☀️';
            }
            if (theme === 'dark') {
                if (svgArea) {
                    svgArea.style.backgroundColor = "transparent";
                }
            } else {
                if (svgArea) {
                    svgArea.style.backgroundColor = "transparent";
                }
            }
        }

        applyTheme(currentTheme);

        if (themeBtn) {
            themeBtn.addEventListener('click', () => {
                currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
                localStorage.setItem('cad-theme', currentTheme);
                applyTheme(currentTheme);
                
                // Redraw scene to apply colors
                if (renderer) {
                    scene.background = new THREE.Color(currentTheme === 'dark' ? "#1e1e1e" : "#f3f4f6");
                    drawCabinets3D();
                }
                if (document.getElementById('view-2d').classList.contains('active')) {
                    drawCabinets2D();
                }
            });
        }
"""

# inject right before `// === INIT & KICKOFF ===`
if '// === INIT & KICKOFF ===' in html:
    html = html.replace('// === INIT & KICKOFF ===', theme_js + '\n        // === INIT & KICKOFF ===')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
    
print("Theming applied via script.")
