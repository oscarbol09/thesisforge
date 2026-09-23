/**
 * ThesisForge — Core Alpine.js Store & Application Orchestrator
 * Governs state synchronization, unified HTTP client, WebSocket connections, and UI notifications.
 */

document.addEventListener('alpine:init', () => {
  Alpine.store('app', {
    // Current Visual Mode & Navigation
    theme: localStorage.getItem('tf_theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'),
    activeTab: 'dashboard',
    
    // Project State Management
    projects: [],
    activeProjectId: localStorage.getItem('tf_active_project_id') || null,
    activeProject: null,
    
    // Global UI Telemetry
    isLoading: false,
    loadingText: '',
    toasts: [],
    
    // Modals visibility
    showCreateModal: false,
    showSettingsModal: false,
    
    // BYOK Config State
    settings: {
      default_provider: 'openrouter',
      default_model: 'anthropic/claude-3.5-sonnet',
      openrouter_api_key: '',
      gemini_api_key: '',
      openai_api_key: '',
      groq_api_key: '',
      nvidia_nim_api_key: '',
      semantic_scholar_api_key: '',
    },

    // Initialization lifecycle
    async init() {
      this.applyTheme(this.theme);
      await this.fetchProjects();
      
      if (this.activeProjectId) {
        await this.selectProject(this.activeProjectId);
      }
      
      // Global keyboard navigation
      window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
          e.preventDefault();
          this.showCreateModal = true;
        }
      });
    },

    // Theme Management
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('tf_theme', this.theme);
      this.applyTheme(this.theme);
    },

    applyTheme(theme) {
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    },

    // Unified API HTTP Client
    async api(endpoint, options = {}) {
      const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

      // Don't set Content-Type for FormData (browser will set multipart/form-data with boundary)
      if (options.body instanceof FormData) {
        delete defaultHeaders['Content-Type'];
      }

      const config = {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
      };

      try {
        const response = await fetch(endpoint, config);
        
        // Handle 204 No Content
        if (response.status === 204) {
          return null;
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          const errorMessage = data.message || data.detail || `Error HTTP ${response.status}`;
          this.toast('error', 'Error en la solicitud', errorMessage);
          throw new Error(errorMessage);
        }

        return data;
      } catch (err) {
        if (!options.silent) {
          console.error(`API Error on [${endpoint}]:`, err);
        }
        throw err;
      }
    },

    // Project Operations
    async fetchProjects() {
      try {
        this.projects = await this.api('/api/projects');
      } catch {
        this.projects = [];
      }
    },

    async selectProject(projectId) {
      if (!projectId) {
        this.activeProjectId = null;
        this.activeProject = null;
        localStorage.removeItem('tf_active_project_id');
        return;
      }

      this.isLoading = true;
      this.loadingText = 'Cargando estado del proyecto...';
      try {
        this.activeProject = await this.api(`/api/projects/${projectId}`);
        this.activeProjectId = projectId;
        localStorage.setItem('tf_active_project_id', projectId);
      } catch (err) {
        this.toast('error', 'No se pudo cargar el proyecto', err.message);
        this.activeProjectId = null;
        this.activeProject = null;
        localStorage.removeItem('tf_active_project_id');
      } finally {
        this.isLoading = false;
        this.loadingText = '';
      }
    },

    async refreshActiveProject() {
      if (this.activeProjectId) {
        try {
          this.activeProject = await this.api(`/api/projects/${this.activeProjectId}`, { silent: true });
          await this.fetchProjects();
        } catch (err) {
          console.error('Error refreshing project state:', err);
        }
      }
    },

    // Toast Notifications System
    toast(type, title, message) {
      const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
      this.toasts.push({ id, type, title, message });

      // Auto dismiss after 4.5 seconds
      setTimeout(() => {
        this.removeToast(id);
      }, 4500);
    },

    removeToast(id) {
      this.toasts = this.toasts.filter(t => t.id !== id);
    },

    // Content Sanitization
    sanitize(rawHtml) {
      if (typeof DOMPurify !== 'undefined') {
        return DOMPurify.sanitize(rawHtml);
      }
      // Basic text escaping fallback
      const div = document.createElement('div');
      div.textContent = rawHtml;
      return div.innerHTML;
    },

    // Academic Phase Utilities
    getPhaseLabel(phase) {
      const labels = {
        setup: 'Configuración Inicial',
        orientation: 'Orientación Metodológica',
        context: 'Literatura & RAG',
        drafting: 'Redacción Modular',
        review: 'Auditoría de Jurado',
        completed: 'Tesis Culminada',
      };
      return labels[phase] || phase;
    },

    getPhaseBadgeClass(phase) {
      return `badge badge-${phase || 'setup'}`;
    },

    formatDate(isoString) {
      if (!isoString) return 's.f.';
      const date = new Date(isoString);
      return new Intl.DateTimeFormat('es-CO', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      }).format(date);
    },
  });
});
