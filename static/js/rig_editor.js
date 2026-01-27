
document.addEventListener('DOMContentLoaded', function () {
    // Nur starten, wenn Canvas existiert
    if (!document.getElementById('rigCanvas')) return;

    // Check dependencies
    if (typeof fabric === 'undefined') {
        document.getElementById('libraryContainer').innerHTML = `<div class="alert alert-danger">Fabric.js konnte nicht geladen werden! Bitte Internetverbindung prüfen (CDN).</div>`;
        return;
    }

    const showId = window.currentShowId;
    let canvas;
    try {
        canvas = new fabric.Canvas('rigCanvas', {
            backgroundColor: '#1a1a1a',
            selection: true,
            preserveObjectStacking: true
        });
    } catch (e) {
        console.error("Canvas Init Failed", e);
        document.getElementById('libraryContainer').innerHTML = `<div class="alert alert-danger">Canvas Fehler: ${e.message}</div>`;
        return;
    }

    const libraryContainer = document.getElementById('libraryContainer');
    let rigData = {};
    let visualPlan = {};
    let isSaving = false; // Flag to prevent concurrent POST requests

    // Standard-Farben für Typen
    const TYPE_COLORS = {
        spots: '#ef4444',   // red
        washes: '#3b82f6',  // blue
        beams: '#eab308',   // yellow
        blinders: '#f97316',// orange
        strobes: '#ffffff', // white
        custom: '#a855f7'   // purple
    };

    // ------------- Configuration -------------
    const METER_PX = 40; // 40px = 1m
    const GRID_SIZE = METER_PX / 2; // Snapping Grid (0.5m = 20px)
    const SNAP_ENABLED = true;
    let globalScale = 1.0;

    // Standard Symbols (Fabric Paths or Shapes)
    // Simple USITT-like representations
    // Standard Symbols (High-Fidelity Industry Designs)
    const SYMBOLS = {
        spots: (color) => {
            // USITT Profile/Spot Style: Rectangle with distinct lens and cooling fins
            const body = new fabric.Path('M -15 -20 L 15 -20 L 15 15 L -15 15 Z', { fill: 'transparent', stroke: color, strokeWidth: 2.5 });
            const nose = new fabric.Path('M -10 -20 L 10 -20 L 12 -35 L -12 -35 Z', { fill: color, opacity: 0.8 }); // Front lens/nose
            const yoke = new fabric.Path('M -20 -10 L -20 10 L 20 10 L 20 -10', { fill: 'transparent', stroke: color, strokeWidth: 1.5, opacity: 0.5 });
            const clamp = new fabric.Path('M -5 18 L 5 18 L 5 25 L -5 25 Z', { fill: color, opacity: 0.4 }); // Hook/Clamp
            return [body, nose, yoke, clamp];
        },
        washes: (color) => {
            // USITT Fresnel/Wash Style: Circular with stepped lens (Fresnel rings)
            const body = new fabric.Circle({ radius: 20, fill: 'transparent', stroke: color, strokeWidth: 2.5, originX: 'center', originY: 'center' });
            const ring1 = new fabric.Circle({ radius: 15, fill: 'transparent', stroke: color, strokeWidth: 1, opacity: 0.3 });
            const ring2 = new fabric.Circle({ radius: 10, fill: 'transparent', stroke: color, strokeWidth: 1, opacity: 0.5 });
            const center = new fabric.Circle({ radius: 5, fill: color, opacity: 0.7 });
            const barndoors = new fabric.Path('M -22 -15 L 22 -15 M -22 15 L 22 15', { stroke: color, strokeWidth: 1.5, opacity: 0.4 });
            const clamp = new fabric.Path('M -5 20 L 5 20 L 5 28 L -5 28 Z', { fill: color, opacity: 0.4 });
            return [body, ring1, ring2, center, barndoors, clamp];
        },
        beams: (color) => {
            // Beam/Par Style: Tapered body with strong center focus
            const body = new fabric.Path('M -15 15 L 15 15 L 12 -25 L -12 -25 Z', { fill: 'transparent', stroke: color, strokeWidth: 3 });
            const lens = new fabric.Circle({ radius: 8, fill: color, top: -25, originX: 'center' });
            const clamp = new fabric.Path('M -5 15 L 5 15 L 5 22 L -5 22 Z', { fill: color, opacity: 0.4 });
            return [body, lens, clamp];
        },
        blinders: (color) => {
            // Multi-cell Blinder (2-Lite or 4-Lite style)
            const frame = new fabric.Rect({ width: 45, height: 25, rx: 4, ry: 4, fill: 'transparent', stroke: color, strokeWidth: 2, originX: 'center', originY: 'center' });
            const cell1 = new fabric.Circle({ radius: 9, fill: color, left: -10, top: 0, originX: 'center', originY: 'center', opacity: 0.9 });
            const cell2 = new fabric.Circle({ radius: 9, fill: color, left: 10, top: 0, originX: 'center', originY: 'center', opacity: 0.9 });
            const clamp = new fabric.Path('M -4 12 L 4 12 L 4 18 L -4 18 Z', { fill: color, opacity: 0.4 });
            return [frame, cell1, cell2, clamp];
        },
        strobes: (color) => {
            // Modern LED Strobe (e.g., JDC1/X4 Bar style)
            const body = new fabric.Rect({ width: 50, height: 14, fill: 'transparent', stroke: color, strokeWidth: 2, originX: 'center', originY: 'center' });
            const ledLine = new fabric.Rect({ width: 46, height: 4, fill: color, originX: 'center', originY: 'center', opacity: 0.8 });
            const segments = new fabric.Path('M -15 -7 L -15 7 M 0 -7 L 0 7 M 15 -7 L 15 7', { stroke: color, strokeWidth: 1, opacity: 0.3 });
            const clamp = new fabric.Path('M -5 7 L 5 7 L 5 14 L -5 14 Z', { fill: color, opacity: 0.4 });
            return [body, ledLine, segments, clamp];
        },
        custom: (color) => {
            // Hexagon for generic/special devices
            const hex = new fabric.Path('M 0 -20 L 17 -10 L 17 10 L 0 20 L -17 10 L -17 -10 Z', { fill: 'transparent', stroke: color, strokeWidth: 2, originX: 'center', originY: 'center' });
            const center = new fabric.Circle({ radius: 4, fill: color, opacity: 0.5 });
            return [hex, center];
        }
    };

    // ------------- Data Loading -------------

    async function loadRigData() {
        try {
            const resp = await fetch(`/show/${showId}/api/get_rig`);
            const json = await resp.json();
            rigData = json.rig;
            visualPlan = json.visual_plan || {};
            renderUI();
        } catch (e) {
            console.error("Failed to load rig:", e);
            libraryContainer.innerHTML = `<div class="alert alert-danger small p-2">
                <i class="bi bi-exclamation-triangle me-2"></i>Fehler beim Laden:<br>${e.message}<br>
                <small>Server neu starten?</small>
            </div>`;
        }
    }

    // ------------- Orchestration & Rendering -------------

    function renderUI() {
        initCanvas();
        renderLibrary();
    }

    function drawGrid() {
        const majorGrid = METER_PX; // 1m
        const minorGrid = METER_PX / 2; // 0.5m
        const width = 2000;
        const height = 2000;

        // Draw Minor Grid (0.5m)
        for (let i = 0; i <= (width / minorGrid); i++) {
            canvas.add(new fabric.Line([i * minorGrid, 0, i * minorGrid, height],
                { stroke: '#1f1f1f', selectable: false, evented: false, strokeDashArray: [2, 2] }));
            canvas.add(new fabric.Line([0, i * minorGrid, width, i * minorGrid],
                { stroke: '#1f1f1f', selectable: false, evented: false, strokeDashArray: [2, 2] }));
        }

        // Draw Major Grid (1m)
        for (let i = 0; i <= (width / majorGrid); i++) {
            canvas.add(new fabric.Line([i * majorGrid, 0, i * majorGrid, height],
                { stroke: '#333', strokeWidth: 1.5, selectable: false, evented: false }));
            canvas.add(new fabric.Line([0, i * majorGrid, width, i * majorGrid],
                { stroke: '#333', strokeWidth: 1.5, selectable: false, evented: false }));
        }
    }

    function addToLibraryGrouped(groupName, items) {
        const wrapper = document.createElement('div');
        wrapper.className = 'mb-3 border border-secondary border-opacity-25 rounded p-2 bg-dark bg-opacity-25';

        const header = document.createElement('div');
        header.className = 'd-flex justify-content-between align-items-center mb-2 px-1';
        header.innerHTML = `
            <span class="small fw-bold text-light">${groupName}</span>
            <span class="badge bg-secondary text-light">${items.length}x</span>
        `;
        wrapper.appendChild(header);

        const btnRow = document.createElement('div');
        btnRow.className = 'd-grid gap-1';

        // Add Next Button
        const btnNext = document.createElement('button');
        btnNext.className = 'btn btn-outline-primary btn-sm text-start';
        btnNext.innerHTML = `<i class="bi bi-plus-lg me-2"></i>Nächstes platzieren`;
        btnNext.onclick = () => {
            const item = items[0];
            const pos = { x: 400 + (Math.random() * 40 - 20), y: 300 + (Math.random() * 40 - 20), rotation: 0 };
            visualPlan[item.key] = pos;
            addToCanvas(item.key, item.label, item.color, pos, item.type, item.meta);
            renderLibrary(); // Update sidebar ONLY
            triggerAutosave();
        };
        btnRow.appendChild(btnNext);

        // Add Bulk Row Button (only if > 1)
        if (items.length > 1) {
            const btnBulk = document.createElement('button');
            btnBulk.className = 'btn btn-outline-info btn-sm text-start';
            btnBulk.innerHTML = `<i class="bi bi-grid-3x2-gap me-2"></i>Alle in Reihe (1m)`;
            btnBulk.onclick = () => {
                const startX = 100;
                const startY = 100 + (Math.random() * 200);
                items.forEach((item, idx) => {
                    const pos = { x: startX + (idx * METER_PX), y: startY, rotation: 0 };
                    visualPlan[item.key] = pos;
                    addToCanvas(item.key, item.label, item.color, pos, item.type, item.meta);
                });
                renderLibrary(); // Update sidebar ONLY
                triggerAutosave();
            };
            btnRow.appendChild(btnBulk);
        }

        wrapper.appendChild(btnRow);
        libraryContainer.appendChild(wrapper);
    }

    function addToCanvas(key, label, color, pos, type, meta = {}) {
        // Create specific shapes
        const shapeGenerator = SYMBOLS[type] || SYMBOLS.custom;
        const shapes = shapeGenerator(color);

        // Group them
        const fixtureGroup = new fabric.Group(shapes, {
            originX: 'center',
            originY: 'center'
        });

        // --- Data Callouts ---

        // 1. Primary ID Label (Bottom)
        const idLabel = new fabric.Text(label, {
            fontSize: 11,
            fontWeight: 'bold',
            fill: '#fff',
            originX: 'center',
            originY: 'center',
            top: 28,
            selectable: false,
            fontFamily: 'Segoe UI, Arial'
        });

        // 2. DMX Label (Top - near nose)
        const dmxText = `${meta.universe || '1'}:${meta.address || '?'}`;
        const dmxLabel = new fabric.Text(dmxText, {
            fontSize: 9,
            fill: color, // Match fixture color for patch info
            originX: 'center',
            originY: 'center',
            top: -45,
            selectable: false,
            fontFamily: 'Monaco, Consolas, monospace',
            backgroundColor: 'rgba(0,0,0,0.6)',
            padding: 2
        });

        // 3. Mode Label (Side)
        const modeLabel = new fabric.Text(meta.mode || '', {
            fontSize: 8,
            fill: '#aaa',
            originX: 'center',
            originY: 'center',
            left: 35,
            top: 0,
            angle: 90,
            selectable: false,
            fontFamily: 'Segoe UI, Arial',
            opacity: 0.8
        });

        // Final draggable group
        const mainGroup = new fabric.Group([fixtureGroup, idLabel, dmxLabel, modeLabel], {
            left: pos.x,
            top: pos.y,
            angle: pos.rotation || 0,
            scaleX: globalScale,
            scaleY: globalScale,
            hasControls: true,
            hasBorders: true,
            borderColor: '#0dcaf0',
            cornerColor: '#fff',
            cornerSize: 8,
            transparentCorners: false,
            padding: 10,
            id: key,
            snapToGrid: true
        });

        canvas.add(mainGroup);
    }

    // ------------- Interaction & Snapping -------------

    canvas.on('object:moving', function (options) {
        if (!SNAP_ENABLED) return;

        const target = options.target;
        const snap = GRID_SIZE; // px step

        // Snap X
        target.set({
            left: Math.round(target.left / snap) * snap,
            top: Math.round(target.top / snap) * snap
        });
    });

    // ------------- Autosave -------------
    let saveTimeout;
    const AUTOSAVE_DELAY = 300; // 0.3 seconds for tighter sync

    function triggerAutosave() {
        // Feedback UI elements
        const indicator = document.getElementById('saveStatusIndicator');
        const btn = document.getElementById('btnSaveRigPlan');

        // Update Indicator
        if (indicator) {
            indicator.className = 'badge bg-warning text-dark w-100 py-2';
            indicator.innerHTML = '<span class="spinner-grow spinner-grow-sm me-2" role="status" aria-hidden="true"></span>Speichert gleich...';
        }

        // Update Button (if present)
        if (btn) {
            btn.innerHTML = '<span class="spinner-grow spinner-grow-sm me-2"></span>Warten...';
        }

        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(saveRigPlan, AUTOSAVE_DELAY);
    }

    // Force save on Tab-Switch or Page Departure
    document.querySelectorAll('.tab-link').forEach(link => {
        link.addEventListener('click', () => {
            if (saveTimeout) {
                clearTimeout(saveTimeout);
                saveRigPlan(); // Immediate save
            }
        });
    });

    // Event Listeners for Changes
    canvas.on('object:modified', triggerAutosave);
    canvas.on('object:added', triggerAutosave);
    canvas.on('object:removed', triggerAutosave);

    // ------------- Saving Logic (extracted) -------------

    async function saveRigPlan() {
        if (isSaving) return; // Ignore if already in flight

        const indicator = document.getElementById('saveStatusIndicator');
        const btn = document.getElementById('btnSaveRigPlan');
        const oldBtnText = '<i class="bi bi-save me-2"></i>Positionen Speichern';

        isSaving = true;

        if (indicator) {
            indicator.className = 'badge bg-info text-dark w-100 py-2';
            indicator.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Speichert...';
        }

        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Speichern...';
        }

        // Capture absolute latest state from Canvas
        const currentVisualPlan = {};
        canvas.getObjects().forEach(obj => {
            if (obj.id) {
                currentVisualPlan[obj.id] = {
                    x: Math.round(obj.left),
                    y: Math.round(obj.top),
                    rotation: Math.round(obj.angle)
                };
            }
        });

        try {
            const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

            const resp = await fetch(`/show/${showId}/api/save_rig_positions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ visual_plan: currentVisualPlan })
            });

            if (!resp.ok) {
                const text = await resp.text();
                throw new Error(`Server error: ${resp.status} - ${text}`);
            }

            // Feedback
            // Feedback Success
            if (indicator) {
                indicator.className = 'badge bg-success w-100 py-2';
                indicator.innerHTML = '<i class="bi bi-check-circle me-1"></i>Gespeichert';

                setTimeout(() => {
                    if (indicator.innerHTML.includes('Gespeichert')) {
                        indicator.className = 'badge bg-secondary w-100 py-2';
                        indicator.innerHTML = '<i class="bi bi-check2 me-1"></i>Aktuell';
                    }
                }, 3000);
            }

            if (btn) {
                btn.classList.replace('btn-primary', 'btn-success');
                btn.innerHTML = '<i class="bi bi-check-lg me-2"></i>Gespeichert!';
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = oldBtnText;
                    btn.classList.replace('btn-success', 'btn-primary');
                }, 2000);
            }

        } catch (e) {
            console.error(e);
            if (indicator) {
                indicator.className = 'badge bg-danger w-100 py-2';
                indicator.innerHTML = '<i class="bi bi-exclamation-triangle me-1"></i>Netzwerkfehler';
            }
            if (btn) {
                btn.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>Fehler!';
                btn.classList.add('btn-danger');
                btn.disabled = false;
            }
        } finally {
            isSaving = false;
        }
    }

    // Attach listener to button if it exists (for manual trigger)
    const manualSaveBtn = document.getElementById('btnSaveRigPlan');
    if (manualSaveBtn) {
        manualSaveBtn.addEventListener('click', saveRigPlan);
    }

    // Manual Save Button
    document.getElementById('btnSaveRigPlan').addEventListener('click', () => {
        clearTimeout(saveTimeout); // Cancel pending autosave to avoid double save
        saveRigPlan();
    });

    // ------------- Features -------------

    // DEL Taste zum Entfernen
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Delete' || e.key === 'Backspace') {
            const active = canvas.getActiveObjects();
            if (active.length) {
                active.forEach(obj => {
                    if (obj.id) {
                        delete visualPlan[obj.id]; // Aus Plan löschen
                    }
                    canvas.remove(obj);
                });
                canvas.discardActiveObject();
                // Library aktualisieren (damit sie wieder auftauchen)
                renderUI();
            }
        }
    });

    document.getElementById('btnResetView').addEventListener('click', () => {
        canvas.setViewportTransform([1, 0, 0, 1, 0, 0]);
    });

    // Zoom Handling (Mouse Wheel)
    canvas.on('mouse:wheel', function (opt) {
        var delta = opt.e.deltaY;
        var zoom = canvas.getZoom();
        zoom *= 0.999 ** delta;
        if (zoom > 20) zoom = 20;
        if (zoom < 0.01) zoom = 0.01;
        canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
        opt.e.preventDefault();
        opt.e.stopPropagation();
    });

    // Dragging Canvas (Alt + Drag)
    let isDragging = false;
    let lastPosX, lastPosY;
    canvas.on('mouse:down', function (opt) {
        var evt = opt.e;
        if (evt.altKey === true) {
            isDragging = true;
            selection = false;
            lastPosX = evt.clientX;
            lastPosY = evt.clientY;
        }
    });
    canvas.on('mouse:move', function (opt) {
        if (isDragging) {
            var e = opt.e;
            var vpt = canvas.viewportTransform;
            vpt[4] += e.clientX - lastPosX;
            vpt[5] += e.clientY - lastPosY;
            canvas.requestRenderAll();
            lastPosX = e.clientX;
            lastPosY = e.clientY;
        }
    });
    canvas.on('mouse:up', function (opt) {
        isDragging = false;
        selection = true;
    });

    // Scale Control
    const scaleInput = document.getElementById('fixtureScale');
    if (scaleInput) {
        scaleInput.addEventListener('input', (e) => {
            globalScale = parseFloat(e.target.value);
            canvas.getObjects().forEach(obj => {
                if (obj.id) {
                    obj.set({
                        scaleX: globalScale,
                        scaleY: globalScale
                    });
                }
            });
            canvas.requestRenderAll();
        });
    }

    // Grouping
    document.getElementById('btnGroup').addEventListener('click', () => {
        if (!canvas.getActiveObject()) return;
        if (canvas.getActiveObject().type !== 'activeSelection') return;

        canvas.getActiveObject().toGroup();
        canvas.requestRenderAll();
        triggerAutosave();
    });

    document.getElementById('btnUngroup').addEventListener('click', () => {
        if (!canvas.getActiveObject()) return;
        if (canvas.getActiveObject().type !== 'group') return;

        canvas.getActiveObject().toActiveSelection();
        canvas.requestRenderAll();
        triggerAutosave();
    });

    // Init Logic
    loadRigData();

    function initCanvas() {
        canvas.clear();
        canvas.backgroundColor = '#1a1a1a';
        canvas.selectionColor = 'rgba(13, 110, 253, 0.1)';
        canvas.selectionBorderColor = '#0d6efd';
        drawGrid();

        // Place items from visualPlan
        const prefixes = ["spots", "washes", "beams", "blinders", "strobes"];
        prefixes.forEach(prefix => {
            const items = rigData[`${prefix}_items`] || [];
            items.forEach((item, itemIdx) => {
                const count = parseInt(item.count || 0);
                for (let i = 0; i < count; i++) {
                    const key = `${prefix}_${itemIdx}_${i}`;
                    if (visualPlan[key]) {
                        const meta = {
                            universe: item.universe || '1',
                            address: item.address ? (parseInt(item.address) + i).toString() : '?',
                            mode: item.mode || ''
                        };
                        addToCanvas(key, `#${i + 1}`, TYPE_COLORS[prefix], visualPlan[key], prefix, meta);
                    }
                }
            });
        });

        const customs = rigData.custom_devices || [];
        customs.forEach((item, itemIdx) => {
            const count = parseInt(item.count || 0);
            for (let i = 0; i < count; i++) {
                const key = `custom_${itemIdx}_${i}`;
                if (visualPlan[key]) {
                    const meta = {
                        universe: item.universe || '1',
                        address: item.address ? (parseInt(item.address) + i).toString() : '?',
                        mode: item.mode || ''
                    };
                    addToCanvas(key, `#${i + 1}`, TYPE_COLORS.custom, visualPlan[key], 'custom', meta);
                }
            }
        });

        canvas.requestRenderAll();
    }

    function renderLibrary() {
        libraryContainer.innerHTML = '';
        const prefixes = ["spots", "washes", "beams", "blinders", "strobes"];
        prefixes.forEach(prefix => {
            const items = rigData[`${prefix}_items`] || [];
            items.forEach((item, itemIdx) => {
                const count = parseInt(item.count || 0);
                const name = item.manufacturer && item.model ? `${item.manufacturer} ${item.model}` : `${prefix.toUpperCase()}`;
                const unplaced = [];
                for (let i = 0; i < count; i++) {
                    const key = `${prefix}_${itemIdx}_${i}`;
                    if (!visualPlan[key]) {
                        unplaced.push({
                            key,
                            label: `#${i + 1}`,
                            color: TYPE_COLORS[prefix],
                            type: prefix,
                            meta: {
                                universe: item.universe || '1',
                                address: item.address ? (parseInt(item.address) + i).toString() : '?',
                                mode: item.mode || ''
                            }
                        });
                    }
                }
                if (unplaced.length > 0) addToLibraryGrouped(name, unplaced);
            });
        });

        const customs = rigData.custom_devices || [];
        customs.forEach((item, itemIdx) => {
            const count = parseInt(item.count || 0);
            const name = item.name || "Custom";
            const unplaced = [];
            for (let i = 0; i < count; i++) {
                const key = `custom_${itemIdx}_${i}`;
                if (!visualPlan[key]) {
                    unplaced.push({
                        key,
                        label: `#${i + 1}`,
                        color: TYPE_COLORS.custom,
                        type: 'custom',
                        meta: {
                            universe: item.universe || '1',
                            address: item.address ? (parseInt(item.address) + i).toString() : '?',
                            mode: item.mode || ''
                        }
                    });
                }
            }
            if (unplaced.length > 0) addToLibraryGrouped(name, unplaced);
        });
    }

});
