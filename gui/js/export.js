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

    render() {
      const project = Alpine.store('app').activeProject;
      if (!project) {
        return `
          <div class="card p-12 text-center max-w-md mx-auto space-y-4">
            <h3 class="font-bold text-lg text-[var(--text-primary)]">Ningún Proyecto Seleccionado</h3>
            <p class="text-sm text-[var(--text-secondary)]">Selecciona un proyecto para exportar a Microsoft Word (.docx).</p>
            <button class="btn btn-primary" @click="$store.app.activeTab = 'dashboard'">Ir al Panel de Proyectos</button>
          </div>
        `;
      }

      const totalSections = project.sections?.length || 0;
      const approvedSections = project.sections?.filter(s => s.status === 'approved').length || 0;

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
              <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Compilador Microsoft Word APA 7ª Edición</h2>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Genera un documento .docx oficial con márgenes de 2.54 cm, portada, numeración y bibliografía formateada.</p>
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
                <p class="text-xs text-[var(--text-secondary)]">${approvedSections} de ${totalSections} secciones aprobadas en el proyecto.</p>
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
                <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Institución / Universidad</label>
                <input type="text" x-model="options.institution_name" placeholder="Ej. Universidad Nacional" class="w-full text-xs">
              </div>
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Facultad / Programa Académico</label>
                <input type="text" x-model="options.faculty_or_program" placeholder="Ej. Facultad de Ingeniería" class="w-full text-xs">
              </div>
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Nombre del Autor / Estudiante</label>
                <input type="text" x-model="options.author_name" placeholder="Nombre completo" class="w-full text-xs">
              </div>
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Nombre del Asesor / Director</label>
                <input type="text" x-model="options.advisor_name" placeholder="Director de tesis" class="w-full text-xs">
              </div>
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Ciudad y País</label>
                <input type="text" x-model="options.city_and_country" placeholder="Ej. Bogotá, Colombia" class="w-full text-xs">
              </div>
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Año de Presentación</label>
                <input type="number" x-model="options.year" class="w-full text-xs">
              </div>
            </div>

            <h3 class="font-bold text-base text-[var(--text-primary)] border-b border-[var(--border-subtle)] pb-2 pt-4">Directrices Tipográficas APA 7</h3>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Fuente Tipográfica</label>
                <select x-model="options.font_name" class="w-full text-xs">
                  <option value="Times New Roman">Times New Roman (12 pt)</option>
                  <option value="Calibri">Calibri (11 pt)</option>
                  <option value="Arial">Arial (11 pt)</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Interlineado</label>
                <select x-model="options.line_spacing" class="w-full text-xs">
                  <option value="2.0">Doble (2.0 — Estándar APA 7)</option>
                  <option value="1.5">1.5 líneas</option>
                  <option value="1.0">Sencillo (1.0)</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Márgenes</label>
                <select x-model="options.margin_inches" class="w-full text-xs">
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
            <div class="pt-4 flex justify-end">
              <button 
                class="btn btn-primary btn-lg" 
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
