import re
import os

path = r'c:\Kodlamalar\Mühendislik\Dolap\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace hardcoded base and wall heights in logic
# 1) let's replace `const ct_mm = 40;` to use `project.countertop_height || 40`
content = content.replace('const ct_mm = 40;', 'const ct_mm = project.countertop_height || 40;')
# 2) let's replace `const legH_mm = 100;` to use `project.toe_kick_height || 100` 
content = re.sub(r'const legH_mm\s*=\s*100;', 'const legH_mm = project.toe_kick_height || 100;', content)
# 3) replace `project.base_height + 40 +` with `project.base_height + (project.countertop_height||40) +`
content = content.replace('project.base_height + 40 +', 'project.base_height + (project.countertop_height || 40) +')
# 4) replace `100 + project.base_height` with `(project.toe_kick_height || 100) + project.base_height`
content = content.replace('100 + project.base_height', '(project.toe_kick_height || 100) + project.base_height')
# 5) replace `project.base_height + 100` with `project.base_height + (project.toe_kick_height || 100)`
content = content.replace('project.base_height + 100', 'project.base_height + (project.toe_kick_height || 100)')

# Let's insert the Accordion panel
accordion_html = """
        <!-- Uygulama Ayarları -->
        <div class="accordion-item" id="panel-settings">
            <button class="accordion-btn" onclick="toggleAccordion(this)">
                <div class="accordion-icon" style="background:#e0f2fe;">⚙️</div>
                <div class="accordion-title">
                    <strong>Uygulama Ayarları</strong>
                    <span>Standart ölçüleri değiştir</span>
                </div>
                <svg class="accordion-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </button>
            <div class="accordion-body">
                <div class="accordion-body-inner">
                    <form id="form-settings" style="margin-top:12px;">
                        <div class="row">
                            <div class="form-group">
                                <label>Ayak / Baza (mm)</label>
                                <input type="number" id="set-toe" value="100">
                            </div>
                            <div class="form-group">
                                <label>Tezgah Kalınlığı (mm)</label>
                                <input type="number" id="set-counter" value="40">
                            </div>
                        </div>
                        <div class="row">
                            <div class="form-group">
                                <label>Alt Dolap Boyu (mm)</label>
                                <input type="number" id="set-base" value="760">
                            </div>
                            <div class="form-group">
                                <label>Tezgah Arası (mm)</label>
                                <input type="number" id="set-gap" value="600">
                            </div>
                        </div>
                        <div class="row">
                            <div class="form-group">
                                <label>Üst Dolap Boyu (mm)</label>
                                <input type="number" id="set-wall" value="760">
                            </div>
                        </div>
                        <button type="submit" class="outline">Değişiklikleri Uygula</button>
                    </form>
                </div>
            </div>
        </div>
"""

# Insert under "Yeni Proje"
target = '        <!-- 4) Duvar Ölçüleri -->'
content = content.replace(target, accordion_html + '\n' + target)

# Add event listener for form-settings to JS
js_logic = """
            // Form Settings Submit Listener
            document.getElementById('form-settings')?.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (!project || !projectId) {
                    showAlert('Önce bir proje oluşturun veya açın.', 'error');
                    return;
                }
                const body = {
                    toe_kick_height: parseInt(document.getElementById('set-toe').value),
                    countertop_height: parseInt(document.getElementById('set-counter').value),
                    base_height: parseInt(document.getElementById('set-base').value),
                    gap_height: parseInt(document.getElementById('set-gap').value),
                    wall_height: parseInt(document.getElementById('set-wall').value)
                };
                await apiRequest(`/api/projects/${projectId}/`, 'PATCH', body);
                project = await apiRequest(`/api/projects/${projectId}/`);
                await apiRequest(`/api/projects/${projectId}/generate/`, 'POST'); // Regenerate cabinets with new heights
                showAlert('Uygulama Ayarları başarıyla güncellendi.', 'success');
                await reloadData();
            });
"""

# populate on load
js_populate = """
                if (project.toe_kick_height !== undefined) {
                    document.getElementById('set-toe').value = project.toe_kick_height;
                    document.getElementById('set-counter').value = project.countertop_height;
                    document.getElementById('set-base').value = project.base_height;
                    document.getElementById('set-gap').value = project.gap_height;
                    document.getElementById('set-wall').value = project.wall_height;
                }
"""

content = content.replace("document.getElementById('form-project').addEventListener('submit', async (e) => {", js_logic + "\n            document.getElementById('form-project').addEventListener('submit', async (e) => {")
content = content.replace("document.getElementById('proj-layout').value = project.layout_type;", "document.getElementById('proj-layout').value = project.layout_type;\n" + js_populate)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML Fixed")
