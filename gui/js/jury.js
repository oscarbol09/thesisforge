/**
 * ThesisForge — Jury Evaluation Component
 * Renders multi-agent doctoral jury audit reports, dimensional juror scores, and detected methodological issues.
 */

function juryComponent() {
  return {
    latestReport: null,
    evaluationHistory: [],
    isAuditing: false,
    isLoadingReport: false,

    async init() {
      await this.loadLatestReport();
    },

    async loadLatestReport() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isLoadingReport = true;
      try {
        const report = await Alpine.store('app').api(`/api/jury/projects/${project.id}/evaluations/latest`, { silent: true });
        this.latestReport = report || null;
      } catch (err) {
        this.latestReport = null;
      } finally {
        this.isLoadingReport = false;
      }
    },

    async runJuryAudit() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isAuditing = true;
      try {
        const report = await Alpine.store('app').api(`/api/jury/projects/${project.id}/audit`, {
          method: 'POST'
        });
        this.latestReport = report;
        Alpine.store('app').toast('success', 'Auditoría Completada', `El tribunal emitió el dictamen: ${this.getVerdictLabel(report.verdict)}.`);
        await Alpine.store('app').refreshActiveProject();
      } catch (err) {
        // Error toast handled in api()
      } finally {
        this.isAuditing = false;
      }
    },

    getVerdictLabel(verdict) {
      const labels = {
        aprobado_con_distincion: 'Aprobado con Distinción (Laude)',
        aprobado: 'Aprobado',
        modificaciones_menores: 'Modificaciones Menores',
        modificaciones_mayores: 'Modificaciones Mayores',
        no_aprobado: 'No Aprobado (Rechazado)',
      };
      return labels[verdict] || verdict;
    },

    getVerdictBadgeClass(verdict) {
      const classes = {
        aprobado_con_distincion: 'badge-completed',
        aprobado: 'badge-completed',
        modificaciones_menores: 'badge-minor',
        modificaciones_mayores: 'badge-major',
        no_aprobado: 'badge-critical',
      };
      return `badge ${classes[verdict] || 'badge-setup'} text-xs py-1 px-2.5`;
    },

    getJurorRoleLabel(role) {
      const roles = {
        metodologo: 'Metodólogo & Epistemólogo',
        especialista_tematico: 'Especialista Temático',
        auditor_estadistico: 'Auditor Estadístico y Cuantitativo',
        abogado_del_diablo: 'Evaluador Crítico (Abogado del Diablo)',
      };
      return roles[role] || role;
    },

    render() {
      const project = Alpine.store('app').activeProject;
      if (!project) {
        return `
          <div class="card p-12 text-center max-w-md mx-auto space-y-4">
            <h3 class="font-bold text-lg text-[var(--text-primary)]">Ningún Proyecto Seleccionado</h3>
            <p class="text-sm text-[var(--text-secondary)]">Selecciona un proyecto para someterlo a la auditoría del tribunal de jurados.</p>
            <button class="btn btn-primary" @click="$store.app.activeTab = 'dashboard'">Ir al Panel de Proyectos</button>
          </div>
        `;
      }

      const report = this.latestReport;

      return `
        <div class="space-y-8 max-w-6xl mx-auto">
          
          <!-- Header & Audit Trigger -->
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                <span>Fase 5</span>
                <span>•</span>
                <span>Tribunal Académico Multi-Agente</span>
              </div>
              <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Auditoría Científica y Dictamen de Jurado</h2>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Evaluación rigurosa por 4 roles doctorales independientes para detectar sesgos e inconsistencias antes de la defensa.</p>
            </div>

            <button 
              class="btn btn-primary btn-lg shrink-0" 
              @click="runJuryAudit()" 
              :disabled="isAuditing"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
              <span x-show="!isAuditing">Auditar con Tribunal Doctoral</span>
              <span x-show="isAuditing">Auditoría en proceso...</span>
            </button>
          </div>

          <!-- UI State 1: No Evaluation Yet -->
          ${!report && !this.isAuditing ? `
            <div class="card p-12 text-center max-w-lg mx-auto space-y-4">
              <div class="w-16 h-16 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
              </div>
              <div>
                <h3 class="font-bold text-lg text-[var(--text-primary)]">Proyecto Pendiente de Evaluación</h3>
                <p class="text-sm text-[var(--text-secondary)] mt-1">Haz clic en el botón superior para convocar al panel de 4 jurados y auditar la totalidad del manuscrito.</p>
              </div>
            </div>
          ` : ''}

          <!-- UI State 2: Evaluation Report Display -->
          ${report ? `
            <div class="space-y-6">
              
              <!-- Master Verdict Banner -->
              <div class="card p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-l-4 ${report.overall_score >= 80 ? 'border-l-emerald-500' : 'border-l-amber-500'}">
                <div class="space-y-1">
                  <div class="flex items-center gap-3">
                    <span class="${this.getVerdictBadgeClass(report.verdict)}">${this.getVerdictLabel(report.verdict)}</span>
                    <span class="text-xs text-[var(--text-muted)]">ID Informe: <code class="font-mono text-[11px]">${report.id}</code></span>
                  </div>
                  <h3 class="text-xl font-bold text-[var(--text-primary)]">Dictamen Oficial del Tribunal Académico</h3>
                </div>

                <div class="flex items-baseline gap-2 bg-[var(--bg-subtle)] p-3 rounded-lg border border-[var(--border-subtle)]">
                  <span class="text-xs text-[var(--text-muted)] font-semibold uppercase">Calificación Global:</span>
                  <span class="text-2xl font-bold tabular-nums text-blue-600">${report.overall_score.toFixed(1)} / 100</span>
                </div>
              </div>

              <!-- Dictamen Synthesis -->
              <div class="card p-5 space-y-2 bg-[var(--bg-subtle)]">
                <h4 class="font-bold text-xs uppercase tracking-wider text-[var(--text-muted)]">Síntesis del Dictamen</h4>
                <p class="text-sm text-[var(--text-primary)] leading-relaxed">${report.summary_dictamen}</p>
              </div>

              <!-- 4 Jurors Dimensional Scores Grid -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                ${(report.juror_evaluations || []).map(eval => `
                  <div class="card p-5 space-y-4">
                    <div class="flex items-start justify-between pb-3 border-b border-[var(--border-subtle)]">
                      <div>
                        <span class="text-[10px] font-mono uppercase text-blue-600 font-semibold">${this.getJurorRoleLabel(eval.juror_role)}</span>
                        <h4 class="font-bold text-base text-[var(--text-primary)]">${eval.juror_name}</h4>
                        <p class="text-xs text-[var(--text-secondary)]">${eval.dimension_name}</p>
                      </div>
                      <span class="text-lg font-bold tabular-nums ${eval.score >= 80 ? 'text-emerald-600' : 'text-amber-600'}">${eval.score.toFixed(0)} pts</span>
                    </div>

                    <p class="text-xs text-[var(--text-secondary)] leading-relaxed">${eval.feedback}</p>

                    <div class="grid grid-cols-2 gap-3 text-xs pt-2">
                      <div>
                        <p class="font-semibold text-emerald-600 text-[11px] mb-1">Fortalezas:</p>
                        <ul class="list-disc list-inside space-y-0.5 text-[var(--text-secondary)] text-[11px]">
                          ${(eval.strengths || []).map(s => `<li>${s}</li>`).join('')}
                        </ul>
                      </div>
                      <div>
                        <p class="font-semibold text-amber-600 text-[11px] mb-1">Observaciones:</p>
                        <ul class="list-disc list-inside space-y-0.5 text-[var(--text-secondary)] text-[11px]">
                          ${(eval.flaws || []).map(f => `<li>${f}</li>`).join('')}
                        </ul>
                      </div>
                    </div>
                  </div>
                `).join('')}
              </div>

              <!-- Identified Issues & Recommendations Table -->
              ${(report.issues || []).length > 0 ? `
                <div class="card overflow-hidden">
                  <div class="card-header">
                    <h4 class="font-bold text-sm text-[var(--text-primary)]">Observaciones y Defectos Identificados (${report.issues.length})</h4>
                  </div>
                  <div class="divide-y divide-[var(--border-subtle)]">
                    ${report.issues.map(iss => `
                      <div class="p-4 space-y-2 text-xs">
                        <div class="flex items-center justify-between">
                          <span class="badge badge-${iss.severity === 'critical' ? 'critical' : iss.severity === 'major' ? 'major' : 'minor'}">${iss.severity}</span>
                          <span class="text-[var(--text-muted)] font-mono text-[11px]">${iss.chapter_or_section}</span>
                        </div>
                        <h5 class="font-bold text-sm text-[var(--text-primary)]">${iss.title}</h5>
                        <p class="text-[var(--text-secondary)]">${iss.description}</p>
                        <div class="p-2.5 rounded bg-[var(--bg-subtle)] text-[var(--text-primary)] border border-[var(--border-subtle)] mt-1">
                          <strong class="text-blue-600">Recomendación:</strong> ${iss.recommendation}
                        </div>
                      </div>
                    `).join('')}
                  </div>
                </div>
              ` : ''}

            </div>
          ` : ''}

        </div>
      `;
    }
  };
}
