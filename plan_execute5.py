import re

html_path = r'c:\Kodlamalar\Mühendislik\Dolap\templates\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Grid Configuration
old_grid = """        body {
            background-color: #1e1e1e; /* Dark theme CAD */
            color: #d4d4d4;
            display: grid;
            grid-template-columns: 320px 1fr;
            grid-template-rows: 48px 40px 1fr 24px;"""
new_grid = """        body {
            background-color: #1e1e1e; /* Dark theme CAD */
            color: #d4d4d4;
            display: grid;
            grid-template-columns: 320px 1fr;
            grid-template-rows: 48px 48px 40px 1fr 24px;"""
html = html.replace(old_grid, new_grid)

# Left Sidebar spanning
html = html.replace('grid-row: 2 / 4;', 'grid-row: 2 / 5;')

# Extract main_header string to move it
start_tag = '<div class="main-header" style="display:none;" id="toolbar">'
end_tag = '        <!-- 2D View -->'
start_idx = html.find(start_tag)
end_idx = html.find(end_tag)

if start_idx != -1 and end_idx != -1:
    main_header_str = html[start_idx:end_idx]
    
    # Remove from original location
    html = html.replace(main_header_str, '')
    
    # Modify main_header_str to have CSS grid classes, dark theme, remove display:none
    main_header_str = main_header_str.replace('style="display:none;" id="toolbar"', 'class="main-header" id="toolbar" style="grid-column: 2; grid-row: 2; background: #252526; border-bottom: 1px solid #333; z-index: 10;"')
    
    # Buttons styling for dark mode in main-header
    main_header_str = main_header_str.replace('border:1px solid var(--border)', 'border:1px solid #444')
    main_header_str = main_header_str.replace('background:var(--border)', 'background:#444')
    main_header_str = main_header_str.replace('color:var(--primary)', 'color:#818cf8')
    main_header_str = main_header_str.replace('border-color:var(--primary)', 'border-color:#818cf8')
    main_header_str = main_header_str.replace('color:var(--success)', 'color:#10b981')
    main_header_str = main_header_str.replace('border-color:var(--success)', 'border-color:#10b981')
    
    # Insert right after top-toolbar
    html = html.replace('</header>', '</header>\n    <!-- 2ci Menü (Proje + 2D/3D Tabs) -->\n    ' + main_header_str)

# Shift items down
html = html.replace('.sub-toolbar {\n            grid-column: 2;\n            grid-row: 2;', '.sub-toolbar {\n            grid-column: 2;\n            grid-row: 3;')
html = html.replace('.main-content {\n            grid-column: 2;\n            grid-row: 3;', '.main-content {\n            grid-column: 2;\n            grid-row: 4;')

# Main Header CSS styling for padding to look natural
old_css_main_header = """.main-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            margin-bottom: 24px;
            border-bottom: 1px solid #f1f5f9;
        }"""
new_css_main_header = """.main-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 16px;
        }"""
html = html.replace(old_css_main_header, new_css_main_header)

# Tab button dark mode fixes
tabbtn_css_old = """.tab-btn {
            background: #ffffff;
            border: 1px solid var(--border);"""
tabbtn_css_new = """.tab-btn {
            background: #2d2d30;
            border: 1px solid #444;"""
html = html.replace(tabbtn_css_old, tabbtn_css_new)
html = html.replace('color: var(--text-muted);', 'color: #aaaaaa;')
html = html.replace('color: var(--text-main);', 'color: currentColor;')

# The JS that toggled it visible: `document.getElementById('toolbar').style.display = 'flex';`
# Can stay since it sets to flex, but to ensure it is always visible and flex from start:
# It's already fixed in HTML because we removed display:none. But wait, we added `style="grid-column..."` 
html = html.replace('document.getElementById(\'toolbar\').style.display = \'flex\';', '')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Main Header moved")
