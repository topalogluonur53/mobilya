import re
import os

html_path = r'c:\Kodlamalar\Mühendislik\Dolap\templates\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Layout Structure (CSS) Grid Rows to add one more header row
grid_old = """        body {
            background-color: #1e1e1e; /* Dark theme CAD */
            color: #d4d4d4;
            display: grid;
            grid-template-columns: 280px 1fr;
            grid-template-rows: 48px 40px 1fr 24px;"""
            
grid_new = """        body {
            background-color: #1e1e1e; /* Dark theme CAD */
            color: #d4d4d4;
            display: grid;
            grid-template-columns: 320px 1fr;
            grid-template-rows: 48px 46px 40px 1fr 24px;"""
html = html.replace(grid_old, grid_new)

# Fix sub-toolbar and main-content rows
html = html.replace('grid-row: 2;\n            background: #2d2d30;', 'grid-row: 3;\n            background: #2d2d30;')
html = html.replace('grid-row: 3;\n            flex: 1;', 'grid-row: 4;\n            flex: 1;')

# Fix left-sidebar row to span tall
sidebar_old = """        /* 2) Sol Panel (Library & Settings) */
        aside.left-sidebar {
            width: 100%;
            grid-column: 1;
            grid-row: 2;"""
sidebar_new = """        /* 2) Sol Panel (Library & Settings) */
        aside.left-sidebar {
            width: 100%;
            grid-column: 1;
            grid-row: 2 / 5;"""
html = html.replace(sidebar_old, sidebar_new)

# 2) Extract .main-header from inside <main> and put it under <header>
start_tag = '<div class="main-header" style="display:none;" id="toolbar">'

if start_tag in html:
    start_idx = html.find(start_tag)
    # The end of main-header is right before <!-- 2D View -->
    end_tag = '<!-- 2D View -->'
    end_idx = html.find(end_tag, start_idx)
    
    if start_idx != -1 and end_idx != -1:
        # Extract and remove from original place
        main_header_str = html[start_idx:end_idx].strip()
        html = html[:start_idx] + "\n        " + html[end_idx:]
        
        # Modify the CSS / display of the extracted string
        main_header_str = main_header_str.replace('style="display:none;" id="toolbar"', 'class="main-header" id="toolbar" style="grid-column: 2; grid-row: 2; background: #252526; border-bottom: 1px solid #333; z-index: 10; padding: 0 16px; height: 100%; display: flex; align-items: center;"')
        
        # Make the buttons look better for dark mode
        main_header_str = main_header_str.replace('border:1px solid var(--border)', 'border:1px solid #444')
        main_header_str = main_header_str.replace('background:var(--border)', 'background:#444')
        main_header_str = main_header_str.replace('color:var(--primary)', 'color:#818cf8')
        main_header_str = main_header_str.replace('border-color:var(--primary)', 'border-color:#818cf8')
        main_header_str = main_header_str.replace('color:var(--success)', 'color:#10b981')
        main_header_str = main_header_str.replace('border-color:var(--success)', 'border-color:#10b981')

        # Insert it directly after `</header>`
        header_end = html.find('</header>')
        if header_end != -1:
            html = html[:header_end + 9] + '\n    <!-- 2ci Menü (Proje + 2D/3D Tabs) -->\n    ' + main_header_str + '\n' + html[header_end + 9:]


# Fix `.main-header { ... }` css to remove margin/padding bottom
main_css_old = """.main-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            margin-bottom: 24px;
            border-bottom: 1px solid #f1f5f9;
        }"""
main_css_new = """.main-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 100%;
        }"""
html = html.replace(main_css_old, main_css_new)


# Tab buttons dark mode 
tb_old = """.tab-btn {
            background: #ffffff;
            border: 1px solid var(--border);"""
tb_new = """.tab-btn {
            background: #2d2d30;
            border: 1px solid #444;"""
html = html.replace(tb_old, tb_new)

# Force the Javascript toggle to not overwrite flex since we want it permanently fixed, but it doesn't hurt.
html = html.replace("document.getElementById('toolbar').style.display = 'flex';", "")


with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
    
print("Successfully re-built all menus according to strict rules.")
