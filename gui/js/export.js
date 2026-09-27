/**
 * ThesisForge — Export Component
 * Configures APA 7th Edition Word (.docx) compilation and handles binary blob file downloads.
 */

function exportComponent() {
  return {
    isExporting: false,
    options: {
      format: 'docx',
      include_cover_page: true,
      include_table_of_contents: true,
      include_references: true,
      font_name: 'Times New Roman',
      font_size_pt: 12,
      line_spacing: 2.0,
      margin_inches: 1.0,
      institution_name: '',
      faculty_or_program: '',
      author_name: '',
      advisor_name: '',
      city_and_country: '',
      year: new Date().getFullYear(),
    },

    async downloadDocx() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isExporting = true;
      try {
        const response = await fetch(`/api/export/projects/${project.id}/docx`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(this.options),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          const errMsg = errData.message || `Error HTTP ${response.status}`;
          Alpine.store('app').toast('error', 'Error al compilar Word', errMsg);
          return;
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // Extract filename from header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `tesis_${project.id}_apa7.docx`;
        if (contentDisposition && contentDisposition.includes('filename=')) {
          filename = contentDisposition.split('filename=')[1].replace(/["']/g, '').trim();
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        Alpine.store('app').toast('success', 'Descarga Completada', `El documento "${filename}" fue compilado y descargado exitosamente.`);
      } catch (err) {
        Alpine.store('app').toast('error', 'Error de Descarga', err.message);
      } finally {
        this.isExporting = false;
      }
    },

    async downloadBibtex() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isExportingBib = true;
      try {
        const response = await fetch(`/api/export/projects/${project.id}/bibtex`);

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          const errMsg = errData.message || `Error HTTP ${response.status}`;
          Alpine.store('app').toast('error', 'Error al exportar BibTeX', errMsg);
          return;
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `bibliografia_${project.id}.bib`;
        if (contentDisposition && contentDisposition.includes('filename=')) {
          filename = contentDisposition.split('filename=')[1].replace(/["']/g, '').trim();
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        Alpine.store('app').toast('success', 'BibTeX Descargado', `El archivo "${filename}" fue exportado para Zotero, Mendeley y Overleaf.`);
      } catch (err) {
        Alpine.store('app').toast('error', 'Error de Descarga', err.message);
      } finally {
        this.isExportingBib = false;
      }
    },

    render() {
      const project = Alpine.store('app').activeProject;
      if (!project) {
        return `
          <div class="card p-12 text-center max-w-md mx-auto space-y-4">
            <h3 class="font-bold text-lg text-[var(--text-primary)]">Ningún Proyecto Seleccionado</h3>
            <p class="text-sm text-[var(--text-secondary)]">Selecciona un proyecto para exportar a Microsoft Word (.docx) o BibTeX (.bib).</p>
            <button class="btn btn-primary" @click="$store.app.activeTab = 'dashboard'">Ir al Panel de Proyectos</button>
          </div>
        `;
      }

      const totalSections = project.sections?.length || 0;
      const approvedSections = project.sections?.filter(s => s.status === 'approved').length || 0;
      const totalCitations = project.validated_citations?.length || 0;

      return `
        <div class="space-y-8 max-w-4xl mx-auto">
          
          <!-- Header -->
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                <span>Fase 4</span>
                <span>•</span>
                <span>Exportación & Compilación Editorial</span>
              </div>
              <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Compilador Editorial APA 7 & BibTeX</h2>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Genera un documento Word (.docx) oficial con normas APA 7ª Edición o exporta la bibliografía en formato BibTeX (.bib) para Zotero, Mendeley y Overleaf.</p>
            </div>

            <div class="flex items-center gap-2 shrink-0">
              <button 
                class="btn btn-outline btn-sm flex items-center gap-1.5" 
                @click="downloadBibtex()" 
                :disabled="isExportingBib || totalCitations === 0"
                title="Exportar archivo .bib compatible con Overleaf y gestores bibliográficos"
              >
                <svg class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                <span x-show="!isExportingBib">Exportar BibTeX (${totalCitations})</span>
                <span x-show="isExportingBib">Exportando .bib...</span>
              </button>
            </div>
          </div>

          <!-- Readiness Telemetry Banner -->
          <div class="card p-4 bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-900 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                APA
              </div>
              <div>
                <p class="text-xs font-bold text-[var(--text-primary)]">Estado de las Secciones a Compilar:</p>
                <p class="text-xs text-[var(--text-secondary)]">${approvedSections} de ${totalSections} secciones aprobadas • ${totalCitations} referencias bibliográficas vinculadas.</p>
              </div>
            </div>
            <span class="badge ${approvedSections === totalSections && totalSections > 0 ? 'badge-success' : 'badge-note'}">
              ${approvedSections === totalSections && totalSections > 0 ? 'Listo para entrega' : 'Compilación de borrador'}
            </span>
          </div>

          <!-- Configuration Form Bento -->
          <div class="card p-6 space-y-6">
            
            <h3 class="font-bold text-base text-[var(--text-primary)] border-b border-[var(--border-subtle)] pb-2">Metadatos de la Portada Académica</h3>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label for="export-institution" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Institución / Universidad</label>
                <input id="export-institution" type="text" x-model="options.institution_name" placeholder="Ej. Universidad Nacional" class="w-full text-xs">
              </div>
              <div>
                <label for="export-faculty" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Facultad / Programa Académico</label>
                <input id="export-faculty" type="text" x-model="options.faculty_or_program" placeholder="Ej. Facultad de Ingeniería" class="w-full text-xs">
              </div>
              <div>
                <label for="export-author" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Nombre del Autor / Estudiante</label>
                <input id="export-author" type="text" x-model="options.author_name" placeholder="Nombre completo" class="w-full text-xs">
              </div>
              <div>
                <label for="export-advisor" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Nombre del Asesor / Director</label>
                <input id="export-advisor" type="text" x-model="options.advisor_name" placeholder="Director de tesis" class="w-full text-xs">
              </div>
              <div>
                <label for="export-city" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Ciudad y País</label>
                <input id="export-city" type="text" x-model="options.city_and_country" placeholder="Ej. Bogotá, Colombia" class="w-full text-xs">
              </div>
              <div>
                <label for="export-year" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Año de Presentación</label>
                <input id="export-year" type="number" x-model="options.year" class="w-full text-xs">
              </div>
            </div>

            <h3 class="font-bold text-base text-[var(--text-primary)] border-b border-[var(--border-subtle)] pb-2 pt-4">Directrices Tipográficas APA 7</h3>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <label for="export-font" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Fuente Tipográfica</label>
                <select id="export-font" x-model="options.font_name" class="w-full text-xs">
                  <option value="Times New Roman">Times New Roman (12 pt)</option>
                  <option value="Calibri">Calibri (11 pt)</option>
                  <option value="Arial">Arial (11 pt)</option>
                </select>
              </div>
              <div>
                <label for="export-spacing" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Interlineado</label>
                <select id="export-spacing" x-model="options.line_spacing" class="w-full text-xs">
                  <option value="2.0">Doble (2.0 — Estándar APA 7)</option>
                  <option value="1.5">1.5 líneas</option>
                  <option value="1.0">Sencillo (1.0)</option>
                </select>
              </div>
              <div>
                <label for="export-margin" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Márgenes</label>
                <select id="export-margin" x-model="options.margin_inches" class="w-full text-xs">
                  <option value="1.0">2.54 cm (1.0 pulgada — APA 7)</option>
                  <option value="1.5">3.81 cm (Encuadernación)</option>
                </select>
              </div>
            </div>

            <div class="space-y-2 pt-2 border-t border-[var(--border-subtle)]">
              <label class="flex items-center gap-2 cursor-pointer text-xs">
                <input type="checkbox" x-model="options.include_cover_page" class="rounded text-blue-600">
                <span class="font-medium text-[var(--text-primary)]">Incluir Portada Oficial de Estudiante</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer text-xs">
                <input type="checkbox" x-model="options.include_table_of_contents" class="rounded text-blue-600">
                <span class="font-medium text-[var(--text-primary)]">Incluir Tabla de Contenidos (Índice General)</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer text-xs">
                <input type="checkbox" x-model="options.include_references" class="rounded text-blue-600">
                <span class="font-medium text-[var(--text-primary)]">Incluir Lista de Referencias con Sangría Francesa</span>
              </label>
            </div>

            <!-- Export Button CTA -->
            <div class="pt-4 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-[var(--border-subtle)]">
              <button 
                type="button"
                class="btn btn-outline btn-md w-full sm:w-auto flex items-center justify-center gap-2" 
                @click="downloadBibtex()" 
                :disabled="isExportingBib || totalCitations === 0"
              >
                <svg class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                <span x-show="!isExportingBib">Descargar BibTeX (.bib)</span>
                <span x-show="isExportingBib">Descargando BibTeX...</span>
              </button>

              <button 
                type="button"
                class="btn btn-primary btn-lg w-full sm:w-auto flex items-center justify-center gap-2" 
                @click="downloadDocx()" 
                :disabled="isExporting"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                <span x-show="!isExporting">Compilar y Descargar Manuscrito (.docx)</span>
                <span x-show="isExporting">Compilando documento APA 7...</span>
              </button>
            </div>

          </div>

        </div>
      `;
    }
  };
}
