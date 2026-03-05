import os
import re

html_path = r'c:\Kodlamalar\Mühendislik\Dolap\templates\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Layout Structure (CSS)
grid_old = """        body {
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
        }"""
        
grid_new = """        body {
            background-color: #1e1e1e; /* Dark theme CAD */
            color: #d4d4d4;
            display: grid;
            grid-template-columns: 280px 1fr;
            grid-template-rows: 48px 40px 1fr 24px;
            height: 100vh;
            overflow: hidden;
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
        }
        
        /* Yatay Özellikler Çubuğu (Propertiers Bar) */
        .sub-toolbar {
            grid-column: 2;
            grid-row: 2;
            background: #2d2d30;
            border-bottom: 1px solid #3e3e42;
            display: flex;
            align-items: center;
            padding: 0 16px;
            gap: 16px;
            font-size: 0.8rem;
            color: #cccccc;
            z-index: 10;
        }
        
        .sub-toolbar input, .sub-toolbar select {
            background: #1e1e1e;
            border: 1px solid #555;
            color: #fff;
            padding: 2px 6px;
            border-radius: 4px;
            width: 70px;
            font-size: 0.8rem;
        }
        
        .prop-group {
            display: flex;
            align-items: center;
            gap: 6px;
            border-right: 1px solid #444;
            padding-right: 16px;
        }
        """
if grid_old in html:
    html = html.replace(grid_old, grid_new)

# 2. Main content CSS update
mc_old = """.main-content {
            grid-column: 2;
            grid-row: 2;
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            background: #1e1e1e; /* Dark Canvas */
        }"""
mc_new = """.main-content {
            grid-column: 2;
            grid-row: 3;
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            background: #1e1e1e; /* Dark Canvas */
        }"""
if mc_old in html:
    html = html.replace(mc_old, mc_new)


# 3. Completely hide right inspector css
ri_old = """/* 4) Sağ Inspector Özellik Paneli */
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
        }"""
ri_new = """/* 4) Sağ Inspector Özellik Paneli (GIZLI, Artık üstte) */
        .right-inspector { display: none; }"""
if ri_old in html:
    html = html.replace(ri_old, ri_new)

# 4. Inject Sub Toolbar HTML just after </header>
html = html.replace('</header>', '</header>\n    <!-- Yatay Özellik Çubuğu (Properties) -->\n    <div class="sub-toolbar" id="inspector-horizontal"><div style="color:#888;">Sahneden düzenlemek istediğiniz bir nesne seçin.</div></div>')

# 5. Fix JS to render inside horizontal bar instead of vertical Panel
js_old = """                const panel = document.getElementById('inspector-content');
                
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

                panel.innerHTML = formHtml;"""

js_new = """                const panel = document.getElementById('inspector-horizontal'); // YATAY BAR
                
                // Update status bar
                document.getElementById('status-left').textContent = `Seçili: ${obj.label || obj.type || (isPiller ? 'Kör Parça' : 'Modül')}`;

                let formHtml = `
                    <div style="font-weight:600; color:#fff; min-width:120px; border-right:1px solid #444; padding-right:16px;">
                        ${obj.label || obj.type || 'Bilinmeyen'} <span style="color:#777; font-size:0.7rem;">#${obj.id}</span>
                    </div>

                    <div class="prop-group">
                        <label>W:</label> <input type="number" id="insp-w" value="${obj.width_mm}">
                        <label style="margin-left:8px;">H:</label> <input type="number" id="insp-h" value="${obj.height_mm}">
                        <label style="margin-left:8px;">X:</label> <input type="number" id="insp-x" value="${obj.start_mm}">
                    </div>
                `;

                if (obj.kind === 'BASE' || obj.kind === 'WALL') {
                     formHtml += `
                     <div class="prop-group">
                        <label>Kapak:</label>
                        <select id="insp-door" style="width:90px;">
                            <option value="AUTO" ${obj.door_style==='AUTO'?'selected':''}>Oto</option>
                            <option value="1" ${obj.door_style==='1'?'selected':''}>1 Kapak</option>
                            <option value="2" ${obj.door_style==='2'?'selected':''}>2 Kapak</option>
                        </select>
                        
                        <label style="margin-left:8px;">Çekmece:</label>
                        <select id="insp-drawer" style="width:60px;">
                            <option value="true" ${obj.has_drawers?'selected':''}>Var</option>
                            <option value="false" ${!obj.has_drawers?'selected':''}>Yok</option>
                        </select>
                        
                        <label style="margin-left:8px;" title="Motor bu modülü bir daha ezmesin">Kilitle:</label>
                        <input type="checkbox" id="insp-lock" ${obj.is_locked?'checked':''} style="width:16px; height:16px; margin:0;">
                     </div>
                     `;
                }
                
                formHtml += `<button onclick="applyInspectorChanges()" style="padding:4px 12px; background:var(--primary); color:white; border:none; border-radius:4px; font-weight:500; cursor:pointer;">Uygula</button>`;
                
                if(obj.type) { 
                    // this is an appliance
                    formHtml += `<button onclick="deleteSelectedObj()" style="padding:4px 12px; background:#ef4444; color:white; border:none; border-radius:4px; margin-left:8px; font-weight:500; cursor:pointer;">Sil</button>`;
                }

                panel.innerHTML = formHtml;"""

if js_old in html:
    html = html.replace(js_old, js_new)

# Update the escape functionality
html = html.replace("document.getElementById('inspector-content').innerHTML = '<p>Sahneden bir nesne seçin.</p>';", "document.getElementById('inspector-horizontal').innerHTML = '<div style=\"color:#888;\">Sahneden düzenlemek istediğiniz bir nesne seçin.</div>';")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Horizontal prop bar added")
