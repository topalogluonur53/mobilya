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
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
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
            font-size: 16px;
        }
        .tool-btn:hover { background: #3e3e42; color: #fff;}
        .tool-btn.active { background: rgba(79, 70, 229, 0.4); color: #fff; border: 1px solid rgba(79,70,229,0.8); }

        /* 2) Sol Panel (Library & Settings) */
        aside.left-sidebar {"""

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

sidebar_css_new = """            grid-column: 1;
            grid-row: 2;
            background: #252526;
            border-right: 1px solid #333;
            padding: 16px;
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
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .inspector-group {
            background: #2d2d30;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #3e3e42;
        }

        .inspector-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-size: 0.85rem;
        }
        .inspector-row label {
            color: #aaa;
        }
        .inspector-row input, .inspector-row select {
            background: #3e3e42;
            border: 1px solid #555;
            color: #fff;
            padding: 4px 8px;
            border-radius: 4px;
            width: 80px;
            text-align: right;
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

# Subdue light theme specific colors in the original CSS
html = html.replace('background: #fff;', 'background: #2d2d30;')
html = html.replace('border: 1px solid var(--border);', 'border: 1px solid #3e3e42;')
html = html.replace('color: var(--text-main);', 'color: #d4d4d4;')
html = html.replace('background: var(--surface);', 'background: #252526;')
html = html.replace('color: var(--text-muted);', 'color: #aaaaaa;')
html = html.replace('box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);', 'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);')


# ---------------------- HTML DOM Replacements -----------------------
body_open_tag = "<body>"
top_toolbar_html = """<body>
    <!-- 1) Üst Araç Çubuğu (Top Toolbar) -->
    <header class="top-toolbar">
        <div style="font-weight: 700; color: #fff; margin-right: 20px;">CAD Planlayıcı</div>
        <div class="top-menu">
            <div>Dosya</div>
            <div>Düzen</div>
            <div>Görünüm</div>
            <div>Standartlar</div>
            <div>Yardım</div>
        </div>
        <div class="tool-group" id="tool-group">
            <button class="tool-btn active" title="Seçim Aracı (S)" data-tool="select">🖱️</button>
            <button class="tool-btn" title="Taşı - X Ekseninde Kaydır (M)" data-tool="move">↔️</button>
            <button class="tool-btn" title="Manuel Cihaz Ekle" data-tool="place">➕</button>
        </div>
        <div style="flex:1"></div>
        <div style="font-size: 0.8rem; color: #aaa; border-left: 1px solid #444; padding-left:16px;">
            Birim: <strong>mm</strong> &nbsp;&nbsp;|&nbsp;&nbsp; Tema: Koyu
        </div>
    </header>
"""
html = html.replace(body_open_tag, top_toolbar_html)


main_content_end_tag = "    </div>\n    <div class=\"tools-backdrop\" id=\"tools-backdrop\" onclick=\"closeToolsDrawer()\"></div>"

inspector_html = """    </div>

    <!-- 4) Sağ Özellik Paneli (Inspector) -->
    <aside class="right-inspector" id="inspector-panel">
        <h3 style="font-size:0.9rem; margin-bottom: 8px; border-bottom: 1px solid #444; padding-bottom: 8px;">Özellikler (Inspector)</h3>
        <div id="inspector-content">
            <div style="font-size: 0.85rem; color: #888; text-align:center; padding: 40px 0;">
                <div style="font-size:2rem; margin-bottom:10px;">🖱️</div>
                Sahneden düzenlemek istediğiniz bir<br>modül veya cihazı seçin.
            </div>
        </div>
    </aside>

    <!-- 5) Alt Status Bar -->
    <footer class="status-bar">
        <div id="status-left">Görünüm: 2D Plan Mode | Seçili obje yok</div>
        <div id="status-right" style="display:flex; gap:16px;">
            <span id="coord-display">X: -, Y: -</span>
            <span>Snap: <b>Aktif (10mm)</b></span>
        </div>
    </footer>
    <div class="tools-backdrop" id="tools-backdrop" onclick="closeToolsDrawer()"></div>"""

html = html.replace(main_content_end_tag, inspector_html)


# Update context menu logic - redirect selections to inspector
script_repl = """            let selectedObjectForInspector = null;
            function showContext(e, obj, isPiller = false) {
                // YENI CAD SİSTEMİ: Prompt ve pop-up yerine Sağ Tarafı doldur.
                selectedObjectForInspector = obj;
                
                const panel = document.getElementById('inspector-content');
                
                // Update status bar
                document.getElementById('status-left').textContent = `Seçili: ${obj.label || obj.type || (isPiller ? 'Kör Parça' : 'Modül')}`;

                let formHtml = `
                    <div class="inspector-group">
                        <div style="font-weight:bold; margin-bottom:10px; color:#fff;">${obj.label || obj.type || 'Bilinmeyen'}</div>
                        <div class="inspector-row">
                            <label>ID</label>
                            <span style="color:#aaa;">${obj.id}</span>
                        </div>
                        <div class="inspector-row">
                            <label>Genişlik (W)</label>
                            <input type="number" id="insp-w" value="${obj.width_mm}">
                        </div>
                        <div class="inspector-row">
                            <label>Yükseklik (H)</label>
                            <input type="number" id="insp-h" value="${obj.height_mm}">
                        </div>
                        <div class="inspector-row">
                            <label>Başlangıç (X)</label>
                            <input type="number" id="insp-x" value="${obj.start_mm}">
                        </div>
                    </div>
                `;

                if (obj.kind === 'BASE' || obj.kind === 'WALL') {
                     formHtml += `
                     <div class="inspector-group">
                        <div style="font-weight:bold; margin-bottom:10px; color:#fff;">Kapak Ayarları</div>
                        <div class="inspector-row">
                            <label>Kapak Stili</label>
                            <select id="insp-door">
                                <option value="AUTO" ${obj.door_style==='AUTO'?'selected':''}>Otomatik</option>
                                <option value="1" ${obj.door_style==='1'?'selected':''}>1 Kapaklı</option>
                                <option value="2" ${obj.door_style==='2'?'selected':''}>2 Kapaklı</option>
                            </select>
                        </div>
                        <div class="inspector-row">
                            <label>Çekmece</label>
                            <select id="insp-drawer">
                                <option value="true" ${obj.has_drawers?'selected':''}>Var</option>
                                <option value="false" ${!obj.has_drawers?'selected':''}>Yok</option>
                            </select>
                        </div>
                         <div class="inspector-row">
                            <label>Modülü Kilitle</label>
                            <input type="checkbox" id="insp-lock" ${obj.is_locked?'checked':''} style="width:20px;">
                        </div>
                     </div>
                     `;
                }
                
                formHtml += `<button onclick="applyInspectorChanges()" style="width:100%; margin-top:10px; padding:8px; background:var(--primary); color:white; border:none; border-radius:4px; cursor:pointer;">Mekanı Yeniden Hesapla</button>`;
                
                if(obj.type) { 
                    // this is an appliance
                    formHtml += `<button onclick="deleteSelectedObj()" style="width:100%; margin-top:10px; padding:8px; background:#ef4444; color:white; border:none; border-radius:4px; cursor:pointer;">Cihazı Sil</button>`;
                }

                panel.innerHTML = formHtml;
                e.stopPropagation();
            }

            async function applyInspectorChanges() {
                if(!selectedObjectForInspector) return;
                const obj = selectedObjectForInspector;
                
                // Read from inputs
                const w = parseInt(document.getElementById('insp-w').value);
                const x = parseInt(document.getElementById('insp-x').value);
                
                let payload = { width_mm: w, start_mm: x };

                if(obj.kind) {
                    // Cabinet specific
                    payload.is_locked = document.getElementById('insp-lock')?.checked || false;
                    payload.door_style = document.getElementById('insp-door')?.value;
                    payload.has_drawers = document.getElementById('insp-drawer')?.value === 'true';
                }

                const endpoint = obj.kind ? `/api/cabinets/${obj.id}/` : `/api/appliances/${obj.id}/`;
                await apiRequest(endpoint, 'PATCH', payload);
                await apiRequest(`/api/projects/${projectId}/generate/`, 'POST');
                await reloadData();
                document.getElementById('status-left').textContent = 'Değişiklik kaydedildi, sistem güncellendi.';
            }

            async function deleteSelectedObj() {
                 if(!selectedObjectForInspector) return;
                 await apiRequest(`/api/appliances/${selectedObjectForInspector.id}/`, 'DELETE');
                 await apiRequest(`/api/projects/${projectId}/generate/`, 'POST');
                 await reloadData();
                 document.getElementById('inspector-content').innerHTML = '<p>Obje silindi.</p>';
                 selectedObjectForInspector = null;
                 document.getElementById('status-left').textContent = 'Hazır.';
            }

            // --- END NEW INSTRUCTOR BLOCK ---
"""

html = html.replace('function showContext(e, cab) {', script_repl + '\n            function showContextOld(e, cab) {')
html = html.replace('function showFillerContext(cab) {', 'function showFillerContext(cab) { showContext(event, cab, true); return; // override')

html = html.replace('function showApplianceContext(e, appl) {', 'function showApplianceContext(e, appl) {\n                showContext(e, appl);\n                return;\n')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Architecture successfully applied!")
