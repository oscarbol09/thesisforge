/**
 * Shared modal component definitions and accessibility controllers for ThesisForge GUI.
 * Implements WCAG 2.2 AA Focus Trap, Escape-key dismiss, and ARIA state sync.
 */

/**
 * Traps focus within an active modal container and restores focus to the triggering element upon close.
 * @param {HTMLElement} modalEl - The modal dialog element
 * @param {Function} onClose - Callback invoked when the modal requests closure (e.g. on ESC)
 * @returns {Function} cleanup - Function to unbind event listeners and restore focus
 */
function attachModalFocusTrap(modalEl, onClose) {
  if (!modalEl) return () => {};

  const previousActiveElement = document.activeElement;
  const focusableSelector = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
  
  const setInitialFocus = () => {
    const focusable = modalEl.querySelectorAll(focusableSelector);
    if (focusable.length > 0) {
      focusable[0].focus();
    }
  };

  const handleKeydown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
      if (typeof onClose === 'function') onClose();
      return;
    }

    if (e.key === 'Tab') {
      const focusable = Array.from(modalEl.querySelectorAll(focusableSelector));
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  };

  // Run after animation frame so Alpine transitions complete
  requestAnimationFrame(setInitialFocus);
  modalEl.addEventListener('keydown', handleKeydown);

  return () => {
    modalEl.removeEventListener('keydown', handleKeydown);
    if (previousActiveElement && typeof previousActiveElement.focus === 'function') {
      previousActiveElement.focus();
    }
  };
}

/**
 * Alpine.js component: Create Project modal form.
 * Mounted via x-data="createProjectModal()" in index.html.
 */
function createProjectModal() {
  return {
    form: {
      title: "",
      academic_level: "pregrado",
      area_of_study: "",
      topic: "",
      language: "es",
    },
    acceptAiTerms: true,
    isSubmitting: false,
    _cleanupTrap: null,

    init() {
      this.$watch('$store.app.showCreateModal', (isOpen) => {
        if (isOpen) {
          this.$nextTick(() => {
            const modalEl = this.$el.closest('.modal-content') || this.$el;
            this._cleanupTrap = attachModalFocusTrap(modalEl, () => {
              Alpine.store('app').showCreateModal = false;
            });
          });
        } else if (this._cleanupTrap) {
          this._cleanupTrap();
          this._cleanupTrap = null;
        }
      });
    },

    async submitCreate() {
      if (!this.form.title.trim()) return;
      this.isSubmitting = true;
      try {
        const project = await Alpine.store("app").api("/api/projects", {
          method: "POST",
          body: JSON.stringify(this.form),
        });
        Alpine.store("app").toast(
          "success",
          "Proyecto creado",
          `El proyecto "${project.title}" ha sido inicializado.`
        );
        await Alpine.store("app").fetchProjects();
        await Alpine.store("app").selectProject(project.id);
        Alpine.store("app").showCreateModal = false;
        Alpine.store("app").activeTab = "advisor";
        this.form = {
          title: "",
          academic_level: "pregrado",
          area_of_study: "",
          topic: "",
          language: "es",
        };
      } catch (_err) {
        // Toast already handled by api()
      } finally {
        this.isSubmitting = false;
      }
    },
  };
}
