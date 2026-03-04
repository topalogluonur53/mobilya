
        let projectId = null, project = null, segments = [], appliances = [], cabinets = [];

        const typeWidthMap = { 'FRIDGE': 800, 'DW': 600, 'OVEN': 600, 'SINK': 800, 'HOOD': 600 };
        const emojiMap = { 'FRIDGE': '🧊', 'DW': '🍽️', 'OVEN': '🍳', 'SINK': '🚰', 'HOOD': '💨' };

        // --- Interaction State ---
        let draggedApplId = null;
        let draggedPairedApplId = null;
        let dragStartX = 0;
        let initialApplStartMm = 0;
        let currentScale = 1;
        let currentMaxLimit = 0;
        let selectedCabId = null;
        let showDimensions = true;
        let showFrontView = true;

        let panZoomState = { zoom: 1, panX: 0, panY: 0, isPanning: false, startX: 0, startY: 0 };
        function applyPanZoom() {
            const area = document.getElementById('drawing-area');
            if (area) {
                area.style.transform = `translate(${panZoomState.panX}px, ${panZoomState.panY}px) scale(${panZoomState.zoom})`;
            }
        }

        let undoStack = [];
        let redoStack = [];

        function updateUndoRedoButtons() {
            document.getElementById('btn-undo').disabled = undoStack.length === 0;
            document.getElementById('btn-redo').disabled = redoStack.length === 0;
        }

        async function saveHistoryState() {
            if (!projectId) return;
            try {
                const state = await apiRequest(`/api/projects/${projectId}/export_state/`);
                undoStack.push(state);
                redoStack = []; // Yeni işlem yapıldığında ileri alma havuzu sıfırlanır
                updateUndoRedoButtons();
            } catch (e) { console.error('History API error', e); }
        }

        async function undoHistory() {
            if (undoStack.length === 0 || !projectId) return;
            const currentState = await apiRequest(`/api/projects/${projectId}/export_state/`);
            redoStack.push(currentState);

            const prevState = undoStack.pop();
            await apiRequest(`/api/projects/${projectId}/restore_state/`, 'POST', prevState);
            await reloadData();
            updateUndoRedoButtons();
        }

        async function redoHistory() {
            if (redoStack.length === 0 || !projectId) return;
            const currentState = await apiRequest(`/api/projects/${projectId}/export_state/`);
            undoStack.push(currentState);

            const nextState = redoStack.pop();
            await apiRequest(`/api/projects/${projectId}/restore_state/`, 'POST', nextState);
            await reloadData();
            updateUndoRedoButtons();
        }

        document.getElementById('btn-undo').addEventListener('click', undoHistory);
        document.getElementById('btn-redo').addEventListener('click', redoHistory);

        document.getElementById('btn-toggle-dims').addEventListener('click', (e) => {
            showDimensions = !showDimensions;
            e.target.textContent = showDimensions ? 'Ölçüleri Gizle' : 'Ölçüleri Göster';
            draw2D();
        });

        document.getElementById('btn-toggle-front').addEventListener('click', (e) => {
            showFrontView = !showFrontView;
            e.target.textContent = showFrontView ? 'MDF Kesiti Göster' : 'Ön Görünüş Göster';
            draw2D();
        });

        function showAlert(msg, isSuccess = false) {
            const a = document.getElementById('alert-box');
            a.textContent = msg; a.className = 'alert ' + (isSuccess ? 'success' : 'error');
            setTimeout(() => a.style.display = 'none', 3000);
        }

        function switchTab(tabId) {
            document.querySelectorAll('.content-area').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');

            if (tabId === 'view-3d') init3D();
            if (tabId === 'view-cutlist') loadCutlist();
        }

        async function apiRequest(url, method = 'GET', body = null) {
            const options = { method, headers: { 'Content-Type': 'application/json' } };
            if (body) options.body = JSON.stringify(body);
            const res = await fetch(url, options);
            if (!res.ok && res.status !== 204) {
                const err = await res.json().catch(() => ({ error: 'Error' }));
                throw new Error(err.error || 'Server error');
            }
            if (res.status === 204) return null;
            return await res.json();
        }

        document.getElementById('appl-type').addEventListener('change', e => {
            document.getElementById('appl-width').value = typeWidthMap[e.target.value] || 600;
        });

        document.getElementById('proj-layout').addEventListener('change', e => {
            document.getElementById('group-seg-b').style.display = e.target.value === 'L' ? 'block' : 'none';
        });

        document.getElementById('form-project').addEventListener('submit', async e => {
            e.preventDefault();
            const bd = {
                name: document.getElementById('proj-name').value,
                layout_type: document.getElementById('proj-layout').value
            };

            try {
                project = await apiRequest('/api/projects/', 'POST', bd);
                projectId = project.id;

                const ws = document.getElementById('panel-workspace');
                ws.style.opacity = '1';
                ws.style.pointerEvents = 'auto';

                document.getElementById('toolbar').style.display = 'flex';
                document.getElementById('current-project-title').textContent = project.name;

                if (project.layout_type === 'L') {
                    document.getElementById('group-seg-b').style.display = 'block';
                    document.getElementById('seg-len-b').required = true;
                }

                showAlert('Proje başarıyla oluşturuldu, şimdi duvar ölçülerini girin.', true);
            } catch (err) {
                showAlert("Proje oluşturulamadı: " + err.message);
                console.error(err);
            }
        });

        document.getElementById('form-segment').addEventListener('submit', async e => {
            e.preventDefault();
            const lenA = parseInt(document.getElementById('seg-len-a').value);
            const hA = parseInt(document.getElementById('seg-h-a').value);

            // Mevcut segmentler var mı diye kontrol edelim (Update için)
            const segList = segments || [];
            const segA = segList.find(s => s.name === 'A');
            if (segA) {
                await apiRequest(`/api/segments/${segA.id}/`, 'PATCH', { length_mm: lenA, height_mm: hA });
            } else {
                await apiRequest('/api/segments/', 'POST', { project: projectId, name: 'A', length_mm: lenA, height_mm: hA });
            }

            if (project.layout_type === 'L') {
                const lenB = parseInt(document.getElementById('seg-len-b').value);
                const hB = parseInt(document.getElementById('seg-h-b').value);
                if (lenB) {
                    const segB = segList.find(s => s.name === 'B');
                    if (segB) {
                        await apiRequest(`/api/segments/${segB.id}/`, 'PATCH', { length_mm: lenB, height_mm: hB });
                    } else {
                        await apiRequest('/api/segments/', 'POST', { project: projectId, name: 'B', length_mm: lenB, height_mm: hB });
                    }
                }
            }
            await reloadData();
            showAlert('Duvar Ölçüleri Kaydedildi', true);
        });

        async function reloadData() {
            project = await apiRequest(`/api/projects/${projectId}/`);
            segments = project.segments || [];
            appliances = project.appliances || [];
            cabinets = project.cabinets || [];

            const sel = document.getElementById('appl-seg');
            sel.innerHTML = '';
            segments.forEach(s => sel.appendChild(new Option(`Duvar ${s.name} (${s.length_mm}mm)`, s.id)));



            draw2D();
            if (document.getElementById('view-3d').classList.contains('active')) init3D();
        }

        document.getElementById('form-appliance').addEventListener('submit', async e => {
            e.preventDefault();
            const startInput = document.getElementById('appl-start').value;
            const startVal = startInput !== "" ? parseInt(startInput) : -1;

            const bd = {
                project: projectId, segment: document.getElementById('appl-seg').value,
                type: document.getElementById('appl-type').value,
                start_mm: startVal,
                width_mm: parseInt(document.getElementById('appl-width').value)
            };
            await apiRequest('/api/appliances/', 'POST', bd);
            await reloadData();
        });



        document.getElementById('btn-generate').addEventListener('click', async () => {
            try {
                await apiRequest(`/api/projects/${projectId}/generate/`, 'POST');
                await reloadData();
                showAlert('Yerleşim Üretildi', true);
            } catch (e) { showAlert(e.message); }
        });

        function createSVGElem(type, attrs) {
            const el = document.createElementNS("http://www.w3.org/2000/svg", type);
            for (let k in attrs) el.setAttribute(k, attrs[k]);
            return el;
        }

        // Draws an appliance with realistic paths instead of emojis
        function drawApplianceVisual(g, type, w, h, x, y) {
            // Background
            if (type !== 'SINK') {
                g.appendChild(createSVGElem("rect", { x, y, width: w, height: h, fill: "#f1f5f9", stroke: "#cbd5e1", "stroke-width": 2, rx: 4, class: "cab-appl", "data-type": type }));
            } else {
                g.appendChild(createSVGElem("rect", { x, y, width: w, height: h, fill: "transparent", stroke: "none", "data-type": type }));
            }

            // Inner padding
            const pad = 10;
            const iw = w - pad * 2;
            const ih = h - pad * 2;
            const ix = x + pad;
            const iy = y + pad;

            if (type === 'FRIDGE') {
                // Two doors
                const d1h = ih * 0.65;
                const d2h = ih * 0.33;
                g.appendChild(createSVGElem("rect", { x: ix, y: iy, width: iw, height: d1h, fill: "#e2e8f0", stroke: "#94a3b8", rx: 3, "pointer-events": "none" }));
                g.appendChild(createSVGElem("rect", { x: ix, y: iy + d1h + (ih * 0.02), width: iw, height: d2h, fill: "#e2e8f0", stroke: "#94a3b8", rx: 3, "pointer-events": "none" }));
                // Handles
                g.appendChild(createSVGElem("line", { x1: ix + iw - 15, y1: iy + d1h / 2 - 30, x2: ix + iw - 15, y2: iy + d1h / 2 + 30, stroke: "#64748b", "stroke-width": 4, "pointer-events": "none" }));
                g.appendChild(createSVGElem("line", { x1: ix + iw - 15, y1: iy + d1h + 20, x2: ix + iw - 15, y2: iy + d1h + 60, stroke: "#64748b", "stroke-width": 4, "pointer-events": "none" }));
            }
            else if (type === 'OVEN') {
                // Oven window
                g.appendChild(createSVGElem("rect", { x: ix + 10, y: iy + 40, width: iw - 20, height: ih - 80, fill: "#0f172a", rx: 10, "pointer-events": "none" }));
                // Control panel
                g.appendChild(createSVGElem("rect", { x: ix, y: iy, width: iw, height: 30, fill: "#cbd5e1", rx: 2, "pointer-events": "none" }));
                // Knobs
                [1 / 4, 2 / 4, 3 / 4].forEach(pos => {
                    g.appendChild(createSVGElem("circle", { cx: ix + iw * pos, cy: iy + 15, r: 6, fill: "#475569", "pointer-events": "none" }));
                });
                // Handle
                g.appendChild(createSVGElem("line", { x1: ix + 20, y1: iy + 50, x2: ix + iw - 20, y2: iy + 50, stroke: "#cbd5e1", "stroke-width": 4, "pointer-events": "none" }));
            }
            else if (type === 'DW') {
                // Control panel top
                g.appendChild(createSVGElem("rect", { x: ix, y: iy, width: iw, height: 40, fill: "#94a3b8", rx: 2, "pointer-events": "none" }));
                // Handle
                g.appendChild(createSVGElem("rect", { x: ix + iw / 2 - 40, y: iy + 10, width: 80, height: 20, fill: "#e2e8f0", rx: 4, "pointer-events": "none" }));
                g.appendChild(createSVGElem("text", { x: x + w / 2, y: y + h - 30, "text-anchor": "middle", fill: "#94a3b8", "font-weight": "bold", "font-size": "14px", "pointer-events": "none" }).appendChild(document.createTextNode("D/W")).parentNode);
            }
            else if (type === 'SINK') {
                // Sadece musluk görünsün (Evye havzası gizli), arka plan şeffaf
                // Musluk (Faucet) tezgah hizasında, tezgahın yüksekliği = 40 * currentScale
                const ctY = y - (40 * currentScale);
                g.appendChild(createSVGElem("path", { d: `M ${x + w / 2} ${ctY} C ${x + w / 2} ${ctY - 40}, ${x + w / 2 + 40} ${ctY - 20}, ${x + w / 2 + 30} ${ctY + 10}`, fill: "none", stroke: "#64748b", "stroke-width": 6, "stroke-linecap": "round", "pointer-events": "none" }));
                g.appendChild(createSVGElem("circle", { cx: x + w / 2, cy: ctY - 5, r: 10, fill: "#94a3b8", "pointer-events": "none" }));
            }
            else if (type === 'HOOD') {
                // Chimney
                g.appendChild(createSVGElem("rect", { x: x + w / 2 - 30, y: y, width: 60, height: h - 40, fill: "#cbd5e1", "pointer-events": "none" }));
                // Canopy
                g.appendChild(createSVGElem("path", { d: `M ${x + 10} ${y + h - 10} L ${x + w / 2 - 30} ${y + h - 40} L ${x + w / 2 + 30} ${y + h - 40} L ${x + w - 10} ${y + h - 10} Z`, fill: "#94a3b8", "pointer-events": "none" }));
                // Bottom panel
                g.appendChild(createSVGElem("rect", { x: x + 10, y: y + h - 10, width: w - 20, height: 10, fill: "#64748b", "pointer-events": "none" }));
            } else {
                g.appendChild(createSVGElem("text", { x: x + w / 2, y: y + h / 2, class: "text-emoji", "pointer-events": "none" }).appendChild(document.createTextNode(emojiMap[type] || '📦')).parentNode);
            }
        }

        function draw2D() {
            const area = document.getElementById('drawing-area');
            area.innerHTML = '';
            if (!segments.length) return;

            const svgWidth = 1000;
            const totalHeight = 2500;
            const H = 2400;

            segments.forEach(seg => {
                const wallRealHeight = seg.height_mm || 2500;
                currentScale = svgWidth / seg.length_mm;
                const svgHeight = (wallRealHeight + 200) * currentScale; // Ekstra boşluk
                const floorY = wallRealHeight * currentScale;

                const wrap = document.createElement('div');
                wrap.className = 'segment-view';

                const svgNS = "http://www.w3.org/2000/svg";
                const svg = document.createElementNS(svgNS, "svg");
                svg.setAttribute("width", svgWidth);
                svg.setAttribute("height", svgHeight);
                // Dışa taşan textlerin ve sol taraftaki ölçülendirmenin görünmesi için viewBox
                svg.setAttribute("viewBox", `-100 -50 ${svgWidth + 160} ${svgHeight + 50}`);
                svg.style.overflow = 'visible';
                svg.style.marginTop = '40px';
                svg.style.marginRight = '40px';

                // --- Draw Back Wall (visible as background in elevation) ---
                const wallHeight = wallRealHeight * currentScale;
                const wallRect = createSVGElem("rect", {
                    x: 0, y: floorY - wallHeight,
                    width: svgWidth, height: wallHeight,
                    fill: "#f8fafc", stroke: "#cbd5e1", "stroke-width": 4
                });
                svg.appendChild(wallRect);

                // Duvar Bilgisi Gösterimi (Üst ve Sağ - Duvarın Dışında)
                const textTop = createSVGElem("text", { x: svgWidth / 2, y: -20, class: "text-label interact-dim", "font-size": "20px", fill: "var(--primary)", "font-weight": "bold", "cursor": "pointer", "text-anchor": "middle" });
                textTop.textContent = `Genişlik: ${seg.length_mm} mm`;
                textTop.onclick = async () => {
                    const newVal = prompt('Yeni Genişlik (mm):', seg.length_mm);
                    if (newVal && !isNaN(newVal)) {
                        await apiRequest(`/api/segments/${seg.id}/`, 'PATCH', { length_mm: parseInt(newVal) });
                        await apiRequest(`/api/projects/${projectId}/generate/`, 'POST');
                        await reloadData();
                    }
                };
                svg.appendChild(textTop);

                const textRight = createSVGElem("text", { x: svgWidth + 30, y: wallHeight / 2, class: "text-label interact-dim", "font-size": "20px", fill: "var(--primary)", "font-weight": "bold", "cursor": "pointer", "text-anchor": "middle", transform: `rotate(-90 ${svgWidth + 30} ${wallHeight / 2})` });
                textRight.textContent = `Yükseklik: ${wallRealHeight} mm`;
                textRight.onclick = async () => {
                    const newVal = prompt('Yeni Duvar Yüksekliği (mm):', wallRealHeight);
                    if (newVal && !isNaN(newVal)) {
                        await apiRequest(`/api/segments/${seg.id}/`, 'PATCH', { height_mm: parseInt(newVal) });
                        await reloadData();
                    }
                };
                svg.appendChild(textRight);

                if (showDimensions) {
                    // --- Sol Tarafa Yükseklik Ölçülendirmeleri ---
                    const dimX = -60; // Sol taraftan ne kadar dışarıda
                    const dimTick = 10;

                    const baseH_mm = project.base_height; // alt dolap
                    const ct_mm = 40; // tezgah kalınlığı
                    const gapH_mm = project.gap_height || 600; // tezgah ile üst dolap arası boşluk
                    const wallCabH_mm = project.wall_height || 720;
                    const legH_mm = 100; // ayak kalınlığı

                    // Y ekseninde (aşağı doğru artar) koordinatlar
                    const yFloor = floorY;
                    const yLegTop = floorY - legH_mm * currentScale;
                    const yCounterTop = yLegTop - (baseH_mm + ct_mm) * currentScale;
                    const yWallCabBottom = yCounterTop - gapH_mm * currentScale;
                    const yWallCabTop = yWallCabBottom - wallCabH_mm * currentScale;
                    const yCeiling = floorY - wallRealHeight * currentScale;

                    const drawDimLines = (y1, y2, textVal, promptLabel, fieldToPatch) => {
                        svg.appendChild(createSVGElem("line", { x1: dimX, y1: y1, x2: dimX, y2: y2, stroke: "var(--primary)", "stroke-width": 1 }));
                        svg.appendChild(createSVGElem("line", { x1: dimX - dimTick / 2, y1: y1, x2: dimX + dimTick / 2, y2: y1, stroke: "var(--primary)", "stroke-width": 1 }));
                        svg.appendChild(createSVGElem("line", { x1: dimX - dimTick / 2, y1: y2, x2: dimX + dimTick / 2, y2: y2, stroke: "var(--primary)", "stroke-width": 1 }));

                        const textY = (y1 + y2) / 2;
                        const tArgs = {
                            x: dimX - 10, y: textY, class: "text-label",
                            "font-size": "13px", fill: "var(--primary)",
                            "text-anchor": "middle",
                            transform: `rotate(-90 ${dimX - 10} ${textY})`
                        };
                        if (fieldToPatch) {
                            tArgs.class += " interact-dim";
                            tArgs.cursor = "pointer";
                            tArgs["font-weight"] = "bold";
                        }
                        const t = createSVGElem("text", tArgs);
                        t.textContent = `${textVal} mm`;

                        if (fieldToPatch) {
                            t.onclick = async () => {
                                const newVal = prompt(`Yeni ${promptLabel} (mm):`, textVal);
                                if (newVal && !isNaN(newVal)) {
                                    let payload = {};
                                    if (fieldToPatch === 'base_height') {
                                        payload[fieldToPatch] = parseInt(newVal) - 40;
                                    } else {
                                        payload[fieldToPatch] = parseInt(newVal);
                                    }
                                    await apiRequest(`/api/projects/${projectId}/`, 'PATCH', payload);
                                    await apiRequest(`/api/projects/${projectId}/generate/`, 'POST');
                                    await reloadData();
                                }
                            };
                        }
                        svg.appendChild(t);
                    };

                    // 1. Ayak Yüksekliği
                    drawDimLines(yFloor, yLegTop, legH_mm, null, null);

                    // 2. Alt Dolap + Tezgah Yüksekliği
                    drawDimLines(yLegTop, yCounterTop, baseH_mm + ct_mm, "Alt Dolap(Tezgah dahil) Yüksekliği", "base_height");

                    // 3. Tezgah Boşluğu
                    drawDimLines(yCounterTop, yWallCabBottom, gapH_mm, "Tezgah Boşluğu", "gap_height");

                    // 4. Üst Dolap
                    drawDimLines(yWallCabBottom, yWallCabTop, wallCabH_mm, "Üst Dolap Yüksekliği", "wall_height");

                    // 5. Tavan - Üst Dolap Boşluğu
                    const ceilingGap_mm = wallRealHeight - (legH_mm + baseH_mm + ct_mm + gapH_mm + wallCabH_mm);
                    if (ceilingGap_mm > 0) {
                        drawDimLines(yWallCabTop, yCeiling, ceilingGap_mm, null, null);
                    }
                }

                // Draw Cabinets
                const segCabs = cabinets.filter(c => c.segment === seg.id);
                const legH_mm = 100;
                segCabs.forEach(cab => {
                    const w = cab.width_mm * currentScale;
                    const h = cab.height_mm * currentScale;
                    const x = cab.start_mm * currentScale;

                    let y, rectClass;
                    if (cab.kind === 'BASE' || cab.kind === 'APPL' || (cab.kind === 'FILLER' && cab.depth_mm > 400)) {
                        y = floorY - (legH_mm * currentScale) - h;
                        rectClass = cab.kind === 'APPL' ? 'cab-appl' : (cab.kind === 'FILLER' ? 'cab-filler' : 'cab-base');
                    } else {
                        const topY = floorY - ((legH_mm + project.base_height + 40 + (project.gap_height || 600) + project.wall_height) * currentScale);
                        y = topY;
                        rectClass = cab.kind === 'FILLER' ? 'cab-filler' : 'cab-wall';
                    }

                    const g = document.createElementNS(svgNS, "g");
                    const rect = createSVGElem("rect", { x, y, width: w, height: h, rx: 4, class: rectClass });
                    g.appendChild(rect);

                    // MDF 18mm board gap lines (roughly 18mm * scale)
                    const mdf = 18 * currentScale;

                    const dStyle = cab.door_style || 'AUTO';
                    const is4Door = dStyle === '4' || (dStyle === 'AUTO' && cab.width_mm >= 1200);
                    const is2Door = dStyle === '2' || (dStyle === 'AUTO' && cab.width_mm >= 600 && cab.width_mm < 1200);

                    if (cab.kind === 'BASE' || cab.kind === 'WALL') {
                        rect.onclick = (e) => showContext(e, cab);
                    }

                    if (showFrontView) {
                        if (cab.kind === 'BASE') {
                            // Vertical MDF side lines
                            g.appendChild(createSVGElem("line", { x1: x + mdf, y1: y, x2: x + mdf, y2: y + h, stroke: "rgba(0,0,0,0.1)", "stroke-width": 1, "pointer-events": "none" }));
                            g.appendChild(createSVGElem("line", { x1: x + w - mdf, y1: y, x2: x + w - mdf, y2: y + h, stroke: "rgba(0,0,0,0.1)", "stroke-width": 1, "pointer-events": "none" }));

                            if (cab.has_drawers) {
                                const dHeight = h / 3;
                                g.appendChild(createSVGElem("line", { x1: x, y1: y + dHeight, x2: x + w, y2: y + dHeight, stroke: "#94a3b8", "stroke-width": 2, "pointer-events": "none" }));
                                g.appendChild(createSVGElem("line", { x1: x, y1: y + 2 * dHeight, x2: x + w, y2: y + 2 * dHeight, stroke: "#94a3b8", "stroke-width": 2, "pointer-events": "none" }));

                                g.appendChild(createSVGElem("rect", { x: x + w / 2 - 20, y: y + dHeight / 2 - 3, width: 40, height: 6, fill: "#64748b", "pointer-events": "none", rx: 3 }));
                                g.appendChild(createSVGElem("rect", { x: x + w / 2 - 20, y: y + dHeight + dHeight / 2 - 3, width: 40, height: 6, fill: "#64748b", "pointer-events": "none", rx: 3 }));
                                g.appendChild(createSVGElem("rect", { x: x + w / 2 - 20, y: y + 2 * dHeight + dHeight / 2 - 3, width: 40, height: 6, fill: "#64748b", "pointer-events": "none", rx: 3 }));
                            } else {
                                if (is4Door) {
                                    g.appendChild(createSVGElem("line", { x1: x + w / 4, y1: y, x2: x + w / 4, y2: y + h, stroke: "#94a3b8", "stroke-width": 1, "pointer-events": "none" }));
                                    g.appendChild(createSVGElem("line", { x1: x + w / 2, y1: y, x2: x + w / 2, y2: y + h, stroke: "#94a3b8", "stroke-width": 1, "pointer-events": "none" }));
                                    g.appendChild(createSVGElem("line", { x1: x + 3 * w / 4, y1: y, x2: x + 3 * w / 4, y2: y + h, stroke: "#94a3b8", "stroke-width": 1, "pointer-events": "none" }));

                                    // Handles (First pair meets at w/4, second pair meets at 3w/4)
                                    g.appendChild(createSVGElem("rect", { x: x + w / 4 - 15, y: y + 30, width: 4, height: 40, fill: "#64748b", "pointer-events": "none" }));
                                    g.appendChild(createSVGElem("rect", { x: x + w / 4 + 11, y: y + 30, width: 4, height: 40, fill: "#64748b", "pointer-events": "none" }));
                                    g.appendChild(createSVGElem("rect", { x: x + 3 * w / 4 - 15, y: y + 30, width: 4, height: 40, fill: "#64748b", "pointer-events": "none" }));
                                    g.appendChild(createSVGElem("rect", { x: x + 3 * w / 4 + 11, y: y + 30, width: 4, height: 40, fill: "#64748b", "pointer-events": "none" }));
                                } else if (is2Door) {
                                    // 2-door logic
                                    g.appendChild(createSVGElem("line", { x1: x + w / 2, y1: y, x2: x + w / 2, y2: y + h, stroke: "#94a3b8", "stroke-width": 1, "pointer-events": "none" }));
                                    // Handles
                                    g.appendChild(createSVGElem("rect", { x: x + w / 2 - 15, y: y + 30, width: 4, height: 40, fill: "#64748b", "pointer-events": "none" }));
                                    g.appendChild(createSVGElem("rect", { x: x + w / 2 + 11, y: y + 30, width: 4, height: 40, fill: "#64748b", "pointer-events": "none" }));
                                } else {
                                    // Single Door Handle
                                    g.appendChild(createSVGElem("rect", { x: x + 15, y: y + 30, width: 4, height: 40, fill: "#64748b", "pointer-events": "none" }));
                                }
                            }

                            // Ayakları çiz
                            g.appendChild(createSVGElem("rect", { x: x + 20 * currentScale, y: y + h, width: 10 * currentScale, height: legH_mm * currentScale, fill: "#334155", "pointer-events": "none" }));
                            g.appendChild(createSVGElem("rect", { x: x + w - 30 * currentScale, y: y + h, width: 10 * currentScale, height: legH_mm * currentScale, fill: "#334155", "pointer-events": "none" }));

                        } else if (cab.kind === 'WALL') {
                            g.appendChild(createSVGElem("line", { x1: x + mdf, y1: y, x2: x + mdf, y2: y + h, stroke: "rgba(0,0,0,0.1)", "stroke-width": 1, "pointer-events": "none" }));
                            g.appendChild(createSVGElem("line", { x1: x + w - mdf, y1: y, x2: x + w - mdf, y2: y + h, stroke: "rgba(0,0,0,0.1)", "stroke-width": 1, "pointer-events": "none" }));

                            if (is4Door) {
                                g.appendChild(createSVGElem("line", { x1: x + w / 4, y1: y, x2: x + w / 4, y2: y + h, stroke: "#94a3b8", "stroke-width": 1, "pointer-events": "none" }));
                                g.appendChild(createSVGElem("line", { x1: x + w / 2, y1: y, x2: x + w / 2, y2: y + h, stroke: "#94a3b8", "stroke-width": 1, "pointer-events": "none" }));
                                g.appendChild(createSVGElem("line", { x1: x + 3 * w / 4, y1: y, x2: x + 3 * w / 4, y2: y + h, stroke: "#94a3b8", "stroke-width": 1, "pointer-events": "none" }));
                            } else if (is2Door) {
                                g.appendChild(createSVGElem("line", { x1: x + w / 2, y1: y, x2: x + w / 2, y2: y + h, stroke: "#94a3b8", "stroke-width": 1, "pointer-events": "none" }));
                            }
                        }
                    } else {
                        // MDF SKELETON VIEW
                        const isApplianceHousing = cab.kind === 'APPL' || cab.kind === 'FILLER' || (cab.label && cab.label.includes('Bulaşık'));
                        if (!isApplianceHousing) {
                            rect.style.fill = "transparent";
                            rect.style.stroke = "transparent";

                            const drawMDF = (px, py, pw, ph) => {
                                // Yüksek kontrastlı renkler: Ahşap/MDF hissiyatı için krem dolgu, koyu gri/kahverengi kenarlık
                                g.appendChild(createSVGElem("rect", {
                                    x: px, y: py, width: pw, height: ph,
                                    fill: "#fef9c3", stroke: "#713f12", "stroke-width": 1.5,
                                    "pointer-events": "none"
                                }));
                            };

                            // Left & Right Panels (Yan Dikmeler)
                            drawMDF(x, y, mdf, h);
                            drawMDF(x + w - mdf, y, mdf, h);

                            // Top & Bottom Panels (Alt ve Üst Tablalar) - Yan dikmelerin arasına girer
                            drawMDF(x + mdf, y, w - 2 * mdf, mdf);
                            drawMDF(x + mdf, y + h - mdf, w - 2 * mdf, mdf);

                            const pStyle = cab.partition_style || 'AUTO';
                            let numDividers = 0;
                            if (pStyle === '4') numDividers = 3;
                            else if (pStyle === '2') numDividers = 1;
                            else if (pStyle === '1') numDividers = 0;
                            else if (pStyle === 'AUTO') {
                                numDividers = is4Door ? 1 : 0;
                            }

                            const validForDividers = !cab.has_drawers && cab.kind !== 'APPL' && cab.kind !== 'FILLER' && !isApplianceHousing;
                            const activeDividers = validForDividers ? numDividers : 0;

                            // Shelves
                            if (cab.kind === 'BASE') {
                                if (cab.has_drawers) {
                                    const dHeight = h / 3;
                                    drawMDF(x + mdf, y + dHeight - mdf / 2, w - 2 * mdf, mdf);
                                    drawMDF(x + mdf, y + 2 * dHeight - mdf / 2, w - 2 * mdf, mdf);
                                } else if (w >= 300) {
                                    if (activeDividers === 3) {
                                        drawMDF(x + mdf, y + h / 2 - mdf / 2, w / 4 - mdf * 1.5, mdf);
                                        drawMDF(x + w / 4 + mdf / 2, y + h / 2 - mdf / 2, w / 4 - mdf, mdf);
                                        drawMDF(x + w / 2 + mdf / 2, y + h / 2 - mdf / 2, w / 4 - mdf, mdf);
                                        drawMDF(x + 3 * w / 4 + mdf / 2, y + h / 2 - mdf / 2, w / 4 - mdf * 1.5, mdf);
                                    } else if (activeDividers === 1) {
                                        drawMDF(x + mdf, y + h / 2 - mdf / 2, w / 2 - mdf * 1.5, mdf);
                                        drawMDF(x + w / 2 + mdf / 2, y + h / 2 - mdf / 2, w / 2 - mdf * 1.5, mdf);
                                    } else {
                                        drawMDF(x + mdf, y + h / 2 - mdf / 2, w - 2 * mdf, mdf);
                                    }
                                }
                            } else if (cab.kind === 'WALL') {
                                const yPosList = cab.height_mm > 700 ? [h / 3, 2 * h / 3] : [h / 2];
                                yPosList.forEach(yOffset => {
                                    if (activeDividers === 3) {
                                        drawMDF(x + mdf, y + yOffset - mdf / 2, w / 4 - mdf * 1.5, mdf);
                                        drawMDF(x + w / 4 + mdf / 2, y + yOffset - mdf / 2, w / 4 - mdf, mdf);
                                        drawMDF(x + w / 2 + mdf / 2, y + yOffset - mdf / 2, w / 4 - mdf, mdf);
                                        drawMDF(x + 3 * w / 4 + mdf / 2, y + yOffset - mdf / 2, w / 4 - mdf * 1.5, mdf);
                                    } else if (activeDividers === 1) {
                                        drawMDF(x + mdf, y + yOffset - mdf / 2, w / 2 - mdf * 1.5, mdf);
                                        drawMDF(x + w / 2 + mdf / 2, y + yOffset - mdf / 2, w / 2 - mdf * 1.5, mdf);
                                    } else {
                                        drawMDF(x + mdf, y + yOffset - mdf / 2, w - 2 * mdf, mdf);
                                    }
                                });
                            }

                            // Middle vertical dividers
                            if (activeDividers === 3) {
                                drawMDF(x + w / 4 - mdf / 2, y + mdf, mdf, h - 2 * mdf);
                                drawMDF(x + w / 2 - mdf / 2, y + mdf, mdf, h - 2 * mdf);
                                drawMDF(x + 3 * w / 4 - mdf / 2, y + mdf, mdf, h - 2 * mdf);
                            } else if (activeDividers === 1) {
                                drawMDF(x + w / 2 - mdf / 2, y + mdf, mdf, h - 2 * mdf);
                            }

                            if (cab.kind === 'BASE') {
                                // Ayakları çiz
                                g.appendChild(createSVGElem("rect", { x: x + 20 * currentScale, y: y + h, width: 10 * currentScale, height: legH_mm * currentScale, fill: "#334155", "pointer-events": "none" }));
                                g.appendChild(createSVGElem("rect", { x: x + w - 30 * currentScale, y: y + h, width: 10 * currentScale, height: legH_mm * currentScale, fill: "#334155", "pointer-events": "none" }));
                            }
                        } else if (cab.kind === 'FILLER') {
                            rect.style.fill = "transparent";
                            rect.style.stroke = "transparent";
                        }
                    }

                    if (cab.kind === 'APPL') {
                        // Invisible placeholder for appl
                    } else if (w > 20) {
                        const txt = createSVGElem("text", { x: x + w / 2, y: y + h / 2, class: "text-label", "pointer-events": "none" });
                        let kindText = cab.has_drawers ? 'ÇKM' : (cab.kind === 'BASE' ? 'ALT' : cab.kind === 'WALL' ? 'ÜST' : cab.kind === 'TALL' ? 'BOY' : cab.kind === 'FILLER' ? 'KÖR' : cab.kind);
                        txt.textContent = (cab.code ? "[" + cab.code + "] " : "") + kindText;
                        g.appendChild(txt);

                        // Ölçüleri Yazdır
                        // Ölçüleri Yazdır
                        if (showDimensions) {
                            const dimY = cab.kind === 'WALL' ? y - 10 : y + h + 15;
                            const isLocked = cab.is_locked ? "bold" : "normal";
                            const txtDeco = cab.is_locked ? "underline" : "none";
                            const dimTxt = createSVGElem("text", {
                                x: x + w / 2, y: dimY, class: "text-label interact-dim",
                                "font-size": "13px", fill: "var(--primary)",
                                "font-weight": isLocked,
                                "text-decoration": txtDeco,
                                "cursor": "pointer"
                            });
                            dimTxt.textContent = `${cab.width_mm}`;
                            dimTxt.onclick = (e) => {
                                e.stopPropagation();
                                openEditPopover(cab, e.pageX, e.pageY);
                            };

                            g.appendChild(dimTxt);

                            // Ölçü çizgisi
                            const lineY = cab.kind === 'WALL' ? y - 2 : y + h + 2;
                            g.appendChild(createSVGElem("line", { x1: x, y1: lineY, x2: x + w, y2: lineY, stroke: "var(--primary)", "stroke-width": 1, "stroke-dasharray": "2", "pointer-events": "none" }));
                        }
                    }
                    svg.appendChild(g);
                });

                // Draw Countertop Line across BASE cabinets (40mm thickness)
                const ctHeight = 40 * currentScale;
                const ctY = floorY - ((legH_mm + project.base_height) * currentScale) - ctHeight;
                const ct = createSVGElem("rect", { x: 0, y: ctY, width: seg.length_mm * currentScale, height: ctHeight, fill: "#facc15", opacity: 0.8, "pointer-events": "none" });
                if (showFrontView) {
                    svg.appendChild(ct);
                }

                if (showFrontView) {
                    // Draw Draggable Appliances
                    const segAppl = appliances.filter(a => a.segment === seg.id);
                    segAppl.forEach(appl => {
                        const w = appl.width_mm * currentScale;
                        let h;

                        // Yükseklik özel girilmişse o kullanılır, yoksa varsayılan
                        if (appl.height_mm) {
                            h = appl.height_mm * currentScale;
                        } else {
                            if (appl.type === 'FRIDGE' || appl.type === 'TALL') h = 2000 * currentScale;
                            else if (appl.type === 'HOOD') h = 300 * currentScale;
                            else if (appl.type === 'DW') h = (project.base_height + legH_mm) * currentScale; // Fills gap from floor to counter
                            else h = project.base_height * currentScale; // OVEN, SINK
                        }

                        let x = appl.start_mm * currentScale;
                        let y;

                        if (appl.type === 'HOOD') {
                            y = floorY - ((legH_mm + project.base_height + 40 + (project.gap_height || 600)) * currentScale) - h;
                        } else if (appl.type === 'FRIDGE' || appl.type === 'DW') {
                            y = floorY - h;
                        } else {
                            y = floorY - (legH_mm * currentScale) - h;
                        }

                        const g = createSVGElem("g", {});

                        // Draw visual
                        drawApplianceVisual(g, appl.type, w, h, x, y);

                        // Grab event catcher (invisible rect on top)
                        const catcher = createSVGElem("rect", { x, y, width: w, height: h, fill: "transparent", cursor: "grab" });
                        catcher.onmousedown = (e) => {
                            draggedApplId = appl.id;
                            dragStartX = e.clientX;
                            initialApplStartMm = appl.start_mm;
                            currentScale = svgWidth / seg.length_mm;
                            currentMaxLimit = seg.length_mm - appl.width_mm;
                            e.target.style.cursor = "grabbing";

                            // Find paired appliance (OVEN <-> HOOD) for visual syncing
                            draggedPairedApplId = null;
                            if (appl.type === 'OVEN') {
                                const pair = appliances.find(a => a.segment === appl.segment && a.type === 'HOOD' && a.start_mm === appl.start_mm);
                                if (pair) draggedPairedApplId = pair.id;
                            } else if (appl.type === 'HOOD') {
                                const pair = appliances.find(a => a.segment === appl.segment && a.type === 'OVEN' && a.start_mm === appl.start_mm);
                                if (pair) draggedPairedApplId = pair.id;
                            }
                        };

                        catcher.oncontextmenu = (e) => {
                            e.preventDefault();
                            openApplEditPopover(appl, e.pageX, e.pageY);
                        };

                        catcher.ondblclick = async (e) => {
                            if (confirm('Bu beyaz eşyayı/aksesuarı silmek istiyor musunuz?')) {
                                try {
                                    await apiRequest(`/api/appliances/${appl.id}/`, 'DELETE');
                                    await apiRequest(`/api/projects/${projectId}/generate/`, 'POST');
                                    await reloadData();
                                    showAlert('Silindi', true);
                                } catch (err) { showAlert(err.message); }
                            }
                        };
                        g.appendChild(catcher);

                        svg.appendChild(g);
                    });
                }

                wrap.appendChild(svg);
                area.appendChild(wrap);
            });
        }

        // Drag & Drop Handlers
        document.addEventListener('mousemove', e => {
            if (draggedApplId) {
                const dx = e.clientX - dragStartX;
                const dx_mm = dx / (currentScale * panZoomState.zoom);
                let newStart = initialApplStartMm + dx_mm;
                if (newStart < 0) newStart = 0;
                if (newStart > currentMaxLimit) newStart = currentMaxLimit;

                const appl = appliances.find(a => a.id === draggedApplId);

                // Kullanıcı "eşyaların atlayıp yer değiştirebilmesini" istediğinden
                // anlık çarpışma kontrolü iptal edildi. Böylece cihazlar diğer
                // cihazların üzerinden atlayabilir.

                appl.start_mm = Math.round(newStart);
                if (draggedPairedApplId) {
                    const pairedAppl = appliances.find(a => a.id === draggedPairedApplId);
                    if (pairedAppl) pairedAppl.start_mm = Math.round(newStart);
                }
                draw2D();
            }
        });

        document.addEventListener('mouseup', async () => {
            if (draggedApplId) {
                const appl = appliances.find(a => a.id === draggedApplId);
                const isMoved = Math.abs(appl.start_mm - initialApplStartMm) > 0;

                draggedApplId = null;
                draggedPairedApplId = null;

                if (isMoved) {
                    try {
                        await apiRequest(`/api/appliances/${appl.id}/`, 'PATCH', { start_mm: appl.start_mm });
                        // Automatically regenerate
                        await apiRequest(`/api/projects/${projectId}/generate/`, 'POST');
                        await reloadData();
                    } catch (e) {
                        showAlert("Çakışma veya geçersiz konum. Eski konuma dönüldü.");
                        await reloadData();
                    }
                }
            }
        });

        // Context Menu for Drawer
        const ctxMenu = document.getElementById('cab-ctx');
        function showContext(e, cab) {
            e.preventDefault();
            selectedCabId = cab.id;
            ctxMenu.style.left = e.pageX + 'px';
            ctxMenu.style.top = e.pageY + 'px';
            ctxMenu.style.display = 'block';

            const btn = document.getElementById('btn-ctx-drawer');
            btn.textContent = cab.has_drawers ? "Kapaklı Yap" : "Çekmeceli Yap";
            btn.style.display = cab.kind === 'BASE' ? 'block' : 'none';
            btn.onclick = async () => {
                ctxMenu.style.display = 'none';
                await apiRequest(`/api/cabinets/${cab.id}/`, 'PATCH', { has_drawers: !cab.has_drawers });
                await reloadData();
            };

            const setDoorStyle = async (newStyle) => {
                ctxMenu.style.display = 'none';
                await apiRequest(`/api/cabinets/${cab.id}/`, 'PATCH', { door_style: newStyle });
                await reloadData();
            };

            document.getElementById('btn-ctx-door-auto').onclick = () => setDoorStyle('AUTO');
            document.getElementById('btn-ctx-door-1').onclick = () => setDoorStyle('1');
            document.getElementById('btn-ctx-door-2').onclick = () => setDoorStyle('2');
            document.getElementById('btn-ctx-door-4').onclick = () => setDoorStyle('4');

            const setPartitionStyle = async (newStyle) => {
                ctxMenu.style.display = 'none';
                await apiRequest(`/api/cabinets/${cab.id}/`, 'PATCH', { partition_style: newStyle });
                await reloadData();
            };

            document.getElementById('btn-ctx-mod-auto').onclick = () => setPartitionStyle('AUTO');
            document.getElementById('btn-ctx-mod-1').onclick = () => setPartitionStyle('1');
            document.getElementById('btn-ctx-mod-2').onclick = () => setPartitionStyle('2');
            document.getElementById('btn-ctx-mod-4').onclick = () => setPartitionStyle('4');

            const btnEdit = document.getElementById('btn-ctx-edit');

            const btnSplit = document.getElementById('btn-ctx-split');
            if (btnSplit) {
                btnSplit.onclick = async () => {
                    ctxMenu.style.display = 'none';
                    try {
                        await apiRequest(`/api/cabinets/${cab.id}/split/`, 'POST');
                        await reloadData();
                    } catch (e) {
                        showAlert('Bölme hatası: ' + e.message);
                    }
                };
            }

            const btnMergeNext = document.getElementById('btn-ctx-merge-next');
            if (btnMergeNext) {
                btnMergeNext.onclick = async () => {
                    ctxMenu.style.display = 'none';
                    try {
                        await apiRequest(`/api/cabinets/${cab.id}/merge_next/`, 'POST');
                        await reloadData();
                    } catch (e) {
                        showAlert('Birleştirme hatası: Sağda uygun dolap yok.');
                    }
                };
            }

            const btnMergePrev = document.getElementById('btn-ctx-merge-prev');
            if (btnMergePrev) {
                btnMergePrev.onclick = async () => {
                    ctxMenu.style.display = 'none';
                    try {
                        await apiRequest(`/api/cabinets/${cab.id}/merge_prev/`, 'POST');
                        await reloadData();
                    } catch (e) {
                        showAlert('Birleştirme hatası: Solda uygun dolap yok.');
                    }
                };
            }
            btnEdit.onclick = () => {
                ctxMenu.style.display = 'none';
                openEditPopover(cab, e.pageX, e.pageY);
            };

            const btnDelete = document.getElementById('btn-ctx-delete');
            if (btnDelete) {
                btnDelete.onclick = async () => {
                    ctxMenu.style.display = 'none';
                    if (confirm('Bu dolabı silmek istiyor musunuz?')) {
                        await saveHistoryState();
                        await apiRequest(`/api/cabinets/${cab.id}/`, 'DELETE');
                        await apiRequest(`/api/projects/${projectId}/generate/`, 'POST');
                        await reloadData();
                        showAlert('Dolap silindi.', true);
                    }
                };
            }
        }
        document.addEventListener('click', e => {
            if (!e.target.closest('#cab-ctx') && e.target.tagName !== 'rect') {
                ctxMenu.style.display = 'none';
            }
            if (!e.target.closest('#edit-popover') && !e.target.classList.contains('interact-dim') && e.target.id !== 'btn-ctx-edit') {
                const pop = document.getElementById('edit-popover');
                if (pop) pop.style.display = 'none';
            }
        });

        let editingCabId = null;
        let editingCabData = null;

        function openEditPopover(cab, x, y) {
            document.getElementById('cab-ctx').style.display = 'none';
            editingCabId = cab.id;
            editingCabData = cab;

            const pop = document.getElementById('edit-popover');
            document.getElementById('pop-width').value = cab.width_mm;
            document.getElementById('pop-label').value = cab.label || '';

            pop.style.left = x + 'px';
            pop.style.top = y + 'px';
            pop.style.display = 'block';
        }

        document.getElementById('pop-cancel').onclick = () => {
            document.getElementById('edit-popover').style.display = 'none';
        };

        document.getElementById('pop-save').onclick = async () => {
            const pop = document.getElementById('edit-popover');
            pop.style.display = 'none';

            const newWidth = parseInt(document.getElementById('pop-width').value);
            const newLabel = document.getElementById('pop-label').value;
            if (!newWidth || isNaN(newWidth) || !editingCabData) return;

            const cab = editingCabData;

            let sameLevelAppls = [];
            let sameLevelLockedCabs = cabinets.filter(c => c.segment === cab.segment && c.is_locked && c.id !== cab.id);
            if (cab.kind === 'WALL') {
                sameLevelAppls = appliances.filter(a => a.segment === cab.segment && (a.type === 'HOOD' || a.type === 'FRIDGE' || a.type === 'TALL'));
                sameLevelLockedCabs = sameLevelLockedCabs.filter(c => c.kind === 'WALL' || c.kind === 'TALL');
            } else {
                sameLevelAppls = appliances.filter(a => a.segment === cab.segment && a.type !== 'HOOD');
                sameLevelLockedCabs = sameLevelLockedCabs.filter(c => c.kind === 'BASE' || c.kind === 'TALL' || c.kind === 'APPL');
            }

            let obstacles = [...sameLevelAppls.map(a => ({ start: a.start_mm, end: a.start_mm + a.width_mm })),
            ...sameLevelLockedCabs.map(c => ({ start: c.start_mm, end: c.start_mm + c.width_mm }))];

            let seg = segments.find(s => s.id === cab.segment);
            let gap_start = 0;
            let gap_end = seg.length_mm;

            for (let o of obstacles) {
                if (o.end <= cab.start_mm && o.end > gap_start) gap_start = o.end;
            }
            let cabEnd = cab.start_mm + cab.width_mm;
            for (let o of obstacles) {
                if (o.start >= cabEnd && o.start < gap_end) gap_end = o.start;
            }

            let final_start = cab.start_mm;
            if (final_start + newWidth > gap_end) {
                final_start = gap_end - newWidth;
            }
            if (final_start < gap_start) {
                showAlert('Bu ölçüdeki bir dolap bu boşluğa sığmaz!');
                return;
            }

            await saveHistoryState();
            await apiRequest(`/api/cabinets/${cab.id}/`, 'PATCH', {
                width_mm: newWidth,
                start_mm: final_start,
                label: newLabel,
                is_locked: true
            });
            await apiRequest(`/api/projects/${projectId}/generate/`, 'POST');
            await reloadData();
        };

        // ---------------- THREE JS 3D VIEWER ----------------
        let renderer, scene, camera, controls;

        function init3D() {
            const container = document.getElementById('canvas-container');
            container.innerHTML = '';

            // Setup
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf8fafc);

            const w = container.clientWidth;
            const h = 500; // Fixed height in tab

            camera = new THREE.PerspectiveCamera(45, w / h, 1, 10000);
            camera.position.set(0, 1500, 4000);

            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(w, h);
            renderer.shadowMap.enabled = true;
            container.appendChild(renderer.domElement);

            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.target.set(1500, 1000, 0);
            controls.update();

            // Lights
            const light = new THREE.HemisphereLight(0xffffff, 0x444444, 0.8);
            light.position.set(0, 3000, 0);
            scene.add(light);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.5);
            dirLight.position.set(0, 2000, 2000);
            dirLight.castShadow = true;
            scene.add(dirLight);

            // Floor
            const planeGeo = new THREE.PlaneGeometry(8000, 8000);
            const planeMat = new THREE.MeshLambertMaterial({ color: 0xe2e8f0 });
            const plane = new THREE.Mesh(planeGeo, planeMat);
            plane.rotation.x = -Math.PI / 2;
            plane.receiveShadow = true;
            scene.add(plane);

            // Materials
            const matBase = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.1, metalness: 0.1 });
            const matDrawer = new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.1, metalness: 0.1 });
            const matWall = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.1, metalness: 0.1 });
            const matCounter = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.5, metalness: 0.2 }); // Siyah tezgah
            const matHandle = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.4, metalness: 0.8 });

            // Appliance materials
            const matSilver = new THREE.MeshStandardMaterial({ color: 0xb5bcc2, metalness: 0.9, roughness: 0.3 }); // Inox renk
            const matDark = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.6, roughness: 0.4 });
            const matGlass = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9, roughness: 0.1, transparent: true, opacity: 0.8 });
            const matRoomWall = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.9, metalness: 0.0 });
            const matSinkHole = new THREE.MeshStandardMaterial({ color: 0x0a0a0a, roughness: 0.9, metalness: 0.1 });

            function create3DCabinet(cab) {
                const group = new THREE.Group();

                // If this is an appliance housing (except Evye which needs doors), don't draw the solid cabinet block to let the appliance mesh show through.
                if (cab.label && (cab.label.includes('Fırın') || cab.label.includes('Bulaşık') || cab.label.includes('Buzdolabı'))) {
                    // Just return an empty group, or maybe a back panel. Empty group is fine since appliance mesh will take the space.
                    return group;
                }

                const bodyGeo = new THREE.BoxGeometry(cab.width_mm, cab.height_mm, cab.depth_mm);
                let bodyMat = cab.kind === 'WALL' ? matWall : matBase;
                const body = new THREE.Mesh(bodyGeo, bodyMat);
                body.castShadow = true; body.receiveShadow = true;
                group.add(body);

                if (cab.kind === 'BASE' || (cab.kind === 'FILLER' && cab.depth_mm > 400)) {
                    const legRadius = 20;
                    const legGeo = new THREE.CylinderGeometry(legRadius, legRadius, 100, 16);
                    const legMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.8 });

                    const legY = -cab.height_mm / 2 - 50;

                    if (cab.width_mm >= 60) {
                        const offsets = [
                            { x: -cab.width_mm / 2 + 25, z: cab.depth_mm / 2 - 30 },
                            { x: cab.width_mm / 2 - 25, z: cab.depth_mm / 2 - 30 },
                            { x: -cab.width_mm / 2 + 25, z: -cab.depth_mm / 2 + 30 },
                            { x: cab.width_mm / 2 - 25, z: -cab.depth_mm / 2 + 30 }
                        ];
                        offsets.forEach(pos => {
                            const leg = new THREE.Mesh(legGeo, legMat);
                            leg.position.set(pos.x, legY, pos.z);
                            group.add(leg);
                        });
                    }
                }

                if (cab.kind === 'FILLER') return group;

                const frontZ = cab.depth_mm / 2 + 1;
                const doorThickness = 18;
                const gap = 3;

                const matFront = cab.has_drawers ? matDrawer : (cab.kind === 'WALL' ? matWall : matBase);

                if (cab.has_drawers) {
                    const dHeight = (cab.height_mm - gap * 4) / 3;
                    for (let i = 0; i < 3; i++) {
                        const dGeo = new THREE.BoxGeometry(cab.width_mm - gap * 2, dHeight, doorThickness);
                        const dMesh = new THREE.Mesh(dGeo, matFront);
                        dMesh.castShadow = true;
                        const dY = -cab.height_mm / 2 + gap + dHeight / 2 + i * (dHeight + gap);
                        dMesh.position.set(0, dY, frontZ + doorThickness / 2);
                        group.add(dMesh);

                        // handle
                        const hGeo = new THREE.BoxGeometry(100, 10, 20);
                        const hMesh = new THREE.Mesh(hGeo, matHandle);
                        hMesh.castShadow = true;
                        hMesh.position.set(0, dY + dHeight / 4, frontZ + doorThickness + 10);
                        group.add(hMesh);
                    }
                } else {
                    const doors = cab.width_mm >= 600 ? 2 : 1;
                    const dWidth = (cab.width_mm - gap * (doors + 1)) / doors;
                    const dHeight = cab.height_mm - gap * 2;

                    for (let i = 0; i < doors; i++) {
                        const dGeo = new THREE.BoxGeometry(dWidth, dHeight, doorThickness);
                        const dMesh = new THREE.Mesh(dGeo, matFront);
                        dMesh.castShadow = true;
                        const dX = doors === 1 ? 0 : (i === 0 ? -cab.width_mm / 4 : cab.width_mm / 4);
                        dMesh.position.set(dX, 0, frontZ + doorThickness / 2);
                        group.add(dMesh);

                        // handle
                        const hGeo = new THREE.BoxGeometry(12, 160, 25);
                        const hMesh = new THREE.Mesh(hGeo, matHandle);
                        hMesh.castShadow = true;

                        let hX = 0;
                        if (doors === 1) hX = cab.width_mm / 2 - 30 - gap;
                        else hX = i === 0 ? dX + dWidth / 2 - 20 : dX - dWidth / 2 + 20;

                        const hY = cab.kind === 'WALL' ? -dHeight / 2 + 100 : dHeight / 2 - 100;
                        hMesh.position.set(hX, hY, frontZ + doorThickness + 12);
                        group.add(hMesh);
                    }
                }
                return group;
            }

            function create3DAppliance(appl, h, d) {
                const group = new THREE.Group();
                const w = appl.width_mm;

                if (appl.type === 'FRIDGE') {
                    const bodyGeo = new THREE.BoxGeometry(w, h, d);
                    const body = new THREE.Mesh(bodyGeo, matSilver);
                    body.castShadow = true; body.receiveShadow = true;
                    group.add(body);

                    const zGap = d / 2 + 1;
                    const d1h = h * 0.65;
                    const d2h = h * 0.33;

                    const topDoorGeo = new THREE.BoxGeometry(w - 4, d1h, 40);
                    const topDoor = new THREE.Mesh(topDoorGeo, matSilver);
                    topDoor.castShadow = true;
                    topDoor.position.set(0, h / 2 - d1h / 2 - 2, zGap + 20);
                    group.add(topDoor);

                    const botDoorGeo = new THREE.BoxGeometry(w - 4, d2h, 40);
                    const botDoor = new THREE.Mesh(botDoorGeo, matSilver);
                    botDoor.castShadow = true;
                    botDoor.position.set(0, -h / 2 + d2h / 2 + 2, zGap + 20);
                    group.add(botDoor);

                    const hGeo = new THREE.BoxGeometry(15, 300, 30);
                    const tHandle = new THREE.Mesh(hGeo, matDark);
                    tHandle.position.set(-w / 2 + 40, h / 2 - d1h / 2, zGap + 40 + 15);
                    group.add(tHandle);

                    const bHandle = new THREE.Mesh(hGeo, matDark);
                    bHandle.position.set(-w / 2 + 40, -h / 2 + d2h / 2 + 150, zGap + 40 + 15);
                    group.add(bHandle);
                }
                else if (appl.type === 'OVEN') {
                    const bodyGeo = new THREE.BoxGeometry(w, h, d);
                    const body = new THREE.Mesh(bodyGeo, matSilver);
                    group.add(body);

                    const zGap = d / 2 + 2;
                    const cpGeo = new THREE.BoxGeometry(w, 80, 5);
                    const cp = new THREE.Mesh(cpGeo, matSilver);
                    cp.position.set(0, h / 2 - 40, zGap);
                    group.add(cp);

                    const winGeo = new THREE.BoxGeometry(w - 60, h - 140, 6);
                    const win = new THREE.Mesh(winGeo, matGlass);
                    win.position.set(0, -30, zGap);
                    group.add(win);

                    const handleGeo = new THREE.BoxGeometry(w - 80, 15, 30);
                    const handle = new THREE.Mesh(handleGeo, matSilver);
                    // Elevated handle so it might clear any overlaps
                    handle.position.set(0, h / 2 - 110, zGap + 20);
                    group.add(handle);
                }
                else if (appl.type === 'DW') {
                    const bodyGeo = new THREE.BoxGeometry(w, h, d);
                    const body = new THREE.Mesh(bodyGeo, matSilver);
                    group.add(body);

                    const zGap = d / 2 + 2;
                    const cpGeo = new THREE.BoxGeometry(w, 120, 10);
                    const cp = new THREE.Mesh(cpGeo, matSilver);
                    cp.position.set(0, h / 2 - 60, zGap);
                    group.add(cp);

                    // Thicker door standing out
                    const doorGeo = new THREE.BoxGeometry(w - 4, h - 130, 20);
                    const door = new THREE.Mesh(doorGeo, matSilver);
                    door.position.set(0, -60, zGap + 5);
                    group.add(door);

                    const handleGeo = new THREE.BoxGeometry(150, 15, 25);
                    const handle = new THREE.Mesh(handleGeo, matHandle);
                    handle.position.set(0, h / 2 - 60, zGap + 20);
                    group.add(handle);
                }
                else if (appl.type === 'HOOD') {
                    const canopyGeo = new THREE.BoxGeometry(w, 80, d);
                    const canopy = new THREE.Mesh(canopyGeo, matSilver);
                    canopy.position.set(0, -h / 2 + 40, 0);
                    group.add(canopy);

                    const chimneyGeo = new THREE.BoxGeometry(w * 0.4, h - 80, d * 0.5);
                    const chimney = new THREE.Mesh(chimneyGeo, matSilver);
                    chimney.position.set(0, 40, -d / 4);
                    group.add(chimney);
                }
                else if (appl.type === 'SINK') {
                    // Evye dudağı (Tezgah üstüne oturan metalik kısım)
                    const lipGeo = new THREE.BoxGeometry(w - 40, 6, d - 40);
                    const lip = new THREE.Mesh(lipGeo, matSilver);
                    // absolute target: h + 40 (countertop top). relative: h/2 + 40.
                    lip.position.set(0, h / 2 + 39, 0);
                    group.add(lip);

                    // Evye havuzu (Derinlik efekti için siyah alan, lip'in iç ve üst kısmı)
                    const holeGeo = new THREE.BoxGeometry(w - 60, 4, d - 60);
                    const hole = new THREE.Mesh(holeGeo, matSinkHole);
                    hole.position.set(0, h / 2 + 40.5, 0);
                    group.add(hole);

                    // Musluk Tabanı
                    const faucetBaseGeo = new THREE.CylinderGeometry(15, 15, 80, 16);
                    const faucetBase = new THREE.Mesh(faucetBaseGeo, matSilver);
                    faucetBase.position.set(0, h / 2 + 80, -d / 4 + 20);
                    group.add(faucetBase);

                    // Musluk Kıvrımı
                    const faucetArchGeo = new THREE.TorusGeometry(60, 10, 16, 32, Math.PI);
                    const faucetArch = new THREE.Mesh(faucetArchGeo, matSilver);
                    faucetArch.position.set(0, h / 2 + 140, -d / 4 + 80);
                    faucetArch.rotation.y = Math.PI / 2;
                    group.add(faucetArch);
                } else {
                    const bodyGeo = new THREE.BoxGeometry(w, h, d);
                    const body = new THREE.Mesh(bodyGeo, matSilver);
                    group.add(body);
                }
                return group;
            }

            // Build Segments
            segments.forEach((seg, i) => {
                const segCabs = cabinets.filter(c => c.segment === seg.id);
                const segAppls = appliances.filter(a => a.segment === seg.id);

                const isSegB = (seg.name === 'B');

                if (isSegB) {
                    const bWallLen = seg.length_mm + project.base_depth;
                    const roomWallGeoB = new THREE.BoxGeometry(bWallLen, 2500, 200);
                    const roomWallMeshB = new THREE.Mesh(roomWallGeoB, matRoomWall);
                    roomWallMeshB.receiveShadow = true;
                    roomWallMeshB.rotation.y = -Math.PI / 2;
                    roomWallMeshB.position.set(-100, 1250, (bWallLen / 2) - project.base_depth);
                    scene.add(roomWallMeshB);
                } else {
                    const roomWallGeo = new THREE.BoxGeometry(seg.length_mm, 2500, 200);
                    const roomWallMesh = new THREE.Mesh(roomWallGeo, matRoomWall);
                    roomWallMesh.receiveShadow = true;
                    roomWallMesh.position.set(seg.length_mm / 2, 1250, -200 / 2 - project.base_depth);
                    scene.add(roomWallMesh);
                }

                // Add Countertop for the segment
                const counterZ = -(project.base_depth / 2);
                let counterLength = seg.length_mm;

                const counterGeo = new THREE.BoxGeometry(counterLength, 40, project.base_depth);
                const counterMesh = new THREE.Mesh(counterGeo, matCounter);
                counterMesh.castShadow = true; counterMesh.receiveShadow = true;

                let cx = counterLength / 2;

                if (isSegB) {
                    counterMesh.rotation.y = -Math.PI / 2;
                    counterMesh.position.set(project.base_depth / 2, project.base_height + 100 + 20, cx);
                } else {
                    counterMesh.position.set(cx, project.base_height + 100 + 20, counterZ);
                }
                scene.add(counterMesh);

                segCabs.forEach(cab => {
                    if (cab.kind === 'APPL') return;

                    const mesh = create3DCabinet(cab);

                    let y = 100 + cab.height_mm / 2;
                    if (cab.kind === 'WALL' || (cab.kind === 'FILLER' && cab.depth_mm < 400)) {
                        y = 100 + project.base_height + 40 + (project.gap_height || 600) + (cab.height_mm / 2);
                    }

                    let x = cab.start_mm + (cab.width_mm / 2);
                    let zCenter = -(cab.depth_mm / 2);

                    if (cab.kind === 'WALL') {
                        zCenter = -(project.base_depth) + (cab.depth_mm / 2);
                    }

                    if (isSegB) {
                        let bCenter = project.base_depth - (cab.depth_mm / 2);
                        if (cab.kind === 'WALL') {
                            bCenter = cab.depth_mm / 2;
                        }
                        mesh.rotation.y = -Math.PI / 2;
                        mesh.position.set(bCenter, y, x);
                    } else {
                        mesh.position.set(x, y, zCenter);
                    }

                    scene.add(mesh);
                });

                segAppls.forEach(appl => {
                    const w = appl.width_mm;
                    let h = project.base_height;
                    const d = project.base_depth;

                    if (appl.type === 'FRIDGE' || appl.type === 'TALL') h = 2000;
                    else if (appl.type === 'HOOD') h = 300;
                    else if (appl.type === 'DW') h = project.base_height + 100;

                    const mesh = create3DAppliance(appl, h, d);

                    let y = 100 + h / 2;
                    if (appl.type === 'FRIDGE' || appl.type === 'TALL' || appl.type === 'DW') {
                        y = h / 2;
                    } else if (appl.type === 'HOOD') {
                        y = 100 + project.base_height + 40 + (project.gap_height || 600) + (h / 2);
                    }

                    let x = appl.start_mm + (w / 2);
                    let zCenter = -(d / 2);

                    if (appl.type === 'HOOD') {
                        zCenter = -(project.base_depth) + (320 / 2);
                    }

                    if (isSegB) {
                        let bCenter = project.base_depth - (d / 2);
                        if (appl.type === 'HOOD') {
                            bCenter = 320 / 2;
                        }
                        mesh.rotation.y = -Math.PI / 2;
                        mesh.position.set(bCenter, y, x);
                    } else {
                        mesh.position.set(x, y, zCenter);
                    }
                    scene.add(mesh);
                });
            });

            // Loop
            function animate() {
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }
            animate();
        }

        async function loadCutlist() {
            const parts = await apiRequest(`/api/projects/${projectId}/cutlist/`);
            const tbody = document.getElementById('cutlist-body');
            tbody.innerHTML = '';
            parts.forEach(p => {
                tbody.innerHTML += `<tr><td>${p.cabinet}</td><td>${p.part_name}</td><td>${p.qty}</td><td>${p.length} x ${p.width}</td><td>${p.thickness}</td></tr>`;
            });
        }

        document.getElementById('btn-csv').addEventListener('click', () => { window.open(`/api/projects/${projectId}/cutlist_csv/`, '_blank'); });

        async function loadProjectsList() {
            try {
                const projs = await apiRequest('/api/projects/');
                const sel = document.getElementById('saved-projects-list');
                const currVal = sel.value;
                sel.innerHTML = '<option value="">-- Proje Seçin --</option>';
                projs.forEach(p => {
                    sel.appendChild(new Option(p.name + (p.layout_type ? ` (${p.layout_type})` : ''), p.id));
                });
                if (currVal) sel.value = currVal;
            } catch (e) {
                console.error('Error loading projects:', e);
            }
        }

        let selectedApplPopover = null;
        function openApplEditPopover(appl, px, py) {
            selectedApplPopover = appl;
            const pop = document.getElementById('appl-edit-popover');
            pop.style.left = px + 'px';
            pop.style.top = py + 'px';
            pop.style.display = 'block';

            document.getElementById('appl-pop-width').value = appl.width_mm;
            document.getElementById('appl-pop-height').value = appl.height_mm || '';
        }

        document.getElementById('appl-pop-cancel').onclick = () => {
            document.getElementById('appl-edit-popover').style.display = 'none';
        };

        document.getElementById('appl-pop-save').onclick = async () => {
            if (!selectedApplPopover) return;
            const w = parseInt(document.getElementById('appl-pop-width').value) || 0;
            const hVal = document.getElementById('appl-pop-height').value;
            const h = hVal ? parseInt(hVal) : null;

            if (w <= 0) return showAlert('Geçerli bir genişlik girin.');

            try {
                // If it's an oven, update paired hood width too
                // If it's a hood, update paired oven width too
                let pairedApplId = null;
                if (selectedApplPopover.type === 'OVEN') {
                    const pair = appliances.find(a => a.segment === selectedApplPopover.segment && a.type === 'HOOD' && a.start_mm === selectedApplPopover.start_mm);
                    if (pair) pairedApplId = pair.id;
                } else if (selectedApplPopover.type === 'HOOD') {
                    const pair = appliances.find(a => a.segment === selectedApplPopover.segment && a.type === 'OVEN' && a.start_mm === selectedApplPopover.start_mm);
                    if (pair) pairedApplId = pair.id;
                }

                await apiRequest(`/api/appliances/${selectedApplPopover.id}/`, 'PATCH', {
                    width_mm: w,
                    height_mm: h
                });

                if (pairedApplId) {
                    await apiRequest(`/api/appliances/${pairedApplId}/`, 'PATCH', { width_mm: w });
                }

                document.getElementById('appl-edit-popover').style.display = 'none';
                await apiRequest(`/api/projects/${projectId}/generate/`, 'POST');
                await reloadData();
            } catch (err) {
                showAlert(err.message);
            }
        };

        window.addEventListener('DOMContentLoaded', loadProjectsList);

        document.getElementById('btn-load-project').addEventListener('click', async () => {
            const pid = document.getElementById('saved-projects-list').value;
            if (!pid) return showAlert('Lütfen bir proje seçin.');

            projectId = pid;
            const ws = document.getElementById('panel-workspace');
            ws.style.opacity = '1';
            ws.style.pointerEvents = 'auto';
            document.getElementById('toolbar').style.display = 'flex';

            try {
                await reloadData();
                document.getElementById('current-project-title').textContent = project.name;

                if (project.layout_type === 'L') {
                    document.getElementById('group-seg-b').style.display = 'block';
                    document.getElementById('seg-len-b').required = true;
                } else {
                    document.getElementById('group-seg-b').style.display = 'none';
                    document.getElementById('seg-len-b').required = false;
                }

                showAlert(project.name + ' yüklendi.', true);
            } catch (e) { showAlert('Proje yüklenirken hata oluştu.'); }
        });

        document.getElementById('btn-edit-project').addEventListener('click', async () => {
            const pid = document.getElementById('saved-projects-list').value;
            if (!pid) return showAlert('Lütfen düzenlemek için bir proje seçin.');

            const sel = document.getElementById('saved-projects-list');
            const currentName = sel.options[sel.selectedIndex].text.split(' (')[0];
            const newName = prompt('Yeni proje adını girin:', currentName);

            if (newName && newName.trim() !== '' && newName !== currentName) {
                try {
                    await apiRequest(`/api/projects/${pid}/`, 'PATCH', { name: newName });
                    await loadProjectsList();
                    if (projectId == pid) document.getElementById('current-project-title').textContent = newName;
                    showAlert('Proje adı güncellendi.', true);
                } catch (e) { showAlert('Güncellenirken hata oluştu.'); }
            }
        });

        document.getElementById('btn-delete-project').addEventListener('click', async () => {
            const pid = document.getElementById('saved-projects-list').value;
            if (!pid) return showAlert('Lütfen silmek için bir proje seçin.');

            if (confirm('Bu projeyi tamamen silmek istediğinize emin misiniz? Bu işlem geri alınamaz!')) {
                try {
                    await apiRequest(`/api/projects/${pid}/`, 'DELETE');
                    await loadProjectsList();
                    if (projectId == pid) {
                        location.reload(); // Reload page if currently active project is deleted
                    } else {
                        showAlert('Proje silindi.', true);
                    }
                } catch (e) { showAlert('Silinirken hata oluştu.'); }
            }
        });

        // ---------------- PAN & ZOOM SETUP ----------------
        const v2d = document.getElementById('view-2d');
        v2d.addEventListener('wheel', e => {
            if (!v2d.classList.contains('active')) return;
            e.preventDefault();
            const zoomStep = 0.05;
            if (e.deltaY < 0) panZoomState.zoom += zoomStep;
            else panZoomState.zoom -= zoomStep;
            panZoomState.zoom = Math.max(0.2, Math.min(panZoomState.zoom, 5));
            applyPanZoom();
        }, { passive: false });

        v2d.addEventListener('mousedown', e => {
            if (e.button !== 1) return; // Sadece orta tuş (tekerleğe basarak)
            e.preventDefault();
            if (e.target.closest('.cab-appl') || e.target.closest('.interact-dim') || e.target.closest('button') || e.target.closest('#cab-ctx') || e.target.closest('#edit-popover')) return;
            panZoomState.isPanning = true;
            panZoomState.startX = e.clientX - panZoomState.panX;
            panZoomState.startY = e.clientY - panZoomState.panY;
            v2d.style.cursor = 'grabbing';
        });

        document.addEventListener('mousemove', e => {
            if (panZoomState.isPanning) {
                panZoomState.panX = e.clientX - panZoomState.startX;
                panZoomState.panY = e.clientY - panZoomState.startY;
                applyPanZoom();
            }
        });

        document.addEventListener('mouseup', e => {
            if (panZoomState.isPanning) {
                panZoomState.isPanning = false;
                v2d.style.cursor = 'default';
            }
        });

    