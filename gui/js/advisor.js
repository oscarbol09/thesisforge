/**
 * ThesisForge — Methodological Advisor Component
 * Orchestrates guided scientific interview steps, epistemological adaptations,
 * consistency audits, and methodology approval.
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
      // Quantitative & Qualitative Epistemological Fields
      hypothesis: '',
      hypothesis_null: '',
      variables: [''],
      operationalized_variables: [],
      qualitative_categories: [],
      methodology: {
        approach: 'cuantitativo',
        paradigm: 'positivista',
        design: '',
        population: '',
        sample: '',
        sampling_technique: 'probabilistico_aleatorio',
        unit_of_analysis: '',
        instruments: [''],
        analysis_technique: '',
        data_collection_procedure: '',
        temporal_scope: 'transversal',
        spatial_setting: '',
        technique_instrument_pairs: [
          { technique: 'Encuesta', instrument: '', target_objective: '' }
        ]
      }
    },

    stepLabels: {
      setup: '1. Inicialización',
      topic_and_area: '2. Área y Tema',
      problem_statement: '3. Planteamiento del Problema',
      research_question: '4. Pregunta de Investigación',
      objectives: '5. Objetivos',
      hypothesis: '6. Hipótesis / Supuestos y Variables / Categorías',
      methodology_design: '7. Diseño Metodológico & Técnicas',
      consistency_audit: '8. Auditoría de Consistencia',
      approved: '9. Ficha Aprobada',
    },

    stepDescriptions: {
      setup: 'Configuración inicial, delimitación del nivel académico y título tentativo.',
      topic_and_area: 'Definición del campo disciplinar, línea de investigación y delimitación temática.',
      problem_statement: 'Caracterización de la situación problemática, justificación, alcance y delimitaciones.',
      research_question: 'Formulación de la pregunta rectora y subpreguntas de investigación.',
      objectives: 'Estructuración del objetivo general (taxonomía de Bloom) y objetivos específicos secuenciales.',
      hypothesis: 'Declaración epistemológica adaptada: Hipótesis/Variables (Cuantitativo) o Supuestos/Categorías (Cualitativo).',
      methodology_design: 'Enfoque, diseño, población, muestra, técnicas e instrumentos estructurados.',
      consistency_audit: 'Evaluación algorítmica de coherencia interna (Problema → Pregunta → Objetivos → Métodos).',
      approved: 'Ficha metodológica formalmente validada y lista para la fase de literatura.',
    },

    async init() {
      await this.loadAdvisorStatus(false);
    },

    selectStep(stepKey) {
      this.currentStep = stepKey;
      this.advisorResponse = null;
    },

    async loadAdvisorStatus(preserveCurrentStep = true) {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isLoadingStatus = true;
      try {
        const data = await Alpine.store('app').api(`/api/advisor/${project.id}/status`);
        this.statusData = data;
        
        // Only set currentStep from server on initial load or if not explicitly navigating
        if (!preserveCurrentStep && (!this.currentStep || this.currentStep === 'setup')) {
          this.currentStep = data.current_step || 'setup';
        }
        
        // Sync formData with current project state safely without erasing active user work
        if (project) {
          if (project.title) this.formData.title = project.title;
          if (project.academic_level) this.formData.academic_level = project.academic_level;
          if (project.area_of_study) this.formData.area_of_study = project.area_of_study;
          if (project.topic) this.formData.topic = project.topic;
          if (project.research_problem) this.formData.research_problem = project.research_problem;
          if (project.justification) this.formData.justification = project.justification;
          if (project.scope_limitations) this.formData.scope_limitations = project.scope_limitations;
          if (project.research_question) this.formData.research_question = project.research_question;
          if (project.general_objective) this.formData.general_objective = project.general_objective;
          
          if (project.specific_objectives && project.specific_objectives.length > 0) {
            this.formData.specific_objectives = [...project.specific_objectives];
          }
          if (project.hypothesis) this.formData.hypothesis = project.hypothesis;
          
          if (project.variables && project.variables.length > 0) {
            this.formData.variables = [...project.variables];
          }
          
          if (project.operationalized_variables && project.operationalized_variables.length > 0) {
            this.formData.operationalized_variables = JSON.parse(JSON.stringify(project.operationalized_variables));
          }
          
          if (project.qualitative_categories && project.qualitative_categories.length > 0) {
            this.formData.qualitative_categories = JSON.parse(JSON.stringify(project.qualitative_categories));
          }

          if (project.methodology) {
            const m = project.methodology;
            if (m.approach) this.formData.methodology.approach = m.approach;
            if (m.paradigm) this.formData.methodology.paradigm = m.paradigm;
            if (m.design) this.formData.methodology.design = m.design;
            if (m.population) this.formData.methodology.population = m.population;
            if (m.sample) this.formData.methodology.sample = m.sample;
            if (m.sampling_technique) this.formData.methodology.sampling_technique = m.sampling_technique;
            if (m.unit_of_analysis) this.formData.methodology.unit_of_analysis = m.unit_of_analysis;
            if (m.analysis_technique) this.formData.methodology.analysis_technique = m.analysis_technique;
            if (m.data_collection_procedure) this.formData.methodology.data_collection_procedure = m.data_collection_procedure;
            
            if (m.instruments && m.instruments.length > 0) {
              this.formData.methodology.instruments = [...m.instruments];
              // Hydrate technique_instrument_pairs if empty
              if (this.formData.methodology.technique_instrument_pairs.length <= 1 && !this.formData.methodology.technique_instrument_pairs[0].instrument) {
                this.formData.methodology.technique_instrument_pairs = m.instruments.map(inst => {
                  let tech = 'Encuesta';
                  let cleanInst = inst;
                  if (inst.includes(':')) {
                    const parts = inst.split(':');
                    tech = parts[0].trim();
                    cleanInst = parts.slice(1).join(':').trim();
                  } else if (inst.toLowerCase().includes('entrevista')) {
                    tech = 'Entrevista';
                  } else if (inst.toLowerCase().includes('observaci')) {
                    tech = 'Observación';
                  } else if (inst.toLowerCase().includes('grupo focal') || inst.toLowerCase().includes('focus')) {
                    tech = 'Grupo Focal';
                  }
                  return { technique: tech, instrument: cleanInst, target_objective: '' };
                });
              }
            }
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

    addOperationalizedVariable() {
      this.formData.operationalized_variables.push({
        name: '',
        variable_type: 'independiente',
        conceptual_definition: '',
        operational_definition: '',
        dimensions: [''],
        indicators: [''],
        measurement_scale: 'ordinal',
        instrument_name: '',
      });
    },
    removeOperationalizedVariable(idx) {
      this.formData.operationalized_variables.splice(idx, 1);
    },

    addQualitativeCategory() {
      this.formData.qualitative_categories.push({
        name: '',
        category_type: 'central',
        definition: '',
        subcategories: [''],
        coding_criteria: '',
        saturation_indicator: '',
      });
    },
    removeQualitativeCategory(idx) {
      this.formData.qualitative_categories.splice(idx, 1);
    },

    addTechniqueInstrumentPair() {
      this.formData.methodology.technique_instrument_pairs.push({
        technique: 'Encuesta',
        instrument: '',
        target_objective: '',
      });
    },
    removeTechniqueInstrumentPair(idx) {
      if (this.formData.methodology.technique_instrument_pairs.length > 1) {
        this.formData.methodology.technique_instrument_pairs.splice(idx, 1);
      }
    },

    syncInstrumentsFromPairs() {
      const pairs = this.formData.methodology.technique_instrument_pairs || [];
      const compiled = pairs
        .filter(p => p.instrument && p.instrument.trim())
        .map(p => p.technique ? `${p.technique}: ${p.instrument.trim()}` : p.instrument.trim());
      
      if (compiled.length > 0) {
        this.formData.methodology.instruments = compiled;
      }
    },

    async processCurrentStep() {
      const project = Alpine.store('app').activeProject;
      if (!project) return;

      this.isProcessingStep = true;
      this.advisorResponse = null;

      // Sync technique-instrument pairs into instruments array
      this.syncInstrumentsFromPairs();

      // If qualitative, keep variables list synced with category names
      if (this.formData.methodology.approach === 'cualitativo' && this.formData.qualitative_categories.length > 0) {
        const catNames = this.formData.qualitative_categories.map(c => c.name).filter(Boolean);
        if (catNames.length > 0) {
          this.formData.variables = catNames;
        }
      }

      try {
        const payload = {
          step: this.currentStep,
          user_input: this.userInput,
          form_data: {
            ...this.formData,
            specific_objectives: this.formData.specific_objectives.filter(s => s && s.trim()),
            variables: this.formData.variables.filter(v => v && v.trim()),
            operationalized_variables: this.formData.operationalized_variables.filter(v => v.name && v.name.trim()),
            qualitative_categories: this.formData.qualitative_categories.filter(c => c.name && c.name.trim()),
            methodology: {
              ...this.formData.methodology,
              instruments: this.formData.methodology.instruments.filter(i => i && i.trim()),
            }
          }
        };

        const result = await Alpine.store('app').api(`/api/advisor/${project.id}/step`, {
          method: 'POST',
          body: JSON.stringify(payload)
        });

        this.advisorResponse = result.ai_analysis?.message || result.advisor_response || result.message || 'Paso validado y guardado correctamente.';
        Alpine.store('app').toast('success', 'Paso Guardado', `Ficha actualizada: ${this.stepLabels[this.currentStep]}`);
        
        await Alpine.store('app').refreshActiveProject();
        await this.loadAdvisorStatus(true);
        
        // Auto-advance to next step if returned
        if (result.next_step && result.next_step !== this.currentStep) {
          this.currentStep = result.next_step;
        }
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
        Alpine.store('app').toast('success', 'Metodología Aprobada', 'El proyecto avanzó con éxito a la Fase 2: Literatura & RAG.');
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
      const approach = this.formData.methodology.approach || 'cuantitativo';

      return `
        <div class="space-y-8 max-w-5xl mx-auto">
          
          <!-- Header and Breadcrumb -->
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                <span>Fase 1</span>
                <span>•</span>
                <span>Asesor Metodológico Socrático</span>
                <span>•</span>
                <span class="text-blue-600 dark:text-blue-400 capitalize">${approach}</span>
              </div>
              <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">${project.title || 'Proyecto de Investigación'}</h2>
              <p class="text-sm text-[var(--text-secondary)] mt-1">Estructura la base epistemológica, metodológica y operativa con rigor científico.</p>
            </div>
            
            <div class="flex items-center gap-3">
              <span class="text-xs text-[var(--text-muted)]">Progreso de la Ficha:</span>
              <span class="text-sm font-bold tabular-nums text-blue-600">${progressPct}%</span>
            </div>
          </div>

          <!-- Stepper Progress Navigation (Clickable Tabs) -->
          <div class="card p-4">
            <div class="h-1.5 w-full bg-[var(--bg-subtle)] rounded-full overflow-hidden mb-4">
              <div class="h-full bg-blue-600 transition-all duration-300" style="width: ${progressPct}%"></div>
            </div>

            <div class="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-9 gap-2">
              ${allSteps.map((step, idx) => {
                const isCurrent = this.currentStep === step;
                const isCompleted = this.statusData?.completed_steps?.includes(step);
                
                let stepClass = 'bg-[var(--bg-subtle)] text-[var(--text-muted)] border-[var(--border-subtle)] hover:border-blue-300 hover:text-[var(--text-primary)]';
                if (isCurrent) {
                  stepClass = 'bg-blue-50 text-blue-700 border-blue-400 dark:bg-blue-950/60 dark:text-blue-400 dark:border-blue-700 font-bold shadow-sm';
                } else if (isCompleted) {
                  stepClass = 'bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900';
                }

                let shortLabel = step.replace('_', ' ');
                if (step === 'hypothesis') {
                  shortLabel = approach === 'cualitativo' ? 'Supuestos/Cat' : (approach === 'mixto' ? 'Hipót/Cat' : 'Hipótesis/Var');
                } else if (step === 'methodology_design') {
                  shortLabel = 'Diseño/Técnicas';
                }

                return `
                  <button 
                    @click="selectStep('${step}')"
                    class="p-2 rounded-md border text-center transition-all ${stepClass} flex flex-col items-center justify-center gap-1 min-h-[56px] cursor-pointer"
                    title="${this.stepLabels[step]}"
                  >
                    <span class="text-[11px] font-mono leading-none">${idx + 1}</span>
                    <span class="text-[10px] leading-tight truncate w-full px-1 capitalize">${shortLabel}</span>
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
                <div class="card-header flex items-center justify-between">
                  <div>
                    <h3 class="font-bold text-base text-[var(--text-primary)]">${this.stepLabels[this.currentStep]}</h3>
                    <p class="text-xs text-[var(--text-secondary)] mt-0.5">${this.stepDescriptions[this.currentStep]}</p>
                  </div>
                </div>

                <div class="card-body space-y-6">
                  
                  <!-- Step 1: Setup & Level -->
                  ${this.currentStep === 'setup' ? `
                    <div class="space-y-4">
                      <div>
                        <label for="adv-title" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Título Tentativo de la Tesis *</label>
                        <input id="adv-title" type="text" x-model="formData.title" class="w-full font-medium" placeholder="Título formal del proyecto de investigación">
                      </div>
                      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label for="adv-level" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Nivel Académico *</label>
                          <select id="adv-level" x-model="formData.academic_level" class="w-full">
                            <option value="pregrado">Pregrado (Licenciatura / Ingeniería)</option>
                            <option value="maestria">Maestría (Magíster / M.Sc.)</option>
                            <option value="doctorado">Doctorado (Ph.D.)</option>
                          </select>
                        </div>
                        <div>
                          <label for="adv-initial-approach" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Enfoque Metodológico Preliminar</label>
                          <select id="adv-initial-approach" x-model="formData.methodology.approach" class="w-full">
                            <option value="cuantitativo">Cuantitativo (Hipotético-Deductivo / Positivista)</option>
                            <option value="cualitativo">Cualitativo (Inductivo-Fenomenológico / Interpretativo)</option>
                            <option value="mixto">Mixto (Integrado / Triangulado)</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 2: Topic & Area -->
                  ${this.currentStep === 'topic_and_area' ? `
                    <div class="space-y-4">
                      <div>
                        <label for="adv-area" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Área o Campo de Conocimiento *</label>
                        <input id="adv-area" type="text" x-model="formData.area_of_study" class="w-full" placeholder="Ej. Inteligencia Artificial, Educación Médica, Ciencias Sociales">
                      </div>
                      <div>
                        <label for="adv-topic" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Tema Delimitado *</label>
                        <input id="adv-topic" type="text" x-model="formData.topic" class="w-full" placeholder="Ej. Integración de arquitecturas RAG para mitigar alucinaciones bibliográficas">
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 3: Problem Statement -->
                  ${this.currentStep === 'problem_statement' ? `
                    <div class="space-y-5">
                      <!-- 8 Movements Pedagogical Banner -->
                      <div class="p-3 bg-blue-50/70 dark:bg-blue-950/40 rounded-lg border border-blue-200 dark:border-blue-900 text-xs text-blue-900 dark:text-blue-300 space-y-1.5">
                        <div class="font-bold flex items-center gap-1.5">
                          <span>📐 Estructura Canónica en 8 Movimientos del Planteamiento:</span>
                        </div>
                        <p class="text-[11px] leading-relaxed text-blue-800 dark:text-blue-400">
                          <strong>1.</strong> Contexto Macro → <strong>2.</strong> Contexto Local → <strong>3.</strong> Evidencia Empírica Directa (síntomas locales) → <strong>4.</strong> Magnitud y Alcance → <strong>5.</strong> Consecuencias en 3 Niveles (Sujetos, Institución, Conocimiento) → <strong>6.</strong> Vacío de Conocimiento Crítico → <strong>7.</strong> Estado del Arte Acotado → <strong>8.</strong> Síntesis y Necesidad Imperativa.
                        </p>
                      </div>

                      <div>
                        <div class="flex items-center justify-between mb-1">
                          <label for="adv-problem" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Planteamiento y Descripción del Problema *</label>
                          <span class="text-[11px] text-[var(--text-muted)]">Los 8 Movimientos de la Problemática</span>
                        </div>
                        <textarea id="adv-problem" x-model="formData.research_problem" rows="6" class="w-full text-sm leading-relaxed" placeholder="1. Contexto Macro: Tendencia del fenómeno a nivel global/regional...&#10;2. Contexto Local: En la institución/entorno específico seleccionado...&#10;3. Evidencia Empírica Directa: Registros, métricas observadas o síntomas documentados...&#10;4. Magnitud: Población o procesos afectados...&#10;5. Consecuencias en 3 Niveles: Impacto en los sujetos, la organización y la disciplina...&#10;6. Vacío de Conocimiento: Qué aspectos específicos aún no han sido resueltos...&#10;7. Síntesis: Justificación de la necesidad imperativa de realizar la investigación aquí y ahora..."></textarea>
                      </div>

                      <div>
                        <div class="flex items-center justify-between mb-1">
                          <label for="adv-justification" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Justificación en 4 Dimensiones & Formulación Negativa</label>
                          <span class="text-[11px] text-[var(--text-muted)]">Teórica • Práctica • Metodológica • Educativa</span>
                        </div>
                        <textarea id="adv-justification" x-model="formData.justification" rows="4" class="w-full text-sm leading-relaxed" placeholder="• Dimensión Teórica: Vacío conceptual y modelos a contrastar...&#10;• Dimensión Práctica/Social: Utilidad tangible para la población y resolución de problemas...&#10;• Dimensión Metodológica: Nuevos instrumentos, algoritmos o protocolos aportados...&#10;• Dimensión Educativa/Institucional: Impacto formativo u organizacional...&#10;• Formulación Negativa: ¿Qué consecuencias adversas, pérdidas o vacíos persistirán si este estudio NO se realiza?"></textarea>
                      </div>

                      <div>
                        <div class="flex items-center justify-between mb-1">
                          <label for="adv-scope" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Delimitaciones & Limitaciones de la Investigación</label>
                          <span class="text-[11px] text-[var(--text-muted)]">Fronteras Elegidas vs. Restricciones en 4 Pasos</span>
                        </div>
                        <textarea id="adv-scope" x-model="formData.scope_limitations" rows="3" class="w-full text-sm leading-relaxed" placeholder="• Delimitación: Espacial (ciudad/sede), Temporal (2025-2026), Poblacional (cohorte específica) y Conceptual.&#10;• Limitaciones (Fórmula de 4 pasos): 1. Declaración de la restricción real -> 2. Efecto potencial -> 3. Estrategia de mitigación -> 4. Afirmación que el estudio NO realizará."></textarea>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 4: Research Question -->
                  ${this.currentStep === 'research_question' ? `
                    <div class="space-y-4">
                      <!-- 5 Components Pedagogical Banner -->
                      <div class="p-3 bg-blue-50/70 dark:bg-blue-950/40 rounded-lg border border-blue-200 dark:border-blue-900 text-xs text-blue-900 dark:text-blue-300 space-y-1">
                        <div class="font-bold flex items-center gap-1.5">
                          <span>🔬 Los 5 Componentes Anatómicos de la Pregunta Principal (PG):</span>
                        </div>
                        <p class="text-[11px] leading-relaxed text-blue-800 dark:text-blue-400">
                          <strong>1.</strong> Unidad de Análisis (sujetos/procesos) + <strong>2.</strong> Foco/Variables + <strong>3.</strong> Contexto delimitado + <strong>4.</strong> Temporalidad + <strong>5.</strong> Tipo de relación/proceso (asociativa, explicativa, fenomenológica). Evita preguntas dicotómicas (Sí/No) y verbos vacuos como 'analizar'.
                        </p>
                      </div>

                      <div>
                        <label for="adv-question" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Pregunta Principal / Rectoral de Investigación (PG) *</label>
                        <input id="adv-question" type="text" x-model="formData.research_question" class="w-full font-medium text-sm" placeholder="¿En qué medida la arquitectura RAG reduce las alucinaciones bibliográficas en tesistas de posgrado de la Universidad X durante 2025?">
                        <p class="text-xs text-[var(--text-muted)] mt-1.5">Formula interrogantes de alta resolución metodológica con partículas formales (ej. '¿En qué medida...?', '¿De qué manera...?', '¿Cómo interactúa...?').</p>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 5: Objectives -->
                  ${this.currentStep === 'objectives' ? `
                    <div class="space-y-5">
                      <!-- Golden Rule Pedagogical Banner -->
                      <div class="p-3 bg-blue-50/70 dark:bg-blue-950/40 rounded-lg border border-blue-200 dark:border-blue-900 text-xs text-blue-900 dark:text-blue-300 space-y-1">
                        <div class="font-bold flex items-center gap-1.5">
                          <span>⚖️ Regla de Oro de los Objetivos:</span>
                        </div>
                        <p class="text-[11px] leading-relaxed text-blue-800 dark:text-blue-400">
                          El <strong>Objetivo General</strong> debe ser la traducción isomórfica exacta de la <strong>Pregunta Principal</strong> en verbo infinitivo ($OG \equiv PG$). Los <strong>Objetivos Específicos</strong> expresan metas de conocimiento secuenciales (Diagnóstica → Diseño/Intervención → Evaluación), nunca tareas del cronograma ('revisar libros', 'aplicar encuestas').
                        </p>
                      </div>

                      <div>
                        <label for="adv-gen-obj" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Objetivo General (OG) *</label>
                        <input id="adv-gen-obj" type="text" x-model="formData.general_objective" class="w-full font-medium text-sm" placeholder="Determinar en qué medida la arquitectura RAG reduce las alucinaciones bibliográficas en tesistas de posgrado...">
                        <p class="text-xs text-[var(--text-muted)] mt-1">Inicia con un verbo en infinitivo medible correspondiente al alcance de la investigación (Determinar, Caracterizar, Evaluar, Demostrar, Comprender).</p>
                      </div>
                      
                      <div class="space-y-3 pt-2">
                        <div class="flex items-center justify-between">
                          <div>
                            <span class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Objetivos Específicos (Secuencia Metodológica: 3 a 5 Objetivos)</span>
                            <span class="text-[11px] text-[var(--text-muted)]">1. Fase Diagnóstica/Caracterización → 2. Fase de Diseño/Intervención → 3. Fase de Evaluación/Impacto</span>
                          </div>
                          <button type="button" class="btn btn-secondary btn-sm" @click="addSpecificObjective()">+ Agregar Objetivo</button>
                        </div>
                        
                        <div class="space-y-2">
                          <template x-for="(obj, idx) in formData.specific_objectives" :key="idx">
                            <div class="flex items-center gap-2">
                              <span class="text-xs font-mono font-semibold text-blue-600 dark:text-blue-400 w-7 shrink-0" x-text="'OE' + (idx + 1) + ':'"></span>
                              <input type="text" x-model="formData.specific_objectives[idx]" :aria-label="'Objetivo específico ' + (idx + 1)" class="flex-1 text-sm" placeholder="Verbo en infinitivo + variable/categoría + unidad de estudio + contexto...">
                              <button type="button" class="btn btn-ghost btn-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-950/40" @click="removeSpecificObjective(idx)" :aria-label="'Eliminar objetivo ' + (idx + 1)" x-show="formData.specific_objectives.length > 1">
                                <svg class="w-4 h-4" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                              </button>
                            </div>
                          </template>
                        </div>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 6: Hypothesis & Variables (Epistemologically Adapted) -->
                  ${this.currentStep === 'hypothesis' ? `
                    <div class="space-y-6">
                      
                      <!-- Approach Selector Banner -->
                      <div class="p-3.5 bg-[var(--bg-subtle)] rounded-lg border border-[var(--border-subtle)] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                          <span class="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Enfoque Epistemológico Activo:</span>
                          <p class="text-xs text-[var(--text-secondary)] mt-0.5">Define las unidades fundamentales de estudio según el paradigma científico.</p>
                        </div>
                        <div class="flex items-center gap-1.5">
                          <button 
                            type="button" 
                            @click="formData.methodology.approach = 'cuantitativo'" 
                            class="px-3 py-1.5 rounded text-xs font-semibold transition-all cursor-pointer"
                            :class="formData.methodology.approach === 'cuantitativo' ? 'bg-blue-600 text-white shadow-sm' : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)]'"
                          >
                            📊 Cuantitativo
                          </button>
                          <button 
                            type="button" 
                            @click="formData.methodology.approach = 'cualitativo'" 
                            class="px-3 py-1.5 rounded text-xs font-semibold transition-all cursor-pointer"
                            :class="formData.methodology.approach === 'cualitativo' ? 'bg-emerald-600 text-white shadow-sm' : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)]'"
                          >
                            🌱 Cualitativo
                          </button>
                          <button 
                            type="button" 
                            @click="formData.methodology.approach = 'mixto'" 
                            class="px-3 py-1.5 rounded text-xs font-semibold transition-all cursor-pointer"
                            :class="formData.methodology.approach === 'mixto' ? 'bg-purple-600 text-white shadow-sm' : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)]'"
                          >
                            🔄 Mixto
                          </button>
                        </div>
                      </div>

                      <!-- 6A. Cuantitativo Branch: Hipótesis de Investigación & Variables -->
                      <div x-show="formData.methodology.approach === 'cuantitativo' || formData.methodology.approach === 'mixto'" class="space-y-5">
                        
                        <div class="p-3 bg-blue-50/60 dark:bg-blue-950/30 rounded border border-blue-200 dark:border-blue-900 text-xs text-blue-900 dark:text-blue-300">
                          <strong>Enfoque Cuantitativo (Hipotético-Deductivo):</strong> El concepto central es la <em>Hipótesis</em> (proposición conjetural contrastable) y la unidad fundamental de estudio es la <em>Variable</em> (propiedad cuantitativa medible).
                        </div>

                        <div>
                          <label for="adv-hypo-quant" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Hipótesis Central de Investigación (H₁)</label>
                          <textarea id="adv-hypo-quant" x-model="formData.hypothesis" rows="3" class="w-full text-sm" placeholder="Existe una relación estadísticamente significativa entre [Variable Independiente] y [Variable Dependiente] en la muestra evaluada..."></textarea>
                        </div>

                        <!-- Variables Dynamic List -->
                        <div class="space-y-3">
                          <div class="flex items-center justify-between">
                            <span class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Variables de Estudio (Independientes / Dependientes / Control)</span>
                            <button type="button" class="btn btn-secondary btn-sm" @click="addVariable()">+ Variable</button>
                          </div>
                          
                          <div class="space-y-2">
                            <template x-for="(v, idx) in formData.variables" :key="idx">
                              <div class="flex items-center gap-2">
                                <span class="text-xs font-mono font-semibold text-blue-600 dark:text-blue-400 w-7 shrink-0" x-text="'V' + (idx + 1) + ':'"></span>
                                <input type="text" x-model="formData.variables[idx]" :aria-label="'Variable de estudio ' + (idx + 1)" class="flex-1 text-sm" placeholder="Nombre de la variable (ej. Arquitectura RAG, Tasa de Alucinaciones)...">
                                <button type="button" class="btn btn-ghost btn-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-950/40" @click="removeVariable(idx)" :aria-label="'Eliminar variable ' + (idx + 1)" x-show="formData.variables.length > 1">
                                  <svg class="w-4 h-4" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                                </button>
                              </div>
                            </template>
                          </div>
                        </div>

                        <!-- Operacionalización de Variables Mini Table -->
                        <div class="pt-2 space-y-3">
                          <div class="flex items-center justify-between">
                            <div>
                              <span class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Matriz de Operacionalización de Variables</span>
                              <span class="text-[11px] text-[var(--text-muted)]">Desglosa variables en dimensiones, indicadores y escalas de medición</span>
                            </div>
                            <button type="button" class="btn btn-secondary btn-sm" @click="addOperationalizedVariable()">+ Fila a Matriz</button>
                          </div>

                          <div class="space-y-3" x-show="formData.operationalized_variables.length > 0">
                            <template x-for="(op, oIdx) in formData.operationalized_variables" :key="oIdx">
                              <div class="p-3.5 rounded-md bg-[var(--bg-subtle)] border border-[var(--border-subtle)] space-y-3 text-xs">
                                <div class="flex items-center justify-between">
                                  <span class="font-bold text-blue-600 dark:text-blue-400" x-text="'Variable Operacionalizada #' + (oIdx + 1)"></span>
                                  <button type="button" class="text-red-500 hover:underline" @click="removeOperationalizedVariable(oIdx)">Eliminar</button>
                                </div>
                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                  <div>
                                    <label class="block font-medium mb-1">Nombre de Variable *</label>
                                    <input type="text" x-model="op.name" class="w-full text-xs" placeholder="Ej. Rendimiento Académico">
                                  </div>
                                  <div>
                                    <label class="block font-medium mb-1">Tipo de Variable</label>
                                    <select x-model="op.variable_type" class="w-full text-xs">
                                      <option value="independiente">Independiente (Causa / Predictora)</option>
                                      <option value="dependiente">Dependiente (Efecto / Resultado)</option>
                                      <option value="control">Control</option>
                                      <option value="moderadora">Moderadora</option>
                                      <option value="interviniente">Interviniente</option>
                                    </select>
                                  </div>
                                </div>
                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                  <div>
                                    <label class="block font-medium mb-1">Definición Conceptual</label>
                                    <input type="text" x-model="op.conceptual_definition" class="w-full text-xs" placeholder="Definición teórica según autor/literatura">
                                  </div>
                                  <div>
                                    <label class="block font-medium mb-1">Definición Operacional</label>
                                    <input type="text" x-model="op.operational_definition" class="w-full text-xs" placeholder="Mecanismo o criterio empírico de medición">
                                  </div>
                                </div>
                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                  <div>
                                    <label class="block font-medium mb-1">Escala de Medición</label>
                                    <select x-model="op.measurement_scale" class="w-full text-xs">
                                      <option value="nominal">Nominal (Categorías sin orden)</option>
                                      <option value="ordinal">Ordinal (Jerarquía / Escala Likert)</option>
                                      <option value="intervalo">Intervalo (Cero arbitrario / Celsius)</option>
                                      <option value="razon">Razón (Cero absoluto / Tiempo, Conteo)</option>
                                    </select>
                                  </div>
                                  <div>
                                    <label class="block font-medium mb-1">Instrumento Asignado</label>
                                    <input type="text" x-model="op.instrument_name" class="w-full text-xs" placeholder="Ej. Cuestionario Likert de 15 ítems">
                                  </div>
                                </div>
                              </div>
                            </template>
                          </div>
                        </div>

                      </div>

                      <!-- 6B. Cualitativo Branch: Supuestos Epistemológicos & Categorías de Análisis -->
                      <div x-show="formData.methodology.approach === 'cualitativo' || formData.methodology.approach === 'mixto'" class="space-y-5">
                        
                        <div class="p-3 bg-emerald-50/60 dark:bg-emerald-950/30 rounded border border-emerald-200 dark:border-emerald-900 text-xs text-emerald-900 dark:text-emerald-300">
                          <strong>Enfoque Cualitativo (Inductivo-Interpretativo):</strong> En lugar de hipótesis cuantitativas se establecen <em>Supuestos de Partida / Premisas Epistemológicas</em>. En lugar de variables se trabaja con <em>Categorías de Análisis</em> y subcategorías emergentes.
                        </div>

                        <div>
                          <label for="adv-hypo-qual" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Supuestos Epistemológicos y Premisas de Partida</label>
                          <textarea id="adv-hypo-qual" x-model="formData.hypothesis" rows="3" class="w-full text-sm" placeholder="Se asume que los sujetos construyen sus significados a partir de su interacción con el fenómeno, reflejando tensiones entre la adopción y la resistencia cultural..."></textarea>
                          <p class="text-xs text-[var(--text-muted)] mt-1">Conjetura orientadora no probabilística que guía el trabajo de campo inductivo.</p>
                        </div>

                        <!-- Qualitative Categories Dynamic List -->
                        <div class="space-y-3">
                          <div class="flex items-center justify-between">
                            <div>
                              <span class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Categorías y Subcategorías de Análisis</span>
                              <span class="text-[11px] text-[var(--text-muted)]">Ejes temáticos y unidades de significado a codificar</span>
                            </div>
                            <button type="button" class="btn btn-secondary btn-sm" @click="addQualitativeCategory()">+ Categoría de Análisis</button>
                          </div>

                          <div class="space-y-3" x-show="formData.qualitative_categories.length > 0">
                            <template x-for="(cat, cIdx) in formData.qualitative_categories" :key="cIdx">
                              <div class="p-3.5 rounded-md bg-[var(--bg-subtle)] border border-[var(--border-subtle)] space-y-3 text-xs">
                                <div class="flex items-center justify-between">
                                  <span class="font-bold text-emerald-600 dark:text-emerald-400" x-text="'Categoría #' + (cIdx + 1)"></span>
                                  <button type="button" class="text-red-500 hover:underline" @click="removeQualitativeCategory(cIdx)">Eliminar</button>
                                </div>
                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                  <div>
                                    <label class="block font-medium mb-1">Nombre de la Categoría *</label>
                                    <input type="text" x-model="cat.name" class="w-full text-xs" placeholder="Ej. Percepción de Autoeficacia en Redacción">
                                  </div>
                                  <div>
                                    <label class="block font-medium mb-1">Tipo de Categoría</label>
                                    <select x-model="cat.category_type" class="w-full text-xs">
                                      <option value="central">Central / Eje Temático Principal</option>
                                      <option value="emergente">Emergente (Derivada del campo)</option>
                                      <option value="axial">Axial (Relacional)</option>
                                    </select>
                                  </div>
                                </div>
                                <div>
                                  <label class="block font-medium mb-1">Definición Conceptual / Criterio de Codificación</label>
                                  <input type="text" x-model="cat.definition" class="w-full text-xs" placeholder="Significado que orientará la identificación de fragmentos en el discurso">
                                </div>
                              </div>
                            </template>
                          </div>
                        </div>

                      </div>

                    </div>
                  ` : ''}

                  <!-- Step 7: Methodology Design, Techniques & Instruments -->
                  ${this.currentStep === 'methodology_design' ? `
                    <div class="space-y-6">
                      
                      <!-- Section A: Enfoque, Paradigma y Diseño -->
                      <div class="space-y-4">
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                          <div>
                            <label for="adv-approach" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Enfoque Metodológico *</label>
                            <select id="adv-approach" x-model="formData.methodology.approach" class="w-full">
                              <option value="cuantitativo">Cuantitativo (Hipotético-Deductivo)</option>
                              <option value="cualitativo">Cualitativo (Inductivo-Fenomenológico)</option>
                              <option value="mixto">Mixto (Integrado Triangulado)</option>
                            </select>
                          </div>
                          <div>
                            <label for="adv-paradigm" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Paradigma Epistemológico *</label>
                            <select id="adv-paradigm" x-model="formData.methodology.paradigm" class="w-full">
                              <option value="positivista">Positivista (Empírico-Analítico)</option>
                              <option value="postpositivista">Postpositivista (Crítico-Realista)</option>
                              <option value="interpretativo">Interpretativo / Hermenéutico</option>
                              <option value="sociocritico">Sociocrítico / Dialéctico</option>
                              <option value="pragmatico">Pragmático (Métodos Mixtos)</option>
                            </select>
                          </div>
                          <div>
                            <label for="adv-design" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Diseño de Investigación</label>
                            <input id="adv-design" type="text" x-model="formData.methodology.design" class="w-full" placeholder="Ej. Cuasiexperimental con pre y postest / Fenomenológico">
                          </div>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                          <div>
                            <label for="adv-population" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Población Objetivo</label>
                            <input id="adv-population" type="text" x-model="formData.methodology.population" class="w-full" placeholder="Ej. 120 estudiantes de posgrado">
                          </div>
                          <div>
                            <label for="adv-sample" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Muestra y Tamaño (n)</label>
                            <input id="adv-sample" type="text" x-model="formData.methodology.sample" class="w-full" placeholder="Ej. n=64 participantes">
                          </div>
                          <div>
                            <label for="adv-sampling" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Técnica de Muestreo</label>
                            <select id="adv-sampling" x-model="formData.methodology.sampling_technique" class="w-full text-xs">
                              <option value="probabilistico_aleatorio">Probabilístico Aleatorio Simple</option>
                              <option value="probabilistico_estratificado">Probabilístico Estratificado</option>
                              <option value="probabilistico_conglomerados">Probabilístico por Conglomerados</option>
                              <option value="no_probabilistico_intencional">No Probabilístico Intencional / Por Criterios</option>
                              <option value="no_probabilistico_bola_nieve">No Probabilístico Bola de Nieve</option>
                              <option value="no_probabilistico_por_cuotas">No Probabilístico por Cuotas</option>
                              <option value="censo_completo">Censo Completo (Poblacional)</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      <!-- Section B: Técnicas e Instrumentos de Recolección (Dynamic List item-by-item) -->
                      <div class="pt-2 space-y-3">
                        <div class="flex items-center justify-between">
                          <div>
                            <span class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">Técnicas e Instrumentos de Recolección de Datos *</span>
                            <span class="text-[11px] text-[var(--text-muted)]">Agrega una a una las técnicas con su respectivo instrumento y objetivo asociado</span>
                          </div>
                          <button type="button" class="btn btn-secondary btn-sm" @click="addTechniqueInstrumentPair()">+ Agregar Técnica e Instrumento</button>
                        </div>

                        <div class="space-y-3">
                          <template x-for="(pair, pIdx) in formData.methodology.technique_instrument_pairs" :key="pIdx">
                            <div class="p-3.5 rounded-md bg-[var(--bg-subtle)] border border-[var(--border-subtle)] space-y-3 text-xs">
                              <div class="flex items-center justify-between">
                                <span class="font-bold text-blue-600 dark:text-blue-400" x-text="'Técnica & Instrumento #' + (pIdx + 1)"></span>
                                <button type="button" class="text-red-500 hover:underline" @click="removeTechniqueInstrumentPair(pIdx)" x-show="formData.methodology.technique_instrument_pairs.length > 1">Eliminar</button>
                              </div>
                              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div>
                                  <label class="block font-medium mb-1">Técnica de Recolección *</label>
                                  <input type="text" x-model="pair.technique" class="w-full text-xs" placeholder="Ej. Encuesta, Entrevista a profundidad, Grupo focal, Observación">
                                </div>
                                <div>
                                  <label class="block font-medium mb-1">Instrumento de Medición / Registro *</label>
                                  <input type="text" x-model="pair.instrument" class="w-full text-xs" placeholder="Ej. Cuestionario estructurado escala Likert de 25 ítems, Guía semiestructurada">
                                </div>
                              </div>
                              <div>
                                <label class="block font-medium mb-1">Objetivo Específico o Variable / Categoría Vinculada</label>
                                <input type="text" x-model="pair.target_objective" class="w-full text-xs" placeholder="Ej. Vinculado al Objetivo Específico 1 y Variable Independiente">
                              </div>
                            </div>
                          </template>
                        </div>
                      </div>

                      <!-- Section C: Análisis de Datos & Procedimiento -->
                      <div class="space-y-4 pt-2">
                        <div>
                          <label for="adv-analysis" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Técnicas de Procesamiento y Análisis de la Información</label>
                          <input id="adv-analysis" type="text" x-model="formData.methodology.analysis_technique" class="w-full text-sm" placeholder="Ej. Prueba t de Student para muestras emparejadas, ANOVA / Análisis temático de Braun y Clarke">
                        </div>
                        <div>
                          <label for="adv-procedure" class="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Procedimiento de Recolección y Consideraciones Éticas</label>
                          <textarea id="adv-procedure" x-model="formData.methodology.data_collection_procedure" rows="3" class="w-full text-sm" placeholder="Fases de recolección en campo, consentimiento informado, confidencialidad y resguardo de datos..."></textarea>
                        </div>
                      </div>

                    </div>
                  ` : ''}

                  <!-- Step 8: Consistency Audit -->
                  ${this.currentStep === 'consistency_audit' ? `
                    <div class="space-y-4">
                      <div class="p-4 rounded-md bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-xs text-[var(--text-secondary)] space-y-2">
                        <p class="font-semibold text-blue-900 dark:text-blue-300">Auditoría Algorítmica de Congruencia Metodológica (6 Pilares):</p>
                        <p>El motor valida que el objetivo general responda a la pregunta rectoral, que los objetivos específicos guíen las fases empíricas, que las hipótesis se alineen a las variables declaradas y que los instrumentos correspondan a la escala y enfoque seleccionado.</p>
                      </div>

                      <div class="space-y-2 text-xs">
                        <div class="flex items-center justify-between p-3 rounded bg-[var(--bg-subtle)] border border-[var(--border-subtle)]">
                          <span>1. Pregunta Rectoral vs. Objetivo General</span>
                          <span class="badge badge-success">Alineado Bloom</span>
                        </div>
                        <div class="flex items-center justify-between p-3 rounded bg-[var(--bg-subtle)] border border-[var(--border-subtle)]">
                          <span>2. Enfoque Metodológico vs. Paradigma Epistemológico</span>
                          <span class="badge badge-success">Congruente</span>
                        </div>
                        <div class="flex items-center justify-between p-3 rounded bg-[var(--bg-subtle)] border border-[var(--border-subtle)]">
                          <span>3. Hipótesis / Supuestos vs. Variables / Categorías</span>
                          <span class="badge badge-note">Contrastable</span>
                        </div>
                        <div class="flex items-center justify-between p-3 rounded bg-[var(--bg-subtle)] border border-[var(--border-subtle)]">
                          <span>4. Técnicas e Instrumentos vs. Objetivos Específicos</span>
                          <span class="badge badge-success">Verificable</span>
                        </div>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Step 9: Approved State -->
                  ${this.currentStep === 'approved' ? `
                    <div class="p-8 text-center space-y-5">
                      <div class="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto shadow-sm">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                      </div>
                      <div>
                        <h4 class="font-bold text-lg text-[var(--text-primary)]">Ficha Metodológica Aprobada con Distinción</h4>
                        <p class="text-xs text-[var(--text-secondary)] max-w-md mx-auto mt-1">Tu proyecto cuenta con una base metodológica y epistemológica rigurosa, congruente y lista para la búsqueda de literatura y redacción capitular.</p>
                      </div>
                      <button class="btn btn-primary btn-lg" @click="approveMethodology()" :disabled="isApproving">
                        <span x-show="!isApproving">Aprobar y Pasar a Fase 2: Literatura & RAG</span>
                        <span x-show="isApproving">Aprobando Ficha...</span>
                      </button>
                    </div>
                  ` : ''}

                </div>

                <!-- Footer Actions -->
                ${this.currentStep !== 'approved' ? `
                  <div class="card-footer flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                    <div class="flex-1 mr-0 sm:mr-3">
                      <input 
                        type="text" 
                        x-model="userInput" 
                        placeholder="Instrucción adicional o pregunta para el Asesor IA (opcional)..." 
                        class="w-full text-xs"
                      >
                    </div>
                    <div class="flex items-center gap-2 justify-end">
                      <button 
                        class="btn btn-primary btn-sm" 
                        @click="processCurrentStep()" 
                        :disabled="isProcessingStep"
                      >
                        <span x-show="!isProcessingStep">Guardar y Validar Paso</span>
                        <span x-show="isProcessingStep">Validando...</span>
                      </button>
                    </div>
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
                    <h4 class="font-bold text-sm text-[var(--text-primary)]">Orientación Metodológica</h4>
                    <span class="text-[10px] text-[var(--text-muted)] font-mono">Tutor Socrático</span>
                  </div>
                </div>

                <div class="text-xs text-[var(--text-secondary)] space-y-3 leading-relaxed">
                  <div x-show="isProcessingStep" class="flex items-center gap-2 text-blue-600 py-4">
                    <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    <span>Analizando coherencia del paso...</span>
                  </div>

                  <div x-show="!isProcessingStep && advisorResponse" class="p-3.5 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-xs">
                    <p class="font-semibold text-blue-600 dark:text-blue-400 mb-1">Dictamen del Asesor:</p>
                    <p x-text="advisorResponse" class="whitespace-pre-line"></p>
                  </div>

                  <div x-show="!isProcessingStep && !advisorResponse">
                    <p>Completa los campos del formulario correspondientes al paso actual y haz clic en <strong>Guardar y Validar Paso</strong>.</p>
                    <p class="mt-2">Puedes navegar libremente entre cualquiera de los pasos haciendo clic en los botones numerados superiores.</p>
                  </div>
                </div>
              </div>

              <!-- Quick Summary Card -->
              <div class="card p-4 space-y-2 text-xs">
                <div class="font-semibold text-[var(--text-primary)]">Resumen de la Ficha</div>
                <div class="text-[11px] text-[var(--text-secondary)] space-y-1">
                  <div><strong>Nivel:</strong> <span class="capitalize" x-text="formData.academic_level"></span></div>
                  <div><strong>Enfoque:</strong> <span class="capitalize" x-text="formData.methodology.approach"></span></div>
                  <div><strong>Problema:</strong> <span class="truncate block text-[var(--text-muted)]" x-text="formData.research_problem ? formData.research_problem.substring(0, 60) + '...' : 'Pendiente'"></span></div>
                  <div><strong>Objetivo General:</strong> <span class="truncate block text-[var(--text-muted)]" x-text="formData.general_objective ? formData.general_objective.substring(0, 60) + '...' : 'Pendiente'"></span></div>
                </div>
              </div>

            </div>

          </div>

        </div>
      `;
    }
  };
}
