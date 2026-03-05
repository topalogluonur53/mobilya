import os

html_path = r'c:\Kodlamalar\Mühendislik\Dolap\templates\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Layout Structure (CSS)
css_to_replace = """        body {
            background-color: var(--bg);
            color: var(--text-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sol Ana Menü (Mevcut) */
        aside.left-sidebar {"""

new_css = """        body {
            background-color: #1e1e1e; /* Dark theme CAD */
            color: #d4d4d4;
            display: grid;
            grid-template-columns: 280px 1fr 300px;
            grid-template-rows: 48px 1fr 24px;
            height: 100vh;
            overflow: hidden;
        }

        /* 1) Üst Araç Çubuğu (Top Menu & Toolbar) */
        .top-toolbar {
            grid-column: 1 / 4;
            grid-row: 1;
            background: #252526;
            border-bottom: 1px solid #333;
            display: flex;
            align-items: center;
            padding: 0 16px;
            gap: 20px;
            z-index: 20;
        }
        .top-menu {
            display: flex;
            gap: 16px;
            font-size: 0.85rem;
            color: #cccccc;
        }
        .top-menu div {
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
        }
        .top-menu div:hover {
            background: #3e3e42;
            color: #fff;
        }

        .tool-group {
            display: flex;
            gap: 4px;
            border-left: 1px solid #444;
            padding-left: 20px;
        }
        .tool-btn {
            background: transparent;
            border: none;
            color: #cccccc;
            padding: 6px;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .tool-btn:hover { background: #3e3e42; color: #fff;}
        .tool-btn.active { background: rgba(79, 70, 229, 0.4); color: #fff; border: 1px solid rgba(79,70,229,0.8); }

        /* 2) Sol Panel (Library & Settings) */
        aside.left-sidebar {
            grid-column: 1;
            grid-row: 2;
            """

html = html.replace(css_to_replace, new_css)

# Update sidebar CSS to match dark theme
sidebar_css_old = """            background: var(--bg);
            border-right: 1px solid var(--border);
            padding: 28px 20px 28px 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.04);
            z-index: 10;"""

sidebar_css_new = """            background: #252526;
            border-right: 1px solid #333;
            padding: 16px 16px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            z-index: 10;
            color: #d4d4d4;"""
html = html.replace(sidebar_css_old, sidebar_css_new)


# Center content and Right sidebar updates
css_center_replace = """.main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            background: var(--surface);
        }"""

css_center_new = """.main-content {
            grid-column: 2;
            grid-row: 2;
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            background: #1e1e1e; /* Dark Canvas */
        }
        
        /* 4) Sağ Inspector Özellik Paneli */
        .right-inspector {
            grid-column: 3;
            grid-row: 2;
            background: #252526;
            border-left: 1px solid #333;
            padding: 16px;
            color: #d4d4d4;
            overflow-y: auto;
        }
        
        /* 5) Alt Status Bar */
        .status-bar {
            grid-column: 1 / 4;
            grid-row: 3;
            background: #007acc; /* VSCode style blue */
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 16px;
            font-size: 0.75rem;
            z-index: 20;
        }
        """
html = html.replace(css_center_replace, css_center_new)

# Force h1, h2, labels to look okay on dark theme
html = html.replace('color: var(--text-main);', 'color: currentColor;')
html = html.replace('background: #fff;', 'background: transparent;')
html = html.replace('background: var(--surface);', 'background: #252526;')


# Inject HTML Structure
body_open_tag = "<body>"
top_toolbar_html = """<body>
    <!-- 1) Üst Araç Çubuğu (Top Toolbar) -->
    <header class="top-toolbar">
        <div style="font-weight: 700; color: #fff; margin-right: 20px;">CAD Planlayıcı</div>
        <div class="top-menu">
            <div>Dosya</div>
            <div>Düzen</div>
            <div>Görünüm</div>
            <div>Araçlar</div>
            <div>Yardım</div>
        </div>
        <div class="tool-group" id="tool-group">
            <button class="tool-btn active" title="Seç (S)" data-tool="select">🖱️</button>
            <button class="tool-btn" title="Taşı (M)" data-tool="move">↔️</button>
            <button class="tool-btn" title="Ölç (T)" data-tool="measure">📏</button>
        </div>
        <div style="flex:1"></div>
        <div style="font-size: 0.8rem; color: #aaa;">Birim: mm</div>
    </header>
"""
html = html.replace(body_open_tag, top_toolbar_html)

# Add Right Inspector HTML inside body (before end)
inspector_html = """
    <!-- 4) Sağ Özellik Paneli (Inspector) -->
    <aside class="right-inspector" id="inspector-panel">
        <h3 style="font-size:0.9rem; margin-bottom: 16px; border-bottom: 1px solid #444; padding-bottom: 8px;">Özellikler (Inspector)</h3>
        <div id="inspector-content" style="font-size: 0.85rem; color: #aaa;">
            <p>Sahneden bir nesne seçin.</p>
        </div>
    </aside>

    <!-- 5) Alt Status Bar -->
    <footer class="status-bar">
        <div id="status-left">Hazır</div>
        <div id="status-right" style="display:flex; gap:16px;">
            <span id="coord-display">X: 0, Y: 0</span>
            <span>Snap: Açık</span>
        </div>
    </footer>
"""

# Insert just before <script> tags begin
html = html.replace('<script src="https://cdnjs', inspector_html + '\n    <script src="https://cdnjs')


with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("UI transformed partially")
