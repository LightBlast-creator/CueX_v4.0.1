/**
 * AutosaveManager
 * 
 * Automatically saves forms with the class 'autosave-form'.
 * Requires:
 * - Form action attribute set to the POST URL.
 * - Input fields with 'name' attributes.
 * - A status indicator element with ID 'saveStatus_{formId}' (optional).
 */
class AutosaveManager {
    constructor() {
        this.forms = document.querySelectorAll('.autosave-form');
        this.timeouts = new Map();
        this.delay = 300; // 300ms debounce

        this.init();
    }

    init() {
        console.log("AutosaveManager Initialized");
        // DEBUG: Alert to prove file is loaded
        // alert("Autosave Script Loaded! Forms found: " + this.forms.length);

        this.forms.forEach(form => {
            console.log("Attaching to form:", form.id);
            // Add listeners to all inputs
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('input', () => this.scheduleSave(form));
                input.addEventListener('change', () => this.scheduleSave(form));
            });

            // Prevent default submit if user hits Enter (unless it's a textarea)
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveForm(form);
            });
        });
    }

    scheduleSave(form) {
        const formId = form.id || 'unknown';

        // Update Status to "Waiting..."
        this.updateStatus(form, 'waiting');

        // Clear existing timeout
        if (this.timeouts.has(formId)) {
            clearTimeout(this.timeouts.get(formId));
        }

        // Set new timeout
        const timeout = setTimeout(() => {
            this.saveForm(form);
        }, this.delay);

        this.timeouts.set(formId, timeout);
    }

    async saveForm(form) {
        const formId = form.id;
        this.updateStatus(form, 'saving');

        try {
            const formData = new FormData(form);
            const csrfToken = formData.get('csrf_token') || document.querySelector('input[name="csrf_token"]')?.value;

            const headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            };

            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }

            console.log(`[Autosave] Saving ${formId}...`);

            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: headers
            });

            if (response.ok) {
                console.log(`[Autosave] ${formId} saved successfully.`);
                this.updateStatus(form, 'saved');
            } else {
                console.error('[Autosave] Server returned error', response.status);
                this.updateStatus(form, 'error');
            }
        } catch (error) {
            console.error('[Autosave] Network error', error);
            this.updateStatus(form, 'error');
        }
    }

    updateStatus(form, state) {
        // Look for specific status container or fall back to generic approach
        // We assume an ID convention: saveStatus_{formId}
        const statusId = `saveStatus_${form.id}`;
        const indicator = document.getElementById(statusId);

        if (!indicator) return;

        switch (state) {
            case 'waiting':
                indicator.className = 'badge bg-warning text-dark';
                indicator.innerHTML = '<span class="spinner-grow spinner-grow-sm me-1"></span>Speichert gleich...';
                break;
            case 'saving':
                indicator.className = 'badge bg-info text-dark';
                indicator.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Speichert...';
                break;
            case 'saved':
                indicator.className = 'badge bg-success';
                indicator.innerHTML = '<i class="bi bi-check-circle me-1"></i>Gespeichert';
                setTimeout(() => {
                    if (indicator.innerHTML.includes('Gespeichert')) {
                        indicator.className = 'badge bg-secondary';
                        indicator.innerHTML = '<i class="bi bi-check2 me-1"></i>Aktuell';
                    }
                }, 500);
                break;
            case 'error':
                indicator.className = 'badge bg-danger';
                indicator.innerHTML = '<i class="bi bi-exclamation-triangle me-1"></i>Fehler!';
                break;
        }
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    new AutosaveManager();
});
