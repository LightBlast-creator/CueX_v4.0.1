
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
    const GRID_SIZE = 20; // Snapping Grid (cm)
    const SNAP_ENABLED = true;

    // Standard Symbols (Fabric Paths or Shapes)
    // Simple USITT-like representations
    const SYMBOLS = {
        spots: (color) => {
            // "Nose" triangle for direction
            const body = new fabric.Rect({ width: 30, height: 40, fill: color, originX: 'center', originY: 'center' });
            const nose = new fabric.Triangle({ width: 30, height: 15, fill: color, originX: 'center', originY: 'bottom', top: -20, angle: 180 });
            return [body, nose];
        },
        washes: (color) => {
            // Circle with inner lens indication
            const circle = new fabric.Circle({ radius: 20, fill: color, originX: 'center', originY: 'center' });
            const lens = new fabric.Circle({ radius: 12, fill: 'rgba(255,255,255,0.3)', originX: 'center', originY: 'center', stroke: 'rgba(0,0,0,0.2)', strokeWidth: 1 });
            return [circle, lens];
        },
        beams: (color) => {
            // Narrow rectangle/tube
            const body = new fabric.Rect({ width: 25, height: 45, fill: color, originX: 'center', originY: 'center', rx: 5, ry: 5 });
            const lens = new fabric.Circle({ radius: 8, fill: '#fff', originX: 'center', originY: 'center', top: -15 });
            return [body, lens];
        },
        blinders: (color) => {
            // Square with "lamps"
            const body = new fabric.Rect({ width: 40, height: 25, fill: color, originX: 'center', originY: 'center' });
            const lamp1 = new fabric.Circle({ radius: 8, fill: '#ffeb3b', originX: 'center', originY: 'center', left: -10 });
            const lamp2 = new fabric.Circle({ radius: 8, fill: '#ffeb3b', originX: 'center', originY: 'center', left: 10 });
            return [body, lamp1, lamp2];
        },
        strobes: (color) => {
            // Wide rect
            return [new fabric.Rect({ width: 50, height: 15, fill: '#fff', stroke: color, strokeWidth: 2, originX: 'center', originY: 'center' })];
        },
        custom: (color) => {
            return [new fabric.Rect({ width: 30, height: 30, fill: color, originX: 'center', originY: 'center' })];
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

    // ------------- Rendering -------------

    function renderUI() {
        libraryContainer.innerHTML = '';
        canvas.clear();
        canvas.backgroundColor = '#1a1a1a';
        canvas.selectionColor = 'rgba(13, 110, 253, 0.1)';
        canvas.selectionBorderColor = '#0d6efd';

        drawGrid();

        // Items verarbeiten
        const prefixes = ["spots", "washes", "beams", "blinders", "strobes"];

        prefixes.forEach(prefix => {
            const items = rigData[`${prefix}_items`] || [];
            items.forEach((item, itemIdx) => {
                const count = parseInt(item.count || 0);
                const name = item.manufacturer && item.model ? `${item.manufacturer} ${item.model}` : `${prefix.toUpperCase()}`;

                for (let i = 0; i < count; i++) {
                    const key = `${prefix}_${itemIdx}_${i}`;
                    const label = `#${i + 1}`; // Short label on fixture
                    const fullLabel = `${name} #${i + 1}`;

                    if (visualPlan[key]) {
                        addToCanvas(key, label, TYPE_COLORS[prefix], visualPlan[key], prefix);
                    } else {
                        addToLibrary(key, fullLabel, TYPE_COLORS[prefix], prefix);
                    }
                }
            });
        });

        // Custom Devices (ähnlich...)
        const customs = rigData.custom_devices || [];
        customs.forEach((item, itemIdx) => {
            const count = parseInt(item.count || 0);
            const name = item.name || "Custom";
            for (let i = 0; i < count; i++) {
                const key = `custom_${itemIdx}_${i}`;
                const label = `#${i + 1}`;
                if (visualPlan[key]) {
                    addToCanvas(key, label, TYPE_COLORS.custom, visualPlan[key], 'custom');
                } else {
                    addToLibrary(key, `${name} #${i + 1}`, TYPE_COLORS.custom, 'custom');
                }
            }
        });

        canvas.requestRenderAll();
    }

    function drawGrid() {
        const gridSize = GRID_SIZE * 2; // Screen pixels per grid unit (scaled)
        const width = 2000; // Virtual infinite canvas size
        const height = 2000;

        for (let i = 0; i < (width / gridSize); i++) {
            canvas.add(new fabric.Line([i * gridSize, 0, i * gridSize, height],
                { stroke: '#262626', selectable: false, evented: false }));
            canvas.add(new fabric.Line([0, i * gridSize, width, i * gridSize],
                { stroke: '#262626', selectable: false, evented: false }));
        }
    }

    function addToLibrary(key, label, color, type) {
        const btn = document.createElement('button');
        btn.className = 'list-group-item list-group-item-action list-group-item-dark d-flex justify-content-between align-items-center small';
        // Icon based on type
        let icon = 'bi-lightbulb';
        if (type === 'washes') icon = 'bi-circle-fill';
        if (type === 'beams') icon = 'bi-cone-striped';

        btn.innerHTML = `
            <span><i class="bi ${icon} me-2" style="color: ${color}"></i>${label}</span>
            <i class="bi bi-plus-lg text-muted"></i>
        `;
        btn.onclick = () => {
            const pos = { x: 400, y: 300, rotation: 0 }; // Default Center
            visualPlan[key] = pos;
            addToCanvas(key, label.split(' ').pop(), color, pos, type);
            btn.remove();
        };
        libraryContainer.appendChild(btn);
    }

    function addToCanvas(key, label, color, pos, type) {
        // Create specific shapes
        const shapeGenerator = SYMBOLS[type] || SYMBOLS.custom;
        const shapes = shapeGenerator(color);

        // Group them
        const group = new fabric.Group(shapes, {
            originX: 'center',
            originY: 'center'
        });

        // Add Label (Text) floating above/below?
        // Or inside? Inside is hard for small icons.
        // Let's put a small text tag next to it.
        const text = new fabric.Text(label, {
            fontSize: 10,
            fill: '#fff',
            originX: 'center',
            originY: 'center',
            top: 25, // offset
            selectable: false
        });

        // Final draggable group
        const mainGroup = new fabric.Group([group, text], {
            left: pos.x,
            top: pos.y,
            angle: pos.rotation || 0,
            hasControls: true,
            hasBorders: true,
            borderColor: '#0dcaf0',
            cornerColor: '#fff',
            cornerSize: 8,
            transparentCorners: false,
            padding: 5,
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
    const AUTOSAVE_DELAY = 1000; // 1 second

    function triggerAutosave() {
        // Change button state to "Pending"
        const btn = document.getElementById('btnSaveRigPlan');
        if (btn) {
            btn.innerHTML = '<span class="spinner-grow spinner-grow-sm me-2"></span>Warten...';
            btn.classList.replace('btn-success', 'btn-primary');
        }

        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(saveRigPlan, AUTOSAVE_DELAY);
    }

    // Event Listeners for Changes
    canvas.on('object:modified', triggerAutosave);
    canvas.on('object:added', triggerAutosave);
    canvas.on('object:removed', triggerAutosave);

    // ------------- Saving Logic (extracted) -------------

    async function saveRigPlan() {
        const btn = document.getElementById('btnSaveRigPlan');
        if (!btn) return;
        const oldHtml = '<i class="bi bi-save me-2"></i>Positionen Speichern'; // Default Text restoration

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Speichern...';

        // Positionen aus Canvas lesen
        canvas.getObjects().forEach(obj => {
            if (obj.id) { // Nur unsere Fixtures
                visualPlan[obj.id] = {
                    x: Math.round(obj.left),
                    y: Math.round(obj.top),
                    rotation: Math.round(obj.angle)
                };
            }
        });

        // Delete Logic: Check what is missing from canvas vs what we had loading?
        // Current simplified logic: We only update positions of existing items.
        // Known issue: Deleting visual item does not remove it from visualPlan completely in backend unless we send full replacement?
        // The backend replaces `rig["visual_plan"] = data.get("visual_plan", {})`.
        // So sending the current state is correct for "what is on canvas".
        // BUT: If something is in `rigData` but not on canvas, it's just "not placed". 
        // We need to ensure we don't lose data of items that are just "not loaded yet"? No, we load everything.

        try {
            // CSRF Token holen
            const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

            const resp = await fetch(`/show/${showId}/api/save_rig_positions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ visual_plan: visualPlan })
            });

            if (!resp.ok) {
                const text = await resp.text();
                throw new Error(`Server error: ${resp.status} - ${text}`);
            }

            // Feedback
            btn.innerHTML = '<i class="bi bi-check-lg me-2"></i>Gespeichert!';
            btn.classList.replace('btn-primary', 'btn-success');

            // Re-enable (but keep "Saved" look for a moment)
            setTimeout(() => {
                btn.disabled = false;
                // Don't reset text immediately if we want to show state, but for manual click validation it's nice.
                // For autosave, maybe keep "Saved!" until next change?
                // Let's reset to "Save" to indicate it's ready.
                btn.innerHTML = oldHtml;
                btn.classList.replace('btn-success', 'btn-primary');
            }, 2000);

        } catch (e) {
            console.error(e);
            btn.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>Fehler!';
            btn.classList.add('btn-danger');
            btn.disabled = false;
        }
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

    // Init Logic
    loadRigData();

});
