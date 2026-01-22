# Skill: UI Expert

This skill ensures that all UI/UX changes in CueX follow the project's "Rich Aesthetics" and design system.

## Design Tokens

To maintain consistency, use the following CSS patterns:

### Colors & Backgrounds
*   **Body Background:** `#181a1b`
*   **Surface Background (Cards, Modals):** `#23272b`
*   **Border Color:** `#343a40`
*   **Text Color (Primary):** `#e9ecef`
*   **Text Color (Muted):** `#ced4da`

### Components
*   **Buttons:** `border-radius: 6px; font-weight: 500;`
*   **Inputs:** Same background as surfaces (`#23272b`), consistent border (`1px solid #343a40`).
*   **Cards:** Use `.card` with the surface background and proper border.

### Aesthetic Principles
1.  **Vibrant but Dark:** Focus on deep grays and near-blacks with high-contrast text.
2.  **Premium Feel:** Always use semi-bold weights for interactive elements and rounded corners for a modern look.
3.  **No Placeholders:** Always use real data or generated assets for demonstrations.

## Checklists for UI Tasks

- [ ] Check `base.html` for existing global styles.
- [ ] Ensure new elements use the defined surface and border colors.
- [ ] Verify responsiveness on desktop and mobile.
- [ ] Add smooth transitions for hover/active states.
