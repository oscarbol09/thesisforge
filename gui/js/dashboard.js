/**
 * ThesisForge — Dashboard Component
 * Manages project portfolio view, filtering, telemetry cards, and project deletion.
 */

function dashboardComponent() {
  return {
    searchQuery: '',
    levelFilter: 'all',
    isDeleting: false,
    deleteTargetId: null,

    get filteredProjects() {
      const projects = Alpine.store('app').projects || [];
      return projects.filter(p => {
        const matchesSearch = !this.searchQuery.trim() || 
          p.title.toLowerCase().includes(this.searchQuery.toLowerCase());
        const matchesLevel = this.levelFilter === 'all' || p.academic_level === this.levelFilter;
        return matchesSearch && matchesLevel;
      });
    },

    get telemetry() {
      const projects = Alpine.store('app').projects || [];
      return {
        total: projects.length,
        inDrafting: projects.filter(p => p.phase === 'drafting').length,
        completed: projects.filter(p => p.phase === 'completed').length,
      };
    },

    async openProject(projectId, targetTab = 'advisor') {
      await Alpine.store('app').selectProject(projectId);
      Alpine.store('app').activeTab = targetTab;
    },

    async confirmDeleteProject(projectId, projectTitle) {
      if (!confirm(`¿Estás seguro de que deseas eliminar permanentemente el proyecto "${projectTitle}"?\nEsta acción no se puede deshacer.`)) {
        return;
      }

      try {
        await Alpine.store('app').api(`/api/projects/${projectId}`, { method: 'DELETE' });
        Alpine.store('app').toast('info', 'Proyecto eliminado', `El proyecto ha sido eliminado correctamente.`);
        
        if (Alpine.store('app').activeProjectId === projectId) {
          Alpine.store('app').selectProject(null);
        }
        await Alpine.store('app').fetchProjects();
      } catch (err) {
        // Toast handled in api()
      }
    },

    render() {
      const projects = this.filteredProjects;
      const totalProjects = (Alpine.store('app').projects || []).length;
      const app = Alpine.store('app');

      return `
        <div class="space-y-8 max-w-7xl mx-auto">
          
          <!-- Header & Telemetry Bento -->
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Portafolio de Investigaciones</h2>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Administra tus proyectos de grado, tesis de posgrado e investigaciones en curso.</p>
            </div>
            
            <div class="flex items-center gap-3">
              <button class="btn btn-primary" @click="$store.app.showCreateModal = true">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                <span>Crear Proyecto</span>
              </button>
            </div>
          </div>

          <!-- Quick Metrics Bar -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="card p-4 flex items-center gap-4">
              <div class="w-10 h-10 rounded-md bg-blue-100 dark:bg-blue-950/60 text-blue-600 flex items-center justify-center shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Total Proyectos</p>
                <p class="text-xl font-bold tabular-nums text-[var(--text-primary)]">${this.telemetry.total}</p>
              </div>
            </div>

            <div class="card p-4 flex items-center gap-4">
              <div class="w-10 h-10 rounded-md bg-amber-100 dark:bg-amber-950/60 text-amber-600 flex items-center justify-center shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">En Redacción</p>
                <p class="text-xl font-bold tabular-nums text-[var(--text-primary)]">${this.telemetry.inDrafting}</p>
              </div>
            </div>

            <div class="card p-4 flex items-center gap-4">
              <div class="w-10 h-10 rounded-md bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 flex items-center justify-center shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Culminados</p>
                <p class="text-xl font-bold tabular-nums text-[var(--text-primary)]">${this.telemetry.completed}</p>
              </div>
            </div>
          </div>

          <!-- Filter & Search Controls -->
          <div class="flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div class="relative w-full sm:w-80">
              <input 
                type="search" 
                x-model="searchQuery" 
                placeholder="Buscar por título..." 
                class="w-full pl-9"
              >
              <svg class="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-3 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </div>

            <div class="flex items-center gap-2 w-full sm:w-auto">
              <select x-model="levelFilter" class="w-full sm:w-48 text-xs">
                <option value="all">Todos los niveles</option>
                <option value="pregrado">Pregrado</option>
                <option value="maestria">Maestría</option>
                <option value="doctorado">Doctorado</option>
              </select>
            </div>
          </div>

          <!-- UI State 1: Zero Projects (Empty State with CTA) -->
          ${totalProjects === 0 ? `
            <div class="card p-12 text-center max-w-lg mx-auto space-y-4">
              <div class="w-16 h-16 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center mx-auto">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
              </div>
              <div>
                <h3 class="font-bold text-lg text-[var(--text-primary)]">Comienza tu Primer Trabajo de Grado</h3>
                <p class="text-sm text-[var(--text-secondary)] mt-1">Crea un proyecto para estructurar tu pregunta de investigación, buscar literatura indexada y redactar bajo normas APA 7.</p>
              </div>
              <button class="btn btn-primary btn-lg" @click="$store.app.showCreateModal = true">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                <span>Crear Primer Proyecto</span>
              </button>
            </div>
          ` : ''}

          <!-- UI State 2: Search yielded 0 results -->
          ${totalProjects > 0 && projects.length === 0 ? `
            <div class="card p-8 text-center max-w-md mx-auto space-y-3">
              <p class="text-sm text-[var(--text-secondary)]">No se encontraron proyectos que coincidan con los filtros aplicados.</p>
              <button class="btn btn-secondary btn-sm" @click="searchQuery = ''; levelFilter = 'all';">Limpiar filtros</button>
            </div>
          ` : ''}

          <!-- UI State 3: Project Cards Grid (Ideal State) -->
          ${projects.length > 0 ? `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              ${projects.map(p => {
                const isSelected = app.activeProjectId === p.id;
                const progressPct = p.total_sections > 0 ? Math.round((p.approved_sections / p.total_sections) * 100) : 0;
                
                return `
                  <div class="card flex flex-col justify-between ${isSelected ? 'ring-2 ring-blue-500 border-transparent shadow-md' : ''}">
                    <div class="card-body space-y-4">
                      <div class="flex items-start justify-between gap-2">
                        <span class="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">${p.academic_level}</span>
                        <span class="${app.getPhaseBadgeClass(p.phase)}">${app.getPhaseLabel(p.phase)}</span>
                      </div>
                      
                      <div>
                        <h4 
                          class="font-bold text-base leading-snug text-[var(--text-primary)] cursor-pointer hover:text-blue-600 transition-colors line-clamp-2"
                          @click="openProject('${p.id}', 'advisor')"
                        >
                          ${p.title}
                        </h4>
                        <p class="text-xs text-[var(--text-muted)] mt-1">ID: <span class="font-mono">${p.id}</span></p>
                      </div>

                      <!-- Progress Bar -->
                      <div class="space-y-1.5 pt-2">
                        <div class="flex justify-between text-xs font-medium">
                          <span class="text-[var(--text-secondary)]">Avance de Capítulos</span>
                          <span class="tabular-nums font-semibold text-[var(--text-primary)]">${p.approved_sections}/${p.total_sections} (${progressPct}%)</span>
                        </div>
                        <div class="h-2 w-full bg-[var(--bg-subtle)] rounded-full overflow-hidden">
                          <div class="h-full bg-blue-600 transition-all duration-300" style="width: ${progressPct}%"></div>
                        </div>
                      </div>
                    </div>

                    <div class="card-footer flex items-center justify-between text-xs text-[var(--text-muted)]">
                      <span>Actualizado: ${app.formatDate(p.updated_at)}</span>
                      <div class="flex items-center gap-1">
                        <button 
                          class="btn btn-ghost btn-sm text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/50" 
                          title="Eliminar proyecto"
                          @click="confirmDeleteProject('${p.id}', '${p.title.replace(/'/g, "\\'")}')"
                        >
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        </button>
                        <button 
                          class="btn btn-secondary btn-sm"
                          @click="openProject('${p.id}', 'advisor')"
                        >
                          <span>Abrir</span>
                          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                        </button>
                      </div>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          ` : ''}

        </div>
      `;
    }
  };
}
