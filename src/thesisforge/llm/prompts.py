"""Versioned prompt templates for methodological advisory and academic validation."""

ADVISOR_SYSTEM_PROMPT = """Eres el Asesor Metodológico Principal de ThesisForge.
Tu función es guiar al estudiante de manera rigurosa, científica y socrática en la delimitación y formalización de su proyecto de investigación ({academic_level}).

Directrices inquebrantables:
1. Rigor Metodológico: Aplica taxonomía científica formal (verbos en infinitivo de taxonomía de Bloom/investigación: Determinar, Analizar, Evaluar, Diseñar, etc.).
2. Coherencia Epistemológica:
   - Cuantitativo: Requiere variables delimitadas, hipótesis contrastable (si es correlacional o explicativo) e instrumentos estandarizados.
   - Cualitativo: Categorías de análisis, supuestos ontológicos, técnicas fenomenológicas/etnográficas/teoría fundamentada.
   - Mixto: Triangulación concurrente o secuencial.
3. Prohibido Alucinar: Nunca inventes citas o datos empíricos.
4. Idioma: Español académico formal, claro, empático pero exigente.
5. Formato de Respuesta: Debes entregar análisis estructurado y sugerencias accionables.
"""

PROBLEM_FORMULATION_PROMPT = """Analiza la siguiente propuesta de problema de investigación:

Área de estudio: {area_of_study}
Tema propuesto: {topic}
Descripción del estudiante:
\"\"\"
{user_input}
\"\"\"

Nivel Académico: {academic_level}

Genera una respuesta con el siguiente formato JSON estricto:
{{
  "critique": "Evaluación crítica del planteamiento (claridad, viabilidad, delimitación espacio-temporal)",
  "refined_problem": "Planteamiento formal del problema refinado académicamente",
  "suggested_questions": [
    "Pregunta de investigación principal formal",
    "Pregunta secundaria 1",
    "Pregunta secundaria 2"
  ],
  "is_viable": true
}}
"""

OBJECTIVES_PROMPT = """Con base en el problema y la pregunta de investigación:
Problema: {research_problem}
Pregunta Principal: {research_question}
Enfoque: {approach}
Nivel: {academic_level}

Aporte del estudiante para objetivos:
\"\"\"
{user_input}
\"\"\"

Genera una formulación coherente en formato JSON estricto:
{{
  "general_objective": "Objetivo general (iniciar con verbo en infinitivo de nivel taxonómico adecuado)",
  "specific_objectives": [
    "Objetivo específico 1 (Diagnóstico/Fundamentación)",
    "Objetivo específico 2 (Diseño/Desarrollo/Intervención)",
    "Objetivo específico 3 (Evaluación/Validación/Impacto)"
  ],
  "variables_or_categories": ["Variable/Categoría 1", "Variable/Categoría 2"],
  "evaluation": "Justificación metodológica de la coherencia entre objetivos y pregunta"
}}
"""

METHODOLOGY_DESIGN_PROMPT = """Evalúa y estructura el marco metodológico:
Nivel: {academic_level}
Pregunta: {research_question}
Objetivo General: {general_objective}
Propuesta del estudiante:
\"\"\"
{user_input}
\"\"\"

Genera la ficha metodológica estructurada en formato JSON estricto:
{{
  "approach": "{approach}",
  "design": "Diseño específico (ej: No experimental transversal correlacional-causal)",
  "population": "Definición de la población o universo de estudio",
  "sample": "Tipo de muestreo y tamaño muestral estimado",
  "instruments": ["Instrumento 1", "Instrumento 2"],
  "analysis_technique": "Técnica estadística o de análisis cualitativo sugerida",
  "recommendations": "Observaciones para garantizar la validez interna y externa"
}}
"""

CONSISTENCY_AUDIT_PROMPT = """Realiza una auditoría completa de coherencia metodológica (Matriz de Consistencia) sobre los siguientes elementos:

- Nivel: {academic_level}
- Título: {title}
- Problema: {research_problem}
- Pregunta: {research_question}
- Hipótesis: {hypothesis}
- Objetivo General: {general_objective}
- Objetivos Específicos: {specific_objectives}
- Enfoque: {approach}
- Diseño: {design}

Evalúa:
1. Correspondencia directa entre Pregunta Principal, Objetivo General e Hipótesis.
2. Suficiencia de los Objetivos Específicos para alcanzar el Objetivo General.
3. Compatibilidad entre el Enfoque/Diseño y los datos requeridos.

Responde en formato JSON estricto:
{{
  "score": 95,
  "status": "APPROVED",
  "strengths": ["Fortaleza 1", "Fortaleza 2"],
  "flaws": ["Observación 1"],
  "actionable_fixes": ["Corrección sugerida 1"],
  "verdict": "Dictamen metodológico detallado"
}}
"""
