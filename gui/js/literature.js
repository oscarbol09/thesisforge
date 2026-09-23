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

    // Claim Verification State
    claimText: '',
    isVerifyingClaim: false,
    claimVerdict: null,

    // Semantic Vector Query State
    vectorQuery: '',
    isQueryingVector: false,
    vectorChunks: [],

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

    async uploadPdfFile(event) {
      const file = event.target.files?.[0] || this.pdfFile;
      if (!file) return;

      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isUploadingPdf = true;
      this.uploadProgressText = 'Extrayendo texto con PyMuPDF e indexando en ChromaDB...';

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

        Alpine.store('app').toast('success', 'PDF Indexado', `Se extrajeron ${chunks.length} fragmentos semánticos.`);
        this.pdfFile = null;
        this.pdfTitle = '';
        this.pdfDoi = '';
        if (event.target) event.target.value = '';
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
          
          <!-- Header and Tabs -->
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                <span>Fase 2</span>
                <span>•</span>
                <span>Literatura Académica & RAG</span>
              </div>
              <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Gestor de Literatura y Respaldo Científico</h2>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Busca publicaciones en Semantic Scholar, ArXiv y CrossRef, o indexa tus propios artículos en PDF.</p>
            </div>
            
            <div class="flex items-center gap-2 bg-[var(--bg-subtle)] p-1 rounded-lg border border-[var(--border-subtle)]">
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
            
            <!-- Search & Filters Bento -->
            <div class="card p-5 space-y-4">
              <div class="flex flex-col sm:flex-row gap-3">
                <div class="relative flex-1">
                  <input 
                    type="search" 
                    x-model="searchQuery" 
                    @keydown.enter="searchLiterature()"
                    placeholder="Buscar publicaciones científicas (ej. large language models in medical diagnosis)..." 
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
                <div class="flex items-center gap-4">
                  <span class="font-semibold text-[var(--text-muted)]">Fuentes:</span>
                  <label class="flex items-center gap-1.5 cursor-pointer">
                    <input type="checkbox" x-model="sources.semantic_scholar" class="rounded text-blue-600">
                    <span>Semantic Scholar</span>
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

            <!-- PDF Upload Accordion -->
            <div class="card p-5 space-y-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
                  <h3 class="font-bold text-sm text-[var(--text-primary)]">Indexar Documento PDF Propio en ChromaDB</h3>
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div class="sm:col-span-1">
                  <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Archivo PDF *</label>
                  <input type="file" accept=".pdf" @change="uploadPdfFile($event)" :disabled="isUploadingPdf" class="w-full text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700">
                </div>
                <div>
                  <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Título del Artículo (opcional)</label>
                  <input type="text" x-model="pdfTitle" placeholder="Nombre descriptivo" class="w-full text-xs">
                </div>
                <div>
                  <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">DOI (opcional)</label>
                  <input type="text" x-model="pdfDoi" placeholder="10.1016/..." class="w-full text-xs">
                </div>
              </div>

              <div x-show="isUploadingPdf" class="flex items-center gap-2 text-xs text-blue-600">
                <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <span x-text="uploadProgressText"></span>
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
                    <div class="space-y-1 flex-1">
                      <div class="flex items-center gap-2">
                        <span class="badge badge-note text-[10px]" x-text="paper.source"></span>
                        <span class="text-xs font-semibold text-[var(--text-muted)]" x-text="paper.year || 's.f.'"></span>
                      </div>
                      <h4 class="font-bold text-base text-[var(--text-primary)] leading-snug" x-text="paper.title"></h4>
                      <p class="text-xs text-[var(--text-secondary)] font-medium" x-text="(paper.authors || []).join(', ')"></p>
                    </div>

                    <button 
                      class="btn btn-secondary btn-sm shrink-0" 
                      @click="addCitationToProject(paper)"
                      title="Guardar esta cita en el proyecto"
                    >
                      <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                      <span>Vincular Cita</span>
                    </button>
                  </div>

                  <p class="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-3" x-text="paper.abstract || 'Sin resumen disponible.'"></p>

                  <div class="flex items-center gap-4 text-xs text-[var(--text-muted)] pt-2 border-t border-[var(--border-subtle)]">
                    <span x-show="paper.venue" class="truncate" x-text="paper.venue"></span>
                    <a x-show="paper.doi" :href="'https://doi.org/' + paper.doi" target="_blank" class="text-blue-600 hover:underline font-mono text-[11px]" x-text="'DOI: ' + paper.doi"></a>
                    <a x-show="paper.open_access_pdf" :href="paper.open_access_pdf" target="_blank" class="text-emerald-600 hover:underline text-[11px] flex items-center gap-1">
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
                <p class="text-sm text-[var(--text-secondary)]">Aún no has vinculado citas a este proyecto. Realiza una búsqueda académica para agregarlas.</p>
                <button class="btn btn-primary btn-sm" @click="activeSubTab = 'search'">Buscar Literatura</button>
              </div>
            ` : `
              <div class="space-y-4">
                <div class="flex items-center justify-between text-xs text-[var(--text-muted)] px-1">
                  <span>Total de fuentes bibliográficas vinculadas: <strong class="text-[var(--text-primary)]">${citations.length}</strong></span>
                </div>

                ${citations.map((c, idx) => `
                  <div class="card p-5 space-y-3">
                    <div class="flex items-start justify-between gap-4">
                      <div class="space-y-1">
                        <span class="badge badge-note text-[10px]">${c.source || 'academic'}</span>
                        <h4 class="font-bold text-sm text-[var(--text-primary)]">${c.title}</h4>
                        <p class="text-xs text-[var(--text-secondary)]">${(c.authors || []).join(', ')} (${c.year || 's.f.'})</p>
                      </div>
                      <span class="text-xs font-mono text-[var(--text-muted)]">#${idx + 1}</span>
                    </div>

                    ${c.apa_formatted ? `
                      <div class="p-3 rounded bg-[var(--bg-subtle)] text-xs border border-[var(--border-subtle)]">
                        <p class="font-semibold text-blue-600 mb-0.5">Formato APA 7ª Edición:</p>
                        <p class="italic text-[var(--text-primary)]">${c.apa_formatted}</p>
                      </div>
                    ` : ''}

                    <div class="flex items-center gap-4 text-xs text-[var(--text-muted)] pt-2 border-t border-[var(--border-subtle)]">
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
                <p class="text-xs text-[var(--text-secondary)] mt-0.5">Comprueba si una afirmación que deseas incluir en tu tesis está respaldada empíricamente por la literatura indexada.</p>
              </div>

              <div class="space-y-3">
                <textarea 
                  x-model="claimText" 
                  rows="3" 
                  placeholder="Escribe la afirmación que deseas verificar contra la literatura..."
                  class="w-full text-sm"
                ></textarea>

                <button 
                  class="btn btn-primary" 
                  @click="verifyClaim()" 
                  :disabled="isVerifyingClaim || !claimText.trim()"
                >
                  <span x-show="!isVerifyingClaim">Verificar Respaldo Empírico</span>
                  <span x-show="isVerifyingClaim">Verificando en ChromaDB...</span>
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

              <div class="text-xs space-y-2">
                <p class="text-[var(--text-secondary)]">Nivel de Confianza: <strong class="tabular-nums" x-text="Math.round((claimVerdict?.confidence_score || 0) * 100) + '%'"></strong></p>
                <p x-show="claimVerdict?.refuting_or_missing_reason" class="text-amber-600 dark:text-amber-400" x-text="claimVerdict?.refuting_or_missing_reason"></p>
              </div>
            </div>

          </div>

        </div>
      `;
    }
  };
}
