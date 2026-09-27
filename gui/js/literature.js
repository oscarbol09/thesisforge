/**
 * ThesisForge — Literature & RAG Component
 * Handles federated academic search, PDF ingestion into ChromaDB, APA 7 citation library, and claim grounding.
 */

function literatureComponent() {
  return {
    activeSubTab: 'search', // 'search' | 'citations' | 'grounding'
    searchQuery: '',
    searchLimit: 10,
    sources: {
      semantic_scholar: true,
      arxiv: true,
      crossref: true,
      openalex: true,
    },
    yearStart: '',
    yearEnd: '',
    isSearching: false,
    searchResults: [],
    
    // PDF Upload State
    pdfFile: null,
    pdfTitle: '',
    pdfDoi: '',
    isUploadingPdf: false,
    uploadProgressText: '',

    // Indexed Documents State
    indexedDocuments: [],
    isLoadingDocuments: false,
    deletingDocId: null,

    // Claim Verification State
    claimText: '',
    isVerifyingClaim: false,
    claimVerdict: null,

    // Semantic Vector Query State
    vectorQuery: '',
    isQueryingVector: false,
    vectorChunks: [],

    init() {
      const project = Alpine.store('app').activeProject;
      if (project) {
        this.loadDocuments();
      }
      this.$watch('$store.app.activeProject', (project) => {
        if (project) {
          this.loadDocuments();
        } else {
          this.indexedDocuments = [];
        }
      });
    },

    async loadDocuments() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;
      this.isLoadingDocuments = true;
      try {
        const docs = await Alpine.store('app').api(`/api/literature/projects/${project.id}/documents`, { silent: true });
        this.indexedDocuments = docs || [];
      } catch (err) {
        // silent fallback
      } finally {
        this.isLoadingDocuments = false;
      }
    },

    async deleteDocument(doc) {
      const project = Alpine.store('app').activeProject;
      if (!project) return;
      const title = doc.title || doc.document_id;
      if (!confirm(`¿Estás seguro de eliminar el documento "${title}" y todos sus fragmentos indexados de ChromaDB?`)) {
        return;
      }
      this.deletingDocId = doc.document_id;
      try {
        await Alpine.store('app').api(`/api/literature/projects/${project.id}/documents/${doc.document_id}`, {
          method: 'DELETE'
        });
        Alpine.store('app').toast('success', 'Documento eliminado', `"${title}" y sus vectores en ChromaDB fueron eliminados correctamente.`);
        await this.loadDocuments();
        await Alpine.store('app').refreshActiveProject();
      } catch (err) {
        // Error handled in app.api()
      } finally {
        this.deletingDocId = null;
      }
    },

    async deleteCitation(citation) {
      const project = Alpine.store('app').activeProject;
      if (!project) return;
      if (!confirm(`¿Deseas desvincular la cita "${citation.title?.slice(0, 50)}..." del proyecto?`)) {
        return;
      }
      try {
        await Alpine.store('app').api(`/api/literature/projects/${project.id}/citations/${citation.id}`, {
          method: 'DELETE'
        });
        Alpine.store('app').toast('success', 'Cita desvinculada', 'La referencia bibliográfica fue removida del proyecto.');
        await Alpine.store('app').refreshActiveProject();
      } catch (err) {
        // Error handled in app.api()
      }
    },

    async searchLiterature() {
      if (!this.searchQuery.trim()) return;
      this.isSearching = true;
      this.searchResults = [];

      try {
        const params = new URLSearchParams();
        params.set('q', this.searchQuery.trim());
        params.set('limit', this.searchLimit.toString());
        
        Object.entries(this.sources).forEach(([src, enabled]) => {
          if (enabled) params.append('source', src);
        });

        if (this.yearStart) params.set('year_start', this.yearStart);
        if (this.yearEnd) params.set('year_end', this.yearEnd);

        const results = await Alpine.store('app').api(`/api/literature/search?${params.toString()}`);
        this.searchResults = results || [];
        
        if (this.searchResults.length === 0) {
          Alpine.store('app').toast('info', 'Búsqueda finalizada', 'No se encontraron artículos con los criterios especificados.');
        }
      } catch (err) {
        // Error toast handled in api()
      } finally {
        this.isSearching = false;
      }
    },

    async addCitationToProject(paper) {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      try {
        const citationPayload = {
          doi: paper.doi || null,
          title: paper.title,
          authors: paper.authors || [],
          year: paper.year || new Date().getFullYear(),
          journal: paper.venue || null,
          abstract: paper.abstract || null,
          url: paper.url || null,
          source: paper.source || 'semantic_scholar',
          apa_formatted: '',
        };

        await Alpine.store('app').api(`/api/literature/citations/${project.id}`, {
          method: 'POST',
          body: JSON.stringify(citationPayload)
        });

        Alpine.store('app').toast('success', 'Cita agregada', `"${paper.title.slice(0, 50)}..." se guardó en el proyecto.`);
        await Alpine.store('app').refreshActiveProject();
      } catch (err) {
        // Error toast handled in api()
      }
    },

    isCitationLinked(paper) {
      const project = Alpine.store('app').activeProject;
      if (!project || !project.validated_citations) return false;
      return project.validated_citations.some(c => 
        (paper.doi && c.doi && c.doi.toLowerCase() === paper.doi.toLowerCase()) ||
        (c.title && paper.title && c.title.trim().toLowerCase() === paper.title.trim().toLowerCase())
      );
    },

    async uploadPdfFile(event) {
      const file = event.target.files?.[0] || this.pdfFile;
      if (!file) return;

      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isUploadingPdf = true;
      this.uploadProgressText = 'Extrayendo texto con PyMuPDF, segmentando e indexando en ChromaDB...';

      try {
        const formData = new FormData();
        formData.append('project_id', project.id);
        formData.append('file', file);
        if (this.pdfTitle.trim()) formData.append('title', this.pdfTitle.trim());
        if (this.pdfDoi.trim()) formData.append('doi', this.pdfDoi.trim());

        const chunks = await Alpine.store('app').api('/api/literature/index-pdf', {
          method: 'POST',
          body: formData,
        });

        Alpine.store('app').toast('success', 'PDF Indexado y Citado', `Se extrajeron ${chunks.length} fragmentos semánticos, guardados en ChromaDB y agregados a las citas del proyecto.`);
        this.pdfFile = null;
        this.pdfTitle = '';
        this.pdfDoi = '';
        if (event.target) event.target.value = '';
        await this.loadDocuments();
        await Alpine.store('app').refreshActiveProject();
      } catch (err) {
        // Error toast handled in api()
      } finally {
        this.isUploadingPdf = false;
        this.uploadProgressText = '';
      }
    },

    async verifyClaim() {
      const project = Alpine.store('app').activeProject;
      if (!project || !this.claimText.trim()) return;

      this.isVerifyingClaim = true;
      this.claimVerdict = null;

      try {
        const result = await Alpine.store('app').api('/api/literature/verify-claim', {
          method: 'POST',
          body: JSON.stringify({
            project_id: project.id,
            claim: this.claimText.trim(),
            top_k: 5
          })
        });

        this.claimVerdict = result;
      } catch (err) {
        // Error toast handled in api()
      } finally {
        this.isVerifyingClaim = false;
      }
    },

    async querySemanticContext() {
      const project = Alpine.store('app').activeProject;
      if (!project || !this.vectorQuery.trim()) return;

      this.isQueryingVector = true;
      this.vectorChunks = [];

      try {
        const result = await Alpine.store('app').api('/api/literature/query-context', {
          method: 'POST',
          body: JSON.stringify({
            project_id: project.id,
            query: this.vectorQuery.trim(),
            top_k: 5,
            min_score: 0.0
          })
        });

        this.vectorChunks = result || [];
      } catch (err) {
        // Error toast handled in api()
      } finally {
        this.isQueryingVector = false;
      }
    },

    render() {
      const project = Alpine.store('app').activeProject;
      if (!project) {
        return `
          <div class="card p-12 text-center max-w-md mx-auto space-y-4">
            <h3 class="font-bold text-lg text-[var(--text-primary)]">Ningún Proyecto Seleccionado</h3>
            <p class="text-sm text-[var(--text-secondary)]">Selecciona un proyecto para gestionar literatura científica, PDFs y citas.</p>
            <button class="btn btn-primary" @click="$store.app.activeTab = 'dashboard'">Ir al Panel de Proyectos</button>
          </div>
        `;
      }

      const citations = project.validated_citations || [];

      return `
        <div class="space-y-8 max-w-6xl mx-auto">
          
          <!-- Header and Sub-tabs -->
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                <span>Fase 2</span>
                <span>•</span>
                <span>Literatura Académica & RAG</span>
              </div>
              <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Gestor de Literatura y Respaldo Científico</h2>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Busca publicaciones en Semantic Scholar, ArXiv y CrossRef, o indexa tus propios artículos en PDF en ChromaDB.</p>
            </div>
            
            <div class="flex items-center gap-2 bg-[var(--bg-subtle)] p-1 rounded-lg border border-[var(--border-subtle)] flex-wrap">
              <button 
                class="btn btn-sm" 
                :class="activeSubTab === 'search' ? 'btn-primary' : 'btn-ghost'"
                @click="activeSubTab = 'search'"
              >
                Búsqueda & PDFs
              </button>
              <button 
                class="btn btn-sm" 
                :class="activeSubTab === 'citations' ? 'btn-primary' : 'btn-ghost'"
                @click="activeSubTab = 'citations'"
              >
                Citas del Proyecto (${citations.length})
              </button>
              <button 
                class="btn btn-sm" 
                :class="activeSubTab === 'grounding' ? 'btn-primary' : 'btn-ghost'"
                @click="activeSubTab = 'grounding'"
              >
                Verificar Afirmación
              </button>
            </div>
          </div>

          <!-- SUBTAB 1: Search & PDF Ingestion -->
          <div x-show="activeSubTab === 'search'" class="space-y-6">
            
            <!-- Open Access API Info Banner -->
            <div class="p-4 rounded-lg bg-blue-50/60 dark:bg-blue-950/20 border border-blue-200/60 dark:border-blue-800/30 flex items-start gap-3">
              <svg class="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <div class="text-xs text-[var(--text-secondary)] space-y-1">
                <p class="font-semibold text-[var(--text-primary)]">Búsqueda Federada de Literatura Científica Abierta</p>
                <p>ThesisForge consulta directamente los repositorios académicos de <strong>Semantic Scholar</strong>, <strong>OpenAlex</strong>, <strong>ArXiv</strong> y <strong>CrossRef</strong> mediante sus APIs públicas de acceso abierto. <em>No requieres configurar ninguna clave API para buscar o vincular citas bibliográficas.</em></p>
              </div>
            </div>

            <!-- Search & Filters Bento -->
            <div class="card p-5 space-y-4">
              <div class="flex flex-col sm:flex-row gap-3">
                <div class="relative flex-1">
                  <input 
                    type="search" 
                    x-model="searchQuery" 
                    @keydown.enter="searchLiterature()"
                    placeholder="Buscar publicaciones científicas (ej. retrieval augmented generation hallucinations, machine learning education)..." 
                    class="w-full pl-9 text-sm"
                  >
                  <svg class="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-3 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                </div>
                <button class="btn btn-primary shrink-0" @click="searchLiterature()" :disabled="isSearching || !searchQuery.trim()">
                  <span x-show="!isSearching">Buscar Literatura</span>
                  <span x-show="isSearching">Buscando...</span>
                </button>
              </div>

              <!-- Filter Toggles -->
              <div class="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-[var(--border-subtle)] text-xs text-[var(--text-secondary)]">
                <div class="flex items-center gap-4 flex-wrap">
                  <span class="font-semibold text-[var(--text-muted)]">Fuentes Abiertas:</span>
                  <label class="flex items-center gap-1.5 cursor-pointer">
                    <input type="checkbox" x-model="sources.semantic_scholar" class="rounded text-blue-600">
                    <span>Semantic Scholar</span>
                  </label>
                  <label class="flex items-center gap-1.5 cursor-pointer">
                    <input type="checkbox" x-model="sources.openalex" class="rounded text-blue-600">
                    <span>OpenAlex</span>
                  </label>
                  <label class="flex items-center gap-1.5 cursor-pointer">
                    <input type="checkbox" x-model="sources.arxiv" class="rounded text-blue-600">
                    <span>ArXiv</span>
                  </label>
                  <label class="flex items-center gap-1.5 cursor-pointer">
                    <input type="checkbox" x-model="sources.crossref" class="rounded text-blue-600">
                    <span>CrossRef</span>
                  </label>
                </div>

                <div class="flex items-center gap-2">
                  <span>Años:</span>
                  <input type="number" x-model="yearStart" placeholder="1900" class="w-20 text-xs py-1">
                  <span>-</span>
                  <input type="number" x-model="yearEnd" placeholder="2026" class="w-20 text-xs py-1">
                </div>
              </div>
            </div>

            <!-- PDF Upload Box -->
            <div class="card p-5 space-y-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
                  <h3 class="font-bold text-sm text-[var(--text-primary)]">Indexar Documento PDF Propio en ChromaDB</h3>
                </div>
                <span class="text-xs text-[var(--text-muted)]">Extracción con PyMuPDF + Chunking semántico</span>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div class="sm:col-span-1">
                  <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Archivo PDF *</label>
                  <input type="file" accept=".pdf" @change="uploadPdfFile($event)" :disabled="isUploadingPdf" class="w-full text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700 dark:file:bg-blue-950 dark:file:text-blue-300">
                </div>
                <div>
                  <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Título del Artículo (opcional)</label>
                  <input type="text" x-model="pdfTitle" placeholder="Nombre descriptivo del paper" class="w-full text-xs">
                </div>
                <div>
                  <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">DOI (opcional)</label>
                  <input type="text" x-model="pdfDoi" placeholder="10.1016/..." class="w-full text-xs">
                </div>
              </div>

              <div x-show="isUploadingPdf" class="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400 font-medium">
                <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <span x-text="uploadProgressText"></span>
              </div>
            </div>

            <!-- ChromaDB Indexed Documents Panel -->
            <div class="card p-5 space-y-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <svg class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2 1.5 3 3.5 3h9c2 0 3.5-1 3.5-3V7c0-2-1.5-3-3.5-3h-9C5.5 4 4 5 4 7zm0 4h16M4 15h16"/></svg>
                  <h3 class="font-bold text-sm text-[var(--text-primary)]">Documentos Indexados en ChromaDB (<span x-text="indexedDocuments.length"></span>)</h3>
                </div>
                <button 
                  class="btn btn-ghost btn-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  @click="loadDocuments()"
                  title="Refrescar lista de documentos"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                  <span>Actualizar</span>
                </button>
              </div>

              <!-- Empty State for Indexed Docs -->
              <div x-show="indexedDocuments.length === 0 && !isLoadingDocuments" class="p-6 text-center rounded-lg bg-[var(--bg-subtle)] border border-[var(--border-subtle)] space-y-2">
                <svg class="w-8 h-8 text-[var(--text-muted)] mx-auto opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                <p class="text-xs font-semibold text-[var(--text-primary)]">No hay documentos PDF indexados en este proyecto</p>
                <p class="text-xs text-[var(--text-secondary)]">Sube un archivo PDF en el panel superior para vectorizarlo en ChromaDB. Sus fragmentos se usarán automáticamente para redactar capítulos y validar afirmaciones.</p>
              </div>

              <!-- List of Indexed Documents -->
              <div x-show="indexedDocuments.length > 0" class="divide-y divide-[var(--border-subtle)] border border-[var(--border-subtle)] rounded-lg overflow-hidden">
                <template x-for="doc in indexedDocuments" :key="doc.document_id">
                  <div class="p-4 bg-[var(--bg-surface)] hover:bg-[var(--bg-subtle)] flex items-center justify-between gap-4 transition-colors">
                    <div class="space-y-1 min-w-0 flex-1">
                      <div class="flex items-center gap-2 flex-wrap">
                        <span 
                          class="badge text-[10px]" 
                          :class="doc.status === 'indexed' ? 'badge-success' : (doc.status === 'pending' ? 'badge-warning' : 'badge-critical')"
                          x-text="doc.status === 'indexed' ? ('Indexado • ' + (doc.chunk_count || 0) + ' fragmentos') : (doc.status === 'pending' ? 'Procesando...' : 'Error')"
                        ></span>
                        <span x-show="doc.doi" class="text-[11px] font-mono text-[var(--text-muted)] truncate" x-text="'DOI: ' + doc.doi"></span>
                      </div>
                      <h4 class="text-sm font-semibold text-[var(--text-primary)] truncate" x-text="doc.title || doc.document_id"></h4>
                      <p class="text-[11px] text-[var(--text-muted)]" x-text="'Indexado el ' + new Date(doc.created_at).toLocaleDateString()"></p>
                    </div>

                    <div class="flex items-center gap-2 shrink-0">
                      <button 
                        class="btn btn-outline btn-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 border-red-200 dark:border-red-900/50"
                        @click="deleteDocument(doc)"
                        :disabled="deletingDocId === doc.document_id"
                        title="Eliminar documento y vectores de ChromaDB"
                      >
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        <span x-show="deletingDocId !== doc.document_id">Eliminar</span>
                        <span x-show="deletingDocId === doc.document_id">Borrando...</span>
                      </button>
                    </div>
                  </div>
                </template>
              </div>
            </div>

            <!-- Search Results List -->
            <div x-show="isSearching" class="space-y-4">
              <div class="card p-5 space-y-3">
                <div class="skeleton h-5 w-3/4"></div>
                <div class="skeleton h-4 w-1/2"></div>
                <div class="skeleton h-16 w-full"></div>
              </div>
            </div>

            <div x-show="!isSearching && searchResults.length > 0" class="space-y-4">
              <div class="flex items-center justify-between text-xs text-[var(--text-muted)] px-1">
                <span>Resultados encontrados: <strong class="text-[var(--text-primary)]" x-text="searchResults.length"></strong></span>
              </div>

              <template x-for="(paper, idx) in searchResults" :key="paper.paper_id || idx">
                <div class="card p-5 space-y-3">
                  <div class="flex items-start justify-between gap-4">
                    <div class="space-y-1 flex-1 min-w-0">
                      <div class="flex items-center gap-2 flex-wrap">
                        <span class="badge badge-note text-[10px]" x-text="paper.source"></span>
                        <span class="text-xs font-semibold text-[var(--text-muted)]" x-text="paper.year || 's.f.'"></span>
                      </div>
                      <h4 class="font-bold text-base text-[var(--text-primary)] leading-snug" x-text="paper.title"></h4>
                      <p class="text-xs text-[var(--text-secondary)] font-medium" x-text="(paper.authors || []).join(', ')"></p>
                    </div>

                    <button 
                      class="btn btn-sm shrink-0" 
                      :class="isCitationLinked(paper) ? 'btn-outline text-emerald-600 border-emerald-300 dark:border-emerald-800' : 'btn-secondary'"
                      @click="addCitationToProject(paper)"
                      :disabled="isCitationLinked(paper)"
                      :title="isCitationLinked(paper) ? 'Esta cita ya está guardada en el proyecto' : 'Guardar esta cita en el proyecto'"
                    >
                      <svg x-show="!isCitationLinked(paper)" class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                      <svg x-show="isCitationLinked(paper)" class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                      <span x-text="isCitationLinked(paper) ? 'Cita Vinculada' : 'Vincular Cita'"></span>
                    </button>
                  </div>

                  <p class="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-3" x-text="paper.abstract || 'Sin resumen disponible.'"></p>

                  <div class="flex items-center gap-4 text-xs text-[var(--text-muted)] pt-2 border-t border-[var(--border-subtle)] flex-wrap">
                    <span x-show="paper.venue" class="truncate" x-text="paper.venue"></span>
                    <a x-show="paper.doi" :href="'https://doi.org/' + paper.doi" target="_blank" class="text-blue-600 hover:underline font-mono text-[11px]" x-text="'DOI: ' + paper.doi"></a>
                    <a x-show="paper.open_access_pdf" :href="paper.open_access_pdf" target="_blank" class="text-emerald-600 hover:underline text-[11px] flex items-center gap-1 font-semibold">
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                      <span>PDF Open Access</span>
                    </a>
                  </div>
                </div>
              </template>
            </div>

          </div>

          <!-- SUBTAB 2: Validated Citations in Project -->
          <div x-show="activeSubTab === 'citations'" class="space-y-4">
            ${citations.length === 0 ? `
              <div class="card p-12 text-center max-w-md mx-auto space-y-3">
                <h4 class="font-bold text-base text-[var(--text-primary)]">Sin Citas Registradas</h4>
                <p class="text-sm text-[var(--text-secondary)]">Aún no has vinculado citas a este proyecto. Realiza una búsqueda académica o sube un PDF para agregarlas.</p>
                <button class="btn btn-primary btn-sm" @click="activeSubTab = 'search'">Buscar Literatura o Subir PDF</button>
              </div>
            ` : `
              <div class="space-y-4">
                <div class="flex items-center justify-between text-xs text-[var(--text-muted)] px-1">
                  <span>Total de fuentes bibliográficas vinculadas: <strong class="text-[var(--text-primary)]">${citations.length}</strong></span>
                </div>

                ${citations.map((c, idx) => `
                  <div class="card p-5 space-y-3">
                    <div class="flex items-start justify-between gap-4">
                      <div class="space-y-1 flex-1">
                        <div class="flex items-center gap-2 flex-wrap">
                          <span class="badge ${c.source === 'local_pdf' ? 'badge-success' : 'badge-note'} text-[10px]">
                            ${c.source === 'local_pdf' ? '📄 PDF Local' : (c.source || 'academic')}
                          </span>
                          <span class="text-xs font-semibold text-[var(--text-muted)]">${c.year || 's.f.'}</span>
                        </div>
                        <h4 class="font-bold text-sm text-[var(--text-primary)]">${c.title}</h4>
                        <p class="text-xs text-[var(--text-secondary)]">${(c.authors || []).join(', ')}</p>
                      </div>
                      
                      <div class="flex items-center gap-2 shrink-0">
                        <span class="text-xs font-mono text-[var(--text-muted)]">#${idx + 1}</span>
                        <button 
                          class="btn btn-ghost btn-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                          @click="deleteCitation(${JSON.stringify(c).replace(/"/g, '&quot;')})"
                          title="Eliminar cita del proyecto"
                        >
                          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        </button>
                      </div>
                    </div>

                    ${c.apa_formatted ? `
                      <div class="p-3 rounded bg-[var(--bg-subtle)] text-xs border border-[var(--border-subtle)]">
                        <p class="font-semibold text-blue-600 dark:text-blue-400 mb-0.5">Formato APA 7ª Edición:</p>
                        <p class="italic text-[var(--text-primary)] font-serif">${c.apa_formatted}</p>
                      </div>
                    ` : ''}

                    <div class="flex items-center gap-4 text-xs text-[var(--text-muted)] pt-2 border-t border-[var(--border-subtle)] flex-wrap">
                      ${c.journal ? `<span>${c.journal}</span>` : ''}
                      ${c.doi ? `<a href="https://doi.org/${c.doi}" target="_blank" class="text-blue-600 hover:underline font-mono text-[11px]">DOI: ${c.doi}</a>` : ''}
                    </div>
                  </div>
                `).join('')}
              </div>
            `}
          </div>

          <!-- SUBTAB 3: Claim Grounding / Fact-checking -->
          <div x-show="activeSubTab === 'grounding'" class="space-y-6">
            <div class="card p-5 space-y-4">
              <div>
                <h3 class="font-bold text-base text-[var(--text-primary)]">Verificador Anti-Alucinaciones (Claim Grounding)</h3>
                <p class="text-xs text-[var(--text-secondary)] mt-0.5">Comprueba si una afirmación que deseas incluir en tu tesis está respaldada empíricamente por los documentos y papers indexados en ChromaDB.</p>
              </div>

              <div class="space-y-3">
                <textarea 
                  x-model="claimText" 
                  rows="3" 
                  placeholder="Escribe la afirmación que deseas verificar contra la literatura (ej. El aprendizaje por refuerzo con retroalimentación humana mitiga sesgos en modelos de lenguaje)..."
                  class="w-full text-sm"
                ></textarea>

                <button 
                  class="btn btn-primary" 
                  @click="verifyClaim()" 
                  :disabled="isVerifyingClaim || !claimText.trim()"
                >
                  <span x-show="!isVerifyingClaim">Verificar Respaldo Empírico en ChromaDB</span>
                  <span x-show="isVerifyingClaim">Buscando y verificando en ChromaDB...</span>
                </button>
              </div>
            </div>

            <!-- Verdict Card -->
            <div x-show="claimVerdict" class="card p-5 space-y-4" style="display: none;">
              <div class="flex items-center justify-between">
                <h4 class="font-bold text-sm text-[var(--text-primary)]">Resultado del Análisis de Evidencia</h4>
                <span 
                  class="badge" 
                  :class="claimVerdict?.is_supported ? 'badge-success' : 'badge-critical'"
                  x-text="claimVerdict?.is_supported ? 'Afirmación Respaldada' : 'Sin Respaldo Suficiente'"
                ></span>
              </div>

              <div class="text-xs space-y-3">
                <p class="text-[var(--text-secondary)]">Nivel de Confianza: <strong class="tabular-nums" x-text="Math.round((claimVerdict?.confidence_score || 0) * 100) + '%'"></strong></p>
                <p x-show="claimVerdict?.refuting_or_missing_reason" class="p-3 rounded bg-amber-50 dark:bg-amber-950/20 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/40" x-text="claimVerdict?.refuting_or_missing_reason"></p>
                
                <template x-if="claimVerdict?.supporting_chunks && claimVerdict.supporting_chunks.length > 0">
                  <div class="space-y-2 pt-2 border-t border-[var(--border-subtle)]">
                    <p class="font-semibold text-[var(--text-primary)]">Fragmentos de Evidencia Recuperados:</p>
                    <div class="space-y-2">
                      <template x-for="sc in claimVerdict.supporting_chunks" :key="sc.chunk.id">
                        <div class="p-3 rounded bg-[var(--bg-subtle)] border border-[var(--border-subtle)] text-xs space-y-1">
                          <div class="flex items-center justify-between text-[11px] text-[var(--text-muted)]">
                            <span class="font-semibold text-[var(--text-primary)]" x-text="sc.chunk.title || 'Documento'"></span>
                            <span x-text="'Pág. ' + (sc.chunk.page_number || 1)"></span>
                          </div>
                          <p class="italic text-[var(--text-secondary)]" x-text="'\"' + sc.chunk.text + '\"'"></p>
                        </div>
                      </template>
                    </div>
                  </div>
                </template>
              </div>
            </div>

          </div>

        </div>
      `;
    }
  };
}
