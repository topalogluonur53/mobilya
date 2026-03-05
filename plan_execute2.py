import os
import re

html_path = r'c:\Kodlamalar\Mühendislik\Dolap\templates\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Make card background dark theme
html = html.replace('background: #ffffff;\n            border: 1px solid #f8fafc;', 'background: transparent;\n            border: 1px solid #3e3e42;')
html = html.replace('background: transparent;\n            border: 1px solid #f8fafc;', 'background: transparent;\n            border: 1px solid #3e3e42;')

# Input fields
html = html.replace('background: #f8fafc;', 'background: #3e3e42;')
html = html.replace('color: #0f172a;', 'color: #d4d4d4;')

# Table borders and background in Cutlist
html = html.replace('th {\n            background: #f1f5f9;', 'th {\n            background: #2d2d30;')
html = html.replace('tr:nth-child(even) {\n            background: #f8fafc;', 'tr:nth-child(even) {\n            background: #252526;')
html = html.replace('tr:hover {\n            background: #f1f5f9;', 'tr:hover {\n            background: #3e3e42;')

# Make the drawing area dark grid
css_drawing_old = """        #drawing-area {
            transform-origin: center center;
            will-change: transform;
        }"""
        
css_drawing_new = """        #drawing-area {
            transform-origin: center center;
            will-change: transform;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
            background-size: 50px 50px;
        }"""
html = html.replace(css_drawing_old, css_drawing_new)

# Force view-2d background
html = html.replace('background-color: var(--bg);', 'background-color: #1e1e1e;')

# Disable top padding on main content to fit nicely below toolbar
html = html.replace('padding: 24px 32px 0 32px;', 'padding: 0;')
html = html.replace('padding: 24px;', 'padding: 24px;') # leave cards alone

# Make SVG background transparent
html = re.sub(r'svgArea\.style\.backgroundColor\s*=\s*"#ffffff";', 'svgArea.style.backgroundColor = "transparent";', html)

# Remove the inline styles that break dark mode on buttons
html = re.sub(r'style="background:#eff6ff;"', 'style="background:rgba(255,255,255,0.1);"', html)
html = re.sub(r'style="background:#fff7ed;"', 'style="background:rgba(255,255,255,0.1);"', html)
html = re.sub(r'style="background:#f0fdf4;"', 'style="background:rgba(255,255,255,0.1);"', html)
html = re.sub(r'style="background:#f5f3ff;"', 'style="background:rgba(255,255,255,0.1);"', html)
html = re.sub(r'style="background:#fef2f2;"', 'style="background:rgba(255,255,255,0.1);"', html)
html = re.sub(r'style="background:#e0f2fe;"', 'style="background:rgba(255,255,255,0.1);"', html)

# Replace the specific text color values for SVG texts
html = html.replace('fill: "var(--primary)"', 'fill: "#818cf8"')
html = html.replace('stroke: "var(--primary)"', 'stroke: "#818cf8"')

# Change the cabinet color on 2D
html = html.replace('stroke="#4a5568"', 'stroke="#aaaaaa"')
html = html.replace('stroke="#2a3a4a"', 'stroke="#888888"')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
    
print("CSS adjustments mapped")
