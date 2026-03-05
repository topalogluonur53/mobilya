import os
import re

html_path = r'c:\Kodlamalar\Mühendislik\Dolap\templates\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Make the drawing area have infinite CAD grid look
old_drawing = """        #drawing-area {
            transform-origin: center center;
            will-change: transform;
        }"""
new_drawing = """        #drawing-area {
            transform-origin: center center;
            will-change: transform;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
            background-size: 50px 50px;
        }"""
if old_drawing in html:
    html = html.replace(old_drawing, new_drawing)


# Hook up the tool buttons JS logic
tool_script = """
        // CAD Tool Manager
        let currentTool = 'select';
        
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
                currentTool = e.currentTarget.dataset.tool;
                
                // update status bar text
                const sts = document.getElementById('status-left');
                if(currentTool === 'select') sts.textContent = 'Mod: Seçim. Objeleri seçmek için tıklayın.';
                if(currentTool === 'move') sts.textContent = 'Mod: Taşıma. Objenin üzerine tıklayıp sağa sola sürükleyin.';
                if(currentTool === 'measure') sts.textContent = 'Mod: Ölçü. Mesafe ölçmek için tıklayın.';
                if(currentTool === 'place') sts.textContent = 'Mod: Manuel Eke. Sürükle bırak ile modül ekleyin.';
                
                // Change cursor
                const svgArea = document.getElementById('drawing-area');
                if(svgArea) {
                    if(currentTool === 'move') svgArea.style.cursor = 'ew-resize';
                    else if(currentTool === 'measure') svgArea.style.cursor = 'crosshair';
                    else svgArea.style.cursor = 'default';
                }
            });
        });

        // Global keydown listeners for tools
        document.addEventListener('keydown', (e) => {
            if(e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return; // ignore typing
            
            if(e.key.toLowerCase() === 's' || e.key === 'Escape') {
                document.querySelector('.tool-btn[data-tool="select"]')?.click();
                if(e.key === 'Escape') {
                    // clear selection
                    selectedObjectForInspector = null;
                    document.getElementById('inspector-content').innerHTML = '<p>Sahneden bir nesne seçin.</p>';
                    document.getElementById('status-left').textContent = 'Hazır.';
                }
            } else if(e.key.toLowerCase() === 'm') {
                document.querySelector('.tool-btn[data-tool="move"]')?.click();
            } else if(e.key.toLowerCase() === 't') {
                document.querySelector('.tool-btn[data-tool="measure"]')?.click();
            }
        });
        
        // Track mouse coords on canvas for bottom bar
        document.addEventListener('mousemove', (e) => {
            const wrap = document.getElementById('view-2d');
            if(!wrap || !wrap.classList.contains('active')) return; // only in 2D
            
            const rect = wrap.getBoundingClientRect();
            // simple estimation of coords
            let vx = Math.round((e.clientX - rect.left) / currentScale);
            let vy = Math.round((e.clientY - rect.top) / currentScale);
            const cd = document.getElementById('coord-display');
            if(cd) cd.textContent = `X: ${vx}, Y: ${vy}`;
        });
"""

html = html.replace('// === STATE & GLOBALS ===', tool_script + '\n\n        // === STATE & GLOBALS ===')


with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Tool manager applied")
