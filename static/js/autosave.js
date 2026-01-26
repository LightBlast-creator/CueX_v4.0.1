/**
 * AutosaveManager
 * 
 * Automatically saves forms with the class 'autosave-form'.
 * Uses Event Delegation to handle forms present at load OR added later.
 */
class AutosaveManager {
    constructor() {
        this.timeouts = new Map();
        this.delay = 300; // 300ms debounce
        this.init();
    }

    init() {
        console.log("AutosaveManager (Delegation) Initialized");

        // Global Listener for Input/Change
        document.addEventListener('input', (e) => this.handleInput(e));
        document.addEventListener('change', (e) => this.handleInput(e));

        // Global Listener for Submit
        document.addEventListener('submit', (e) => {
            const form = e.target.closest('.autosave-form');
            if (form) {
                e.preventDefault();
                this.saveForm(form);
            }
        });
    }

    handleInput(e) {
        const target = e.target;
        // Only care about inputs/textareas/selects inside an .autosave-form
        const form = target.closest('.autosave-form');
        if (!form) return;

        // Ignore utility inputs if needed (e.g. search fields inside a form, though unlikely)
        if (target.type === 'button' || target.type === 'submit') return;

        this.scheduleSave(form);
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

                // Optional: Update form values from response if server modifies them?
                // For now, we assume one-way sync is enough.
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
                    // Check if text is still "Gespeichert" before resetting (avoid race conditions)
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
