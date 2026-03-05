import os

html_path = r'c:\Kodlamalar\Mühendislik\Dolap\templates\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# I messed up by using replace() maliciously which duplicated pieces. Let's fix it by extracting the exact body and cleaning it.
# We will use regex to remove ALL top-toolbars and sub-toolbars and then construct the grid properly.
import re

# Remove everything from <body> to <aside class="left-sidebar">
body_start = html.find('<body>')
sidebar_start = html.find('    <aside class="left-sidebar">')

if body_start != -1 and sidebar_start != -1:
    clean_html = html[:body_start + 6] + '\n'
    
    # Generate the perfect 3-bar header
    perfect_headers = """
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

    <!-- 2) Tabs & View Menu -->
    <div class="main-header" id="toolbar" style="grid-column: 2; grid-row: 2; background: #252526; border-bottom: 1px solid #333; z-index: 10;">
        <div>
            <h2 style="margin:0; border:none;" id="current-project-title">Proje Adı</h2>
        </div>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('view-2d')">2D Plan</button>
            <button class="tab-btn" onclick="switchTab('view-3d')">3D Görünüm</button>
            <button class="tab-btn" onclick="switchTab('view-cutlist')">Kesim Listesi</button>
        </div>

        <div style="display:flex; gap:12px; align-items:center;">
            <!-- Undo/Redo Group -->
            <div style="display:flex; border:1px solid #444; border-radius:8px; overflow:hidden; height:38px;">
                <button id="btn-undo" class="action-btn" disabled title="Geri Al">↶</button>
                <div style="width:1px; background:#444;"></div>
                <button id="btn-redo" class="action-btn" disabled title="İleri Al">↷</button>
            </div>

            <!-- View Group (Görünüm) -->
            <div class="dropdown">
                <button class="outline" style="width:auto; padding:8px 12px; display:flex; gap:6px; align-items:center; height:38px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    Görünüm ▾
                </button>
                <div class="dropdown-content">
                    <div class="dropdown-menu">
                        <button id="btn-toggle-dims" class="dropdown-item">Ölçüleri Gizle</button>
                        <button id="btn-toggle-labels" class="dropdown-item">Yazıları Gizle</button>
                        <button id="btn-toggle-front" class="dropdown-item">MDF Kesiti Göster</button>
                    </div>
                </div>
            </div>

            <!-- Tools & Actions -->
            <button id="btn-fill-gaps" class="outline" style="width:auto; border-color:#10b981; color:#10b981; padding:8px 12px; height:38px; display:flex; align-items:center;">Boşlukları Doldur</button>
            <button id="btn-generate" style="background:#10b981; color:white; border:none; border-radius:8px; width:auto; padding:8px 16px; height:38px; display:flex; align-items:center; cursor:pointer;">Yerleşimi Üret</button>

            <!-- Export Group -->
            <div class="dropdown">
                <button class="outline" style="width:auto; border-color:#818cf8; color:#818cf8; padding:8px 12px; display:flex; gap:6px; align-items:center; height:38px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Dışa Aktar ▾
                </button>
                <div class="dropdown-content">
                    <div class="dropdown-menu">
                        <button id="btn-export-2d" class="dropdown-item">Planı HD İndir</button>
                        <button id="btn-export-pdf" class="dropdown-item">Kesim PDF</button>
                        <button id="btn-csv" class="dropdown-item">CSV İndir</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 3) Yatay Özellik Çubuğu (Inspector Properties) -->
    <div class="sub-toolbar" id="inspector-horizontal">
        <div style="color:#888;">Sahneden düzenlemek istediğiniz bir nesne seçin.</div>
    </div>
"""
    tailHtml = html[sidebar_start:]
    
    # We must also remove `.main-header` duplicates that might be hiding deeper inside `tailHtml` (in <main>).
    # Regex to erase any `<div class="main-header" ...` up to its closing `</div>` structure. 
    # Since regex is greedy, doing it correctly by strings:
    
    idx1 = tailHtml.find('<div class="main-header"')
    while idx1 != -1:
        # Find closing </div> for this main-header. We just need to stop at <!-- 2D View -->
        idx2 = tailHtml.find('<!-- 2D View -->', idx1)
        if idx2 != -1:
            tailHtml = tailHtml[:idx1] + tailHtml[idx2:]
        idx1 = tailHtml.find('<div class="main-header"')

    with open(html_path, 'w', encoding='utf-8') as fw:
        fw.write(clean_html + perfect_headers + tailHtml)

print("Cleanup complete")
