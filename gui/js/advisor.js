/**
 * ThesisForge — Methodological Advisor Component
 * Orchestrates guided scientific interview steps, consistency audits, and methodology approval.
 */

function advisorComponent() {
  return {
    statusData: null,
    currentStep: 'setup',
    isLoadingStatus: false,
    isProcessingStep: false,
    isApproving: false,
    userInput: '',
    advisorResponse: null,

    // Form inputs synchronized across steps
    formData: {
      title: '',
      academic_level: 'pregrado',
      area_of_study: '',
      topic: '',
      research_problem: '',
      justification: '',
      scope_limitations: '',
      research_question: '',
      general_objective: '',
      specific_objectives: [''],
      hypothesis: '',
      variables: [''],
      methodology: {
        approach: 'cuantitativo',
        design: '',
        population: '',
        sample: '',
        instruments: [''],
        analysis_technique: '',
      }
    },

    stepLabels: {
      setup: '1. Inicialización',
      topic_and_area: '2. Área y Tema',
      problem_statement: '3. Planteamiento del Problema',
      research_question: '4. Pregunta de Investigación',
      objectives: '5. Objetivos',
      hypothesis: '6. Hipótesis y Variables',
      methodology_design: '7. Diseño Metodológico',
      consistency_audit: '8. Auditoría de Consistencia',
      approved: '9. Ficha Aprobada',
    },

    stepDescriptions: {
      setup: 'Configuración inicial y delimitación del nivel académico.',
      topic_and_area: 'Definición del campo disciplinar, línea de investigación y tema central.',
      problem_statement: 'Caracterización de la situación problemática, justificación e impacto.',
      research_question: 'Formulación de la pregunta rectora de la investigación.',
      objectives: 'Estructuración del objetivo general (taxonomía de Bloom) y objetivos específicos.',
      hypothesis: 'Declaración de conjeturas contrastables y operacionalización de variables.',
      methodology_design: 'Selección del enfoque, diseño, población, muestra e instrumentos.',
      consistency_audit: 'Evaluación algorítmica de congruencia epistemológica y metodológica.',
      approved: 'Ficha metodológica formalmente validada y lista para la fase de literatura.',
    },

    async init() {
      await this.loadAdvisorStatus();
    },

    async loadAdvisorStatus() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isLoadingStatus = true;
      try {
        const data = await Alpine.store('app').api(`/api/advisor/${project.id}/status`);
        this.statusData = data;
        this.currentStep = data.current_step || 'setup';
        
        // Sync formData with current project state
        if (project) {
          this.formData.title = project.title || '';
          this.formData.academic_level = project.academic_level || 'pregrado';
          this.formData.area_of_study = project.area_of_study || '';
          this.formData.topic = project.topic || '';
          this.formData.research_problem = project.research_problem || '';
          this.formData.justification = project.justification || '';
          this.formData.scope_limitations = project.scope_limitations || '';
          this.formData.research_question = project.research_question || '';
          this.formData.general_objective = project.general_objective || '';
          this.formData.specific_objectives = project.specific_objectives?.length ? [...project.specific_objectives] : [''];
          this.formData.hypothesis = project.hypothesis || '';
          this.formData.variables = project.variables?.length ? [...project.variables] : [''];
          
          if (project.methodology) {
            this.formData.methodology = {
              approach: project.methodology.approach || 'cuantitativo',
              design: project.methodology.design || '',
              population: project.methodology.population || '',
              sample: project.methodology.sample || '',
              instruments: project.methodology.instruments?.length ? [...project.methodology.instruments] : [''],
              analysis_technique: project.methodology.analysis_technique || '',
            };
          }
        }
      } catch (err) {
        console.error('Error loading advisor status:', err);
      } finally {
        this.isLoadingStatus = false;
      }
    },

    // Array manipulation helpers for dynamic lists
    addSpecificObjective() {
      this.formData.specific_objectives.push('');
    },
    removeSpecificObjective(idx) {
      if (this.formData.specific_objectives.length > 1) {
        this.formData.specific_objectives.splice(idx, 1);
      }
    },

    addVariable() {
      this.formData.variables.push('');
    },
    removeVariable(idx) {
      if (this.formData.variables.length > 1) {
        this.formData.variables.splice(idx, 1);
      }
    },

    addInstrument() {
      this.formData.methodology.instruments.push('');
    },
    removeInstrument(idx) {
      if (this.formData.methodology.instruments.length > 1) {
        this.formData.methodology.instruments.splice(idx, 1);
      }
    },

    async processCurrentStep() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isProcessingStep = true;
      this.advisorResponse = null;

      try {
        const payload = {
          step: this.currentStep,
          user_input: this.userInput,
          form_data: {
            ...this.formData,
            specific_objectives: this.formData.specific_objectives.filter(s => s.trim()),
            variables: this.formData.variables.filter(v => v.trim()),
            methodology: {
              ...this.formData.methodology,
              instruments: this.formData.methodology.instruments.filter(i => i.trim()),
            }
          }
        };

        const result = await Alpine.store('app').api(`/api/advisor/${project.id}/step`, {
          method: 'POST',
          body: JSON.stringify(payload)
        });

        this.advisorResponse = result.advisor_response || result.message || 'Paso procesado correctamente.';
        Alpine.store('app').toast('success', 'Paso Completado', `Se ha validado el paso: ${this.stepLabels[this.currentStep]}`);
        
        await Alpine.store('app').refreshActiveProject();
        await this.loadAdvisorStatus();
        this.userInput = '';
      } catch (err) {
        // Error toast handled by api()
      } finally {
        this.isProcessingStep = false;
      }
    },

    async approveMethodology() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isApproving = true;
      try {
        await Alpine.store('app').api(`/api/advisor/${project.id}/approve`, { method: 'POST' });
        Alpine.store('app').toast('success', 'Metodología Aprobada', 'El proyecto avanzó a la Fase 2: Literatura & RAG.');
        await Alpine.store('app').refreshActiveProject();
        Alpine.store('app').activeTab = 'literature';
      } catch (err) {
        // Error toast handled by api()
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
            <p class="text-sm text-[var(--text-secondary)]">Selecciona o crea un proyecto desde el panel principal para iniciar el asesor metodológico.</p>
            <button class="btn btn-primary" @click="$store.app.activeTab = 'dashboard'">Ir al Panel de Proyectos</button>
          </div>
        `;
      }

      const progressPct = this.statusData?.progress_percentage || 0;
      const allSteps = ['setup', 'topic_and_area', 'problem_statement', 'research_question', 'objectives', 'hypothesis', 'methodology_design', 'consistency_audit', 'approved'];

      return `
        <div class="space-y-8 max-w-5xl mx-auto">
          
          <!-- Header and Breadcrumb -->
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                <span>Fase 1</span>
                <span>•</span>
                <span>Asesor Metodológico</span>
              </div>
              <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">${project.title}</h2>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Estructura la base epistemológica y metodológica con orientación socrática.</p>
            </div>
            
            <div class="flex items-center gap-3">
              <span class="text-xs text-[var(--text-muted)]">Avance de la Ficha:</span>
              <span class="text-sm font-bold tabular-nums text-blue-600">${progressPct}%</span>
            </div>
          </div>

          <!-- Stepper Progress Navigation -->
          <div class="card p-4">
            <div class="h-1.5 w-full bg-[var(--bg-subtle)] rounded-full overflow-hidden mb-4">
              <div class="h-full bg-blue-600 transition-all duration-300" style="width: ${progressPct}%"></div>
            </div>

            <div class="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-9 gap-2">
              ${allSteps.map((step, idx) => {
                const isCurrent = this.currentStep === step;
                const isCompleted = this.statusData?.completed_steps?.includes(step);
                
                let stepClass = 'bg-[var(--bg-subtle)] text-[var(--text-muted)] border-[var(--border-subtle)]';
                if (isCurrent) {
                  stepClass = 'bg-blue-50 text-blue-700 border-blue-300 dark:bg-blue-950/60 dark:text-blue-400 dark:border-blue-800 font-bold';
                } else if (isCompleted) {
                  stepClass = 'bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900';
                }

                return `
                  <button 
                    @click="currentStep = '${step}'"
                    class="p-2 rounded-md border text-center transition-all ${stepClass} flex flex-col items-center justify-center gap-1 min-h-[56px]"
                    title="${this.stepLabels[step]}"
                  >
                    <span class="text-[11px] font-mono leading-none">${idx + 1}</span>
                    <span class="text-[10px] leading-tight truncate w-full px-1">${step.replace('_', ' ')}</span>
                  </button>
                `;
              }).join('')}
            </div>
          </div>

          <!-- Main Interactive Advisor Workspace -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            <!-- Left 2 Cols: Form Content for Current Step -->
            <div class="lg:col-span-2 space-y-6">
              
              <div class="card">
                <div class="card-header">
                  <div>
                    <h3 class="font-bold text-base text-[var(--text-primary)]">${this.stepLabels[this.currentStep]}</h3>
                    <p class="text-xs text-[var(--text-secondary)] mt-0.5">${this.stepDescriptions[this.currentStep]}</p>
                  </div>
                </div>

                <div class="card-body space-y-5">
                  
                  <!-- Step 1: Setup & Level -->
                  ${this.currentStep === 'setup' ? `
                    <div class="space-y-4">
                      <div>
                        <label for="adv-title" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Título Tentativo de la Tesis *</label>
                        <input id="adv-title" type="text" x-model="formData.title" class="w-full" placeholder="Título del proyecto">
                      </div>
                      <div>
                        <label for="adv-level" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Nivel Académico *</label>
                        <select id="adv-level" x-model="formData.academic_level" class="w-full">
                          <option value="pregrado">Pregrado (Licenciatura / Ingeniería)</option>
                          <option value="maestria">Maestría (Magíster / M.Sc.)</option>
                          <option value="doctorado">Doctorado (Ph.D.)</option>
                        </select>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 2: Topic & Area -->
                  ${this.currentStep === 'topic_and_area' ? `
                    <div class="space-y-4">
                      <div>
                        <label for="adv-area" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Área o Campo de Conocimiento *</label>
                        <input id="adv-area" type="text" x-model="formData.area_of_study" class="w-full" placeholder="Ej. Inteligencia Artificial, Educación Superior">
                      </div>
                      <div>
                        <label for="adv-topic" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Tema Delimitado *</label>
                        <input id="adv-topic" type="text" x-model="formData.topic" class="w-full" placeholder="Ej. Integración de RAG para reducción de alucinaciones">
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 3: Problem Statement -->
                  ${this.currentStep === 'problem_statement' ? `
                    <div class="space-y-4">
                      <div>
                        <label for="adv-problem" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Planteamiento del Problema *</label>
                        <textarea id="adv-problem" x-model="formData.research_problem" rows="4" class="w-full text-sm" placeholder="Describe los síntomas, causas y consecuencias de la problemática..."></textarea>
                      </div>
                      <div>
                        <label for="adv-justification" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Justificación del Estudio</label>
                        <textarea id="adv-justification" x-model="formData.justification" rows="3" class="w-full text-sm" placeholder="Relevancia teórica, metodológica y práctica..."></textarea>
                      </div>
                      <div>
                        <label for="adv-scope" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Alcance y Delimitación</label>
                        <input id="adv-scope" type="text" x-model="formData.scope_limitations" class="w-full" placeholder="Delimitación temporal, espacial y conceptual">
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 4: Research Question -->
                  ${this.currentStep === 'research_question' ? `
                    <div class="space-y-4">
                      <div>
                        <label for="adv-question" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Pregunta Principal de Investigación *</label>
                        <input id="adv-question" type="text" x-model="formData.research_question" class="w-full font-medium" placeholder="¿En qué medida la arquitectura RAG impacta la tasa de alucinaciones en...?">
                        <p class="text-xs text-[var(--text-muted)] mt-1">La pregunta debe ser precisa, delimitada y vinculada a las variables del estudio.</p>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 5: Objectives -->
                  ${this.currentStep === 'objectives' ? `
                    <div class="space-y-4">
                      <div>
                        <label for="adv-gen-obj" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Objetivo General *</label>
                        <input id="adv-gen-obj" type="text" x-model="formData.general_objective" class="w-full font-medium" placeholder="Evaluar el impacto de la arquitectura RAG mediante...">
                        <p class="text-xs text-[var(--text-muted)] mt-1">Debe iniciar con un verbo en infinitivo (Taxonomía de Bloom/Investigación).</p>
                      </div>
                      <div class="space-y-2">
                        <div class="flex items-center justify-between">
                          <span class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Objetivos Específicos</span>
                          <button type="button" class="btn btn-secondary btn-sm" @click="addSpecificObjective()">+ Agregar Objetivo</button>
                        </div>
                        <template x-for="(obj, idx) in formData.specific_objectives" :key="idx">
                          <div class="flex items-center gap-2">
                            <span class="text-xs font-mono text-[var(--text-muted)] w-6" x-text="idx + 1 + '.'"></span>
                            <input type="text" x-model="formData.specific_objectives[idx]" :aria-label="'Objetivo específico ' + (idx + 1)" class="flex-1" placeholder="Objetivo específico...">
                            <button type="button" class="btn btn-ghost btn-sm text-red-500" @click="removeSpecificObjective(idx)" :aria-label="'Eliminar objetivo ' + (idx + 1)" x-show="formData.specific_objectives.length > 1">
                              <svg class="w-4 h-4" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                            </button>
                          </div>
                        </template>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 6: Hypothesis & Variables -->
                  ${this.currentStep === 'hypothesis' ? `
                    <div class="space-y-4">
                      <div>
                        <label for="adv-hypothesis" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Hipótesis Central (si aplica)</label>
                        <textarea id="adv-hypothesis" x-model="formData.hypothesis" rows="3" class="w-full text-sm" placeholder="Existe una correlación estadísticamente significativa entre..."></textarea>
                      </div>
                      <div class="space-y-2">
                        <div class="flex items-center justify-between">
                          <span class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Variables de Estudio</span>
                          <button type="button" class="btn btn-secondary btn-sm" @click="addVariable()">+ Variable</button>
                        </div>
                        <template x-for="(v, idx) in formData.variables" :key="idx">
                          <div class="flex items-center gap-2">
                            <span class="text-xs font-mono text-[var(--text-muted)] w-6" x-text="'V' + (idx + 1)"></span>
                            <input type="text" x-model="formData.variables[idx]" :aria-label="'Variable de estudio ' + (idx + 1)" class="flex-1" placeholder="Variable independiente / dependiente...">
                            <button type="button" class="btn btn-ghost btn-sm text-red-500" @click="removeVariable(idx)" :aria-label="'Eliminar variable ' + (idx + 1)" x-show="formData.variables.length > 1">
                              <svg class="w-4 h-4" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                            </button>
                          </div>
                        </template>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 7: Methodology Design -->
                  ${this.currentStep === 'methodology_design' ? `
                    <div class="space-y-4">
                      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label for="adv-approach" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Enfoque *</label>
                          <select id="adv-approach" x-model="formData.methodology.approach" class="w-full">
                            <option value="cuantitativo">Cuantitativo (Hipotético-Deductivo)</option>
                            <option value="cualitativo">Cualitativo (Inductivo-Fenomenológico)</option>
                            <option value="mixto">Mixto (Integrado Triangulado)</option>
                          </select>
                        </div>
                        <div>
                          <label for="adv-design" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Diseño de Investigación</label>
                          <input id="adv-design" type="text" x-model="formData.methodology.design" class="w-full" placeholder="Ej. Cuasiexperimental pretest-postest">
                        </div>
                      </div>
                      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label for="adv-population" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Población</label>
                          <input id="adv-population" type="text" x-model="formData.methodology.population" class="w-full" placeholder="Ej. 120 estudiantes de medicina">
                        </div>
                        <div>
                          <label for="adv-sample" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Muestra y Muestreo</label>
                          <input id="adv-sample" type="text" x-model="formData.methodology.sample" class="w-full" placeholder="Ej. Muestra probabilística n=64">
                        </div>
                      </div>
                      <div>
                        <label for="adv-tech" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Técnica de Análisis</label>
                        <input id="adv-tech" type="text" x-model="formData.methodology.analysis_technique" class="w-full" placeholder="Ej. Prueba t de Student para muestras relacionadas, ANOVA">
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 8: Consistency Audit -->
                  ${this.currentStep === 'consistency_audit' ? `
                    <div class="space-y-4">
                      <div class="p-4 rounded-md bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-xs text-[var(--text-secondary)] space-y-2">
                        <p class="font-semibold text-blue-900 dark:text-blue-300">Auditoría Algorítmica de Coherencia Metodológica:</p>
                        <p>El motor evaluará si tu objetivo general responde a la pregunta de investigación, si tus hipótesis se alinean a las variables declaradas y si el diseño cuantitativo/cualitativo es adecuado.</p>
                      </div>

                      <div class="space-y-2 text-xs">
                        <div class="flex items-center justify-between p-2.5 rounded bg-[var(--bg-subtle)]">
                          <span>Pregunta Principal vs. Objetivo General</span>
                          <span class="badge badge-success">Alineado</span>
                        </div>
                        <div class="flex items-center justify-between p-2.5 rounded bg-[var(--bg-subtle)]">
                          <span>Enfoque Metodológico vs. Instrumentos</span>
                          <span class="badge badge-success">Coherente</span>
                        </div>
                        <div class="flex items-center justify-between p-2.5 rounded bg-[var(--bg-subtle)]">
                          <span>Hipótesis y Variables</span>
                          <span class="badge badge-note">Contrastable</span>
                        </div>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 9: Approved State -->
                  ${this.currentStep === 'approved' ? `
                    <div class="p-6 text-center space-y-4">
                      <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                      </div>
                      <div>
                        <h4 class="font-bold text-base text-[var(--text-primary)]">Ficha Metodológica Completada</h4>
                        <p class="text-xs text-[var(--text-secondary)] mt-1">Tu proyecto cuenta con una base de formulación científica rigurosa y validada.</p>
                      </div>
                      <button class="btn btn-primary btn-lg" @click="approveMethodology()" :disabled="isApproving">
                        <span x-show="!isApproving">Aprobar y Pasar a Fase 2: Literatura & RAG</span>
                        <span x-show="isApproving">Aprobando...</span>
                      </button>
                    </div>
                  ` : ''}

                </div>

                <!-- Footer Actions -->
                ${this.currentStep !== 'approved' ? `
                  <div class="card-footer flex items-center justify-between">
                    <div class="flex-1 max-w-sm mr-4">
                      <input 
                        type="text" 
                        x-model="userInput" 
                        placeholder="Pregunta o instrucción adicional para el Asesor..." 
                        class="w-full text-xs"
                      >
                    </div>
                    <button 
                      class="btn btn-primary btn-sm" 
                      @click="processCurrentStep()" 
                      :disabled="isProcessingStep"
                    >
                      <span x-show="!isProcessingStep">Validar Paso con Asesor</span>
                      <span x-show="isProcessingStep">Procesando...</span>
                    </button>
                  </div>
                ` : ''}
              </div>

            </div>

            <!-- Right 1 Col: Advisor Guidance & AI Feedback -->
            <div class="space-y-4">
              <div class="card p-5 space-y-4 bg-gradient-to-b from-[var(--bg-surface)] to-[var(--bg-subtle)]">
                <div class="flex items-center gap-2">
                  <div class="w-7 h-7 rounded-md bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                    IA
                  </div>
                  <div>
                    <h4 class="font-bold text-sm text-[var(--text-primary)]">Asesor Metodológico</h4>
                    <span class="text-[10px] text-[var(--text-muted)] font-mono">Orientación en Vivo</span>
                  </div>
                </div>

                <div class="text-xs text-[var(--text-secondary)] space-y-3 leading-relaxed">
                  <div x-show="isProcessingStep" class="flex items-center gap-2 text-blue-600 py-4">
                    <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    <span>Analizando coherencia del paso...</span>
                  </div>

                  <div x-show="!isProcessingStep && advisorResponse" class="p-3 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                    <p class="font-semibold text-blue-600 mb-1">Dictamen del Asesor:</p>
                    <p x-text="advisorResponse" class="whitespace-pre-line"></p>
                  </div>

                  <div x-show="!isProcessingStep && !advisorResponse">
                    <p>Completa los campos del formulario correspondientes al paso actual y haz clic en <strong>Validar Paso</strong>.</p>
                    <p class="mt-2">El asesor verificará la precisión taxonómica y la coherencia antes de habilitar el siguiente hito.</p>
                  </div>
                </div>
              </div>
            </div>

          </div>

        </div>
      `;
    }
  };
}
