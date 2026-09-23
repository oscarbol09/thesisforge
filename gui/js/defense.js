/**
 * ThesisForge — Defense Simulator Component
 * Conducts turn-based socratic oral thesis defense simulations with real-time feedback and grading.
 */

function defenseComponent() {
  return {
    activeSession: null,
    studentAnswer: '',
    isStarting: false,
    isSubmittingTurn: false,
    totalTurns: 4,

    async init() {
      await this.loadActiveSession();
    },

    async loadActiveSession() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      try {
        const sessions = await Alpine.store('app').api(`/api/defense/projects/${project.id}/sessions`, { silent: true });
        if (sessions && sessions.length > 0) {
          // Take the most recent session
          this.activeSession = sessions[0];
        }
      } catch (err) {
        this.activeSession = null;
      }
    },

    async startDefense() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isStarting = true;
      try {
        const session = await Alpine.store('app').api(`/api/defense/projects/${project.id}/start?turns=${this.totalTurns}`, {
          method: 'POST'
        });
        this.activeSession = session;
        this.studentAnswer = '';
        Alpine.store('app').toast('success', 'Defensa Iniciada', 'El tribunal ha formulado la primera pregunta de sustentación.');
      } catch (err) {
        // Error toast handled in api()
      } finally {
        this.isStarting = false;
      }
    },

    async submitAnswer() {
      if (!this.activeSession || !this.studentAnswer.trim()) return;

      this.isSubmittingTurn = true;
      try {
        const updated = await Alpine.store('app').api(`/api/defense/sessions/${this.activeSession.id}/reply`, {
          method: 'POST',
          body: JSON.stringify({
            student_answer: this.studentAnswer.trim()
          })
        });

        this.activeSession = updated;
        this.studentAnswer = '';
        Alpine.store('app').toast('success', 'Réplica Evaluada', 'El jurado evaluó tu respuesta.');
        await Alpine.store('app').refreshActiveProject();
      } catch (err) {
        // Error toast handled in api()
      } finally {
        this.isSubmittingTurn = false;
      }
    },

    getJurorRoleLabel(role) {
      const roles = {
        metodologo: 'Metodólogo',
        especialista_tematico: 'Especialista Temático',
        auditor_estadistico: 'Auditor Estadístico',
        abogado_del_diablo: 'Abogado del Diablo',
      };
      return roles[role] || role;
    },

    getDefenseStatusLabel(status) {
      const labels = {
        in_progress: 'En Curso',
        passed_with_honors: 'Aprobado con Honores (Magna Cum Laude)',
        passed: 'Aprobado Satisfactoriamente',
        needs_revision: 'Requiere Revisión Posterior',
        failed: 'No Aprobado',
      };
      return labels[status] || status;
    },

    render() {
      const project = Alpine.store('app').activeProject;
      if (!project) {
        return `
          <div class="card p-12 text-center max-w-md mx-auto space-y-4">
            <h3 class="font-bold text-lg text-[var(--text-primary)]">Ningún Proyecto Seleccionado</h3>
            <p class="text-sm text-[var(--text-secondary)]">Selecciona un proyecto para iniciar la simulación socrática de defensa oral.</p>
            <button class="btn btn-primary" @click="$store.app.activeTab = 'dashboard'">Ir al Panel de Proyectos</button>
          </div>
        `;
      }

      const session = this.activeSession;
      const isCompleted = session && session.status !== 'in_progress';
      const currentTurn = session?.turns?.[session.current_turn_index];

      return `
        <div class="space-y-8 max-w-5xl mx-auto">
          
          <!-- Header -->
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                <span>Fase 6</span>
                <span>•</span>
                <span>Sustentación Oral Socrática</span>
              </div>
              <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Simulador Interactivo de Defensa de Tesis</h2>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Enfrenta rondas de preguntas desafiantes formuladas por los jurados y recibe retroalimentación inmediata sobre tus réplicas.</p>
            </div>

            ${!session || isCompleted ? `
              <button 
                class="btn btn-primary btn-lg shrink-0" 
                @click="startDefense()" 
                :disabled="isStarting"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <span x-show="!isStarting">${session ? 'Iniciar Nueva Sustentación' : 'Iniciar Sustentación Oral'}</span>
                <span x-show="isStarting">Iniciando sesión...</span>
              </button>
            ` : ''}
          </div>

          <!-- Empty State (No Session Yet) -->
          ${!session ? `
            <div class="card p-12 text-center max-w-lg mx-auto space-y-4">
              <div class="w-16 h-16 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"/></svg>
              </div>
              <div>
                <h3 class="font-bold text-lg text-[var(--text-primary)]">Preparación para la Sustentación Oral</h3>
                <p class="text-sm text-[var(--text-secondary)] mt-1">Inicia una simulación de 4 turnos para medir tu capacidad argumentativa y dominio del manuscrito.</p>
              </div>
            </div>
          ` : ''}

          <!-- Active Session Canvas -->
          ${session ? `
            <div class="space-y-6">
              
              <!-- Session Header Telemetry -->
              <div class="card p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-md bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                    ${session.current_turn_index + 1}/${session.total_turns}
                  </div>
                  <div>
                    <h4 class="font-bold text-sm text-[var(--text-primary)]">Turno Actual: ${session.current_turn_index + 1} de ${session.total_turns}</h4>
                    <p class="text-xs text-[var(--text-muted)]">Estado: <span class="font-semibold text-blue-600">${this.getDefenseStatusLabel(session.status)}</span></p>
                  </div>
                </div>

                ${session.final_score !== null && session.final_score !== undefined ? `
                  <div class="flex items-baseline gap-2 bg-[var(--bg-subtle)] p-2.5 rounded-lg border border-[var(--border-subtle)]">
                    <span class="text-xs text-[var(--text-muted)] font-semibold">Puntaje Final:</span>
                    <span class="text-xl font-bold tabular-nums text-emerald-600">${session.final_score.toFixed(1)} / 100</span>
                  </div>
                ` : ''}
              </div>

              <!-- Turns Conversation Timeline -->
              <div class="space-y-6">
                ${(session.turns || []).map((t, idx) => `
                  <div class="card p-6 space-y-4 ${idx === session.current_turn_index && !t.is_answered ? 'ring-2 ring-blue-500 border-transparent shadow-md' : ''}">
                    
                    <!-- Juror Question Row -->
                    <div class="flex items-start gap-4">
                      <div class="w-9 h-9 rounded-full bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-400 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                        J${idx + 1}
                      </div>
                      <div class="space-y-1.5 flex-1">
                        <div class="flex items-center gap-2">
                          <span class="font-bold text-sm text-[var(--text-primary)]">${t.juror_name}</span>
                          <span class="badge badge-note text-[10px]">${this.getJurorRoleLabel(t.juror_role)}</span>
                          <span class="text-xs text-[var(--text-muted)]">• Eje: ${t.focus_area}</span>
                        </div>
                        <p class="text-sm font-medium text-[var(--text-primary)] leading-relaxed">${t.question}</p>
                      </div>
                    </div>

                    <!-- Student Answer (if answered) -->
                    ${t.student_answer ? `
                      <div class="flex items-start gap-4 pl-6 sm:pl-10 border-l-2 border-emerald-500/40 mt-3">
                        <div class="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                          Tú
                        </div>
                        <div class="space-y-1 flex-1">
                          <span class="font-semibold text-xs text-[var(--text-muted)]">Tu Réplica:</span>
                          <p class="text-xs text-[var(--text-secondary)] leading-relaxed">${t.student_answer}</p>
                        </div>
                      </div>
                    ` : ''}

                    <!-- Juror Feedback & Score -->
                    ${t.juror_feedback ? `
                      <div class="p-3.5 rounded-lg bg-[var(--bg-subtle)] text-xs border border-[var(--border-subtle)] space-y-1.5 mt-2">
                        <div class="flex items-center justify-between">
                          <span class="font-semibold text-blue-600">Evaluación del Jurado:</span>
                          <span class="font-bold tabular-nums ${t.turn_score >= 80 ? 'text-emerald-600' : 'text-amber-600'}">Calificación: ${t.turn_score?.toFixed(0) || 0} pts</span>
                        </div>
                        <p class="text-[var(--text-secondary)] leading-relaxed">${t.juror_feedback}</p>
                      </div>
                    ` : ''}

                    <!-- Active Input (if this turn is unanswered) -->
                    ${idx === session.current_turn_index && !t.is_answered ? `
                      <div class="pt-4 border-t border-[var(--border-subtle)] space-y-3">
                        <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Redacta tu Réplica Argumentativa:</label>
                        <textarea 
                          x-model="studentAnswer" 
                          rows="4" 
                          placeholder="Sustenta tu postura con respaldo metodológico, datos empíricos o asumiendo honestamente las limitaciones..." 
                          class="w-full text-sm"
                          :disabled="isSubmittingTurn"
                        ></textarea>

                        <div class="flex justify-end">
                          <button 
                            class="btn btn-primary btn-sm" 
                            @click="submitAnswer()" 
                            :disabled="isSubmittingTurn || !studentAnswer.trim()"
                          >
                            <span x-show="!isSubmittingTurn">Emitir Réplica al Jurado</span>
                            <span x-show="isSubmittingTurn">Evaluando respuesta...</span>
                          </button>
                        </div>
                      </div>
                    ` : ''}

                  </div>
                `).join('')}
              </div>

              <!-- Completed Summary Banner -->
              ${isCompleted ? `
                <div class="card p-6 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-center space-y-3">
                  <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                  </div>
                  <div>
                    <h3 class="font-bold text-lg text-emerald-900 dark:text-emerald-200">Sustentación Oral Culminada</h3>
                    <p class="text-sm text-emerald-700 dark:text-emerald-300 mt-1">${session.final_remarks || 'Has completado todos los turnos de sustentación con éxito.'}</p>
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
