/**
 * ThesisForge — Chapter Drafting & WebSocket Streaming Component
 * Orchestrates 5-chapter canonical thesis outline, LLM section generation, HITL review, and approval.
 */

function draftingComponent() {
  return {
    sections: [],
    selectedSectionId: null,
    selectedSection: null,
    userInstructions: '',
    editorContent: '',
    userFeedback: '',
    
    // Streaming & Async Telemetry
    isStreaming: false,
    streamingTokens: '',
    isSaving: false,
    isApproving: false,
    isInitializing: false,
    wsSocket: null,

    async init() {
      await this.loadSections();
    },

    async loadSections() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      try {
        const data = await Alpine.store('app').api(`/api/drafting/projects/${project.id}/sections`);
        this.sections = data || [];
        
        if (this.sections.length > 0 && !this.selectedSectionId) {
          this.selectSection(this.sections[0].section_id);
        } else if (this.selectedSectionId) {
          const found = this.sections.find(s => s.section_id === this.selectedSectionId);
          if (found) this.selectSection(found.section_id);
        }
      } catch (err) {
        this.sections = [];
      }
    },

    async initializeOutline() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isInitializing = true;
      try {
        const sections = await Alpine.store('app').api(`/api/drafting/projects/${project.id}/initialize`, { method: 'POST' });
        this.sections = sections || [];
        Alpine.store('app').toast('success', 'Esquema Inicializado', `Se generaron ${this.sections.length} secciones en 5 capítulos.`);
        await Alpine.store('app').refreshActiveProject();
        if (this.sections.length > 0) {
          this.selectSection(this.sections[0].section_id);
        }
      } catch (err) {
        // Error toast handled in api()
      } finally {
        this.isInitializing = false;
      }
    },

    selectSection(sectionId) {
      if (this.wsSocket) {
        try {
          this.wsSocket.close();
        } catch (e) {
          // ignore
        }
        this.wsSocket = null;
        this.isStreaming = false;
      }
      this.selectedSectionId = sectionId;
      this.selectedSection = this.sections.find(s => s.section_id === sectionId) || null;
      if (this.selectedSection) {
        this.editorContent = this.selectedSection.content || '';
        this.userFeedback = this.selectedSection.user_feedback || '';
        this.streamingTokens = '';
      }
    },

    getChapterSections(chapterNum) {
      return this.sections.filter(s => s.chapter_number === chapterNum);
    },

    getSectionStatusBadge(status) {
      const badges = {
        pending: 'badge-setup',
        in_progress: 'badge-orientation',
        ready_for_review: 'badge-review',
        approved: 'badge-completed',
      };
      const labels = {
        pending: 'Pendiente',
        in_progress: 'En Proceso',
        ready_for_review: 'Para Revisión',
        approved: 'Aprobado',
      };
      return `<span class="badge ${badges[status] || 'badge-setup'} text-[10px]">${labels[status] || status}</span>`;
    },

    async saveDraftContent() {
      const project = Alpine.store('app').activeProject;
      if (!project || !this.selectedSectionId) return;

      this.isSaving = true;
      try {
        const updated = await Alpine.store('app').api(`/api/drafting/projects/${project.id}/sections/${this.selectedSectionId}`, {
          method: 'PUT',
          body: JSON.stringify({
            content: this.editorContent,
            user_feedback: this.userFeedback || null,
          })
        });

        Alpine.store('app').toast('success', 'Borrador Guardado', `Se guardaron ${updated.word_count} palabras.`);
        await this.loadSections();
      } catch (err) {
        // Error toast handled in api()
      } finally {
        this.isSaving = false;
      }
    },

    async generateWithWebSocket() {
      const project = Alpine.store('app').activeProject;
      if (!project || !this.selectedSectionId) return;

      if (this.wsSocket) {
        try {
          this.wsSocket.close();
        } catch (e) {
          // ignore
        }
        this.wsSocket = null;
      }

      this.isStreaming = true;
      this.streamingTokens = '';
      this.editorContent = '';

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/drafting/ws/${project.id}/${this.selectedSectionId}`;

      try {
        const ws = new WebSocket(wsUrl);
        this.wsSocket = ws;

        ws.onopen = () => {
          ws.send(JSON.stringify({
            action: 'generate',
            user_instructions: this.userInstructions || '',
          }));
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.event === 'token') {
              this.streamingTokens += data.token;
              this.editorContent = this.streamingTokens;
            } else if (data.event === 'complete') {
              this.editorContent = data.content || this.streamingTokens;
              this.isStreaming = false;
              this.wsSocket = null;
              Alpine.store('app').toast('success', 'Generación Completada', `Se redactaron ${data.word_count || 0} palabras.`);
              this.loadSections();
            } else if (data.event === 'error') {
              Alpine.store('app').toast('error', 'Error en Streaming', data.message);
              this.isStreaming = false;
              this.wsSocket = null;
            }
          } catch (e) {
            console.error('Error parsing websocket chunk:', e);
          }
        };

        ws.onerror = (err) => {
          console.error('WebSocket Error:', err);
          Alpine.store('app').toast('error', 'Error de Conexión', 'No se pudo mantener la conexión WebSocket.');
          this.isStreaming = false;
          this.wsSocket = null;
        };

        ws.onclose = () => {
          this.isStreaming = false;
          this.wsSocket = null;
        };

      } catch (err) {
        Alpine.store('app').toast('error', 'Error al Iniciar Streaming', err.message);
        this.isStreaming = false;
        this.wsSocket = null;
      }
    },

    async approveSection() {
      const project = Alpine.store('app').activeProject;
      if (!project || !this.selectedSectionId) return;

      this.isApproving = true;
      try {
        await Alpine.store('app').api(`/api/drafting/projects/${project.id}/sections/${this.selectedSectionId}/approve`, {
          method: 'POST'
        });

        Alpine.store('app').toast('success', 'Sección Aprobada', 'Sección aprobada y resumen consolidado en la memoria jerárquica.');
        await this.loadSections();
        await Alpine.store('app').refreshActiveProject();
      } catch (err) {
        // Error toast handled in api()
      } finally {
        this.isApproving = false;
      }
    },

    render() {
      const project = Alpine.store('app').activeProject;
      if (!project) {
        return `
          <div class="card p-12 text-center max-w-md mx-auto space-y-4">
            <h3 class="font-bold text-lg text-[var(--text-primary)]">Ningún Proyecto Seleccionado</h3>
            <p class="text-sm text-[var(--text-secondary)]">Selecciona un proyecto para acceder a la redacción modular por capítulos.</p>
            <button class="btn btn-primary" @click="$store.app.activeTab = 'dashboard'">Ir al Panel de Proyectos</button>
          </div>
        `;
      }

      if (this.sections.length === 0) {
        return `
          <div class="card p-12 text-center max-w-lg mx-auto space-y-4">
            <div class="w-16 h-16 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
            </div>
            <div>
              <h3 class="font-bold text-lg text-[var(--text-primary)]">Inicializar Esquema Canónico de Tesis</h3>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Genera la estructura estandarizada de 5 capítulos (19 secciones) adaptada a tu enfoque metodológico.</p>
            </div>
            <button class="btn btn-primary btn-lg" @click="initializeOutline()" :disabled="isInitializing">
              <span x-show="!isInitializing">Inicializar Esquema de 5 Capítulos</span>
              <span x-show="isInitializing">Inicializando estructura...</span>
            </button>
          </div>
        `;
      }

      const chapters = [
        { num: 1, title: 'Capítulo I: El Problema de Investigación' },
        { num: 2, title: 'Capítulo II: Marco Teórico y Referencial' },
        { num: 3, title: 'Capítulo III: Marco Metodológico' },
        { num: 4, title: 'Capítulo IV: Análisis e Interpretación de Resultados' },
        { num: 5, title: 'Capítulo V: Conclusiones y Recomendaciones' },
      ];

      return `
        <div class="space-y-6 max-w-7xl mx-auto">
          
          <!-- Header -->
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                <span>Fase 3</span>
                <span>•</span>
                <span>Redacción Modular por Capítulos</span>
              </div>
              <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Estudio de Redacción Científica</h2>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Redacta de forma incremental con streaming en tiempo real y memoria acumulativa.</p>
            </div>

            <div class="flex items-center gap-2">
              <span class="text-xs text-[var(--text-muted)]">Total Secciones:</span>
              <span class="text-sm font-bold tabular-nums text-blue-600">${this.sections.length}</span>
            </div>
          </div>

          <!-- Main 2-Column Split: Outline Sidebar vs. Writing Canvas -->
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            
            <!-- Left 4 Cols: 5-Chapter Outline Navigation -->
            <div class="lg:col-span-4 space-y-4 max-h-[calc(100vh-14rem)] overflow-y-auto pr-1">
              ${chapters.map(ch => {
                const chSections = this.getChapterSections(ch.num);
                if (chSections.length === 0) return '';
                
                return `
                  <div class="card overflow-hidden">
                    <div class="p-3 bg-[var(--bg-subtle)] border-b border-[var(--border-subtle)] font-bold text-xs text-[var(--text-primary)] flex items-center justify-between">
                      <span class="truncate">${ch.title}</span>
                      <span class="text-[10px] font-mono text-[var(--text-muted)]">${chSections.length} secciones</span>
                    </div>

                    <div class="divide-y divide-[var(--border-subtle)]">
                      ${chSections.map(sec => {
                        const isSelected = this.selectedSectionId === sec.section_id;
                        return `
                          <button 
                            @click="selectSection('${sec.section_id}')"
                            class="w-full p-3 text-left transition-colors flex items-start justify-between gap-2 text-xs ${isSelected ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400 font-semibold' : 'hover:bg-[var(--bg-subtle)] text-[var(--text-secondary)]'}"
                          >
                            <div class="space-y-0.5 min-w-0">
                              <p class="truncate text-[var(--text-primary)]">${sec.title}</p>
                              <p class="text-[10px] text-[var(--text-muted)] font-mono">${sec.word_count || 0} palabras</p>
                            </div>
                            ${this.getSectionStatusBadge(sec.status)}
                          </button>
                        `;
                      }).join('')}
                    </div>
                  </div>
                `;
              }).join('')}
            </div>

            <!-- Right 8 Cols: Active Section Writing & Streaming Canvas -->
            <div class="lg:col-span-8 space-y-6">
              ${this.selectedSection ? `
                <div class="card space-y-4 p-6">
                  
                  <!-- Section Header -->
                  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-[var(--border-subtle)] gap-2">
                    <div>
                      <span class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Capítulo ${this.selectedSection.chapter_number} • Sección</span>
                      <h3 class="text-lg font-bold text-[var(--text-primary)]">${this.selectedSection.title}</h3>
                    </div>
                    <div class="flex items-center gap-3">
                      <span class="text-xs text-[var(--text-muted)]">Palabras: <strong class="tabular-nums text-[var(--text-primary)]">${this.selectedSection.word_count || 0}</strong></span>
                      ${this.getSectionStatusBadge(this.selectedSection.status)}
                    </div>
                  </div>

                  <!-- Guidance Input -->
                  <div class="space-y-2">
                    <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Instrucciones u Orientación para la IA (opcional)</label>
                    <div class="flex gap-2">
                      <input 
                        type="text" 
                        x-model="userInstructions" 
                        placeholder="Ej. Desarrollar antecedentes citando a los autores del marco RAG..." 
                        class="flex-1 text-xs"
                        :disabled="isStreaming"
                      >
                      <button 
                        class="btn btn-primary btn-sm shrink-0" 
                        @click="generateWithWebSocket()" 
                        :disabled="isStreaming"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                        <span x-show="!isStreaming">Generar con Streaming</span>
                        <span x-show="isStreaming">Redactando...</span>
                      </button>
                    </div>
                  </div>

                  <!-- Textarea Editor Canvas -->
                  <div class="space-y-2">
                    <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Contenido del Borrador</label>
                    <textarea 
                      x-model="editorContent" 
                      rows="14" 
                      placeholder="El contenido de la sección aparecerá aquí conforme se genere por streaming, o puedes redactarlo directamente..." 
                      class="w-full text-sm font-serif leading-relaxed"
                      :disabled="isStreaming"
                      aria-live="polite"
                    ></textarea>
                  </div>

                  <!-- Bottom Actions -->
                  <div class="flex flex-wrap items-center justify-between pt-4 border-t border-[var(--border-subtle)] gap-3">
                    <div class="flex items-center gap-2">
                      <button 
                        class="btn btn-secondary btn-sm" 
                        @click="saveDraftContent()" 
                        :disabled="isSaving || isStreaming"
                      >
                        <span x-show="!isSaving">Guardar Cambios</span>
                        <span x-show="isSaving">Guardando...</span>
                      </button>
                    </div>

                    <div class="flex items-center gap-2">
                      <button 
                        class="btn btn-primary btn-sm" 
                        @click="approveSection()" 
                        :disabled="isApproving || isStreaming || !editorContent.trim()"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                        <span x-show="!isApproving">Aprobar Sección & Sintetizar Memoria</span>
                        <span x-show="isApproving">Aprobando...</span>
                      </button>
                    </div>
                  </div>

                </div>
              ` : `
                <div class="card p-12 text-center space-y-3">
                  <p class="text-sm text-[var(--text-secondary)]">Selecciona una sección del esquema para comenzar a redactar.</p>
                </div>
              `}
            </div>

          </div>

        </div>
      `;
    }
  };
}
