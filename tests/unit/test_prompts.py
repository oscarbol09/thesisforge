"""Unit tests for all prompt templates and variable placeholder rendering."""

from thesisforge.llm import prompts


def test_advisor_system_prompt_rendering():
    """Verify ADVISOR_SYSTEM_PROMPT formats cleanly."""
    formatted = prompts.ADVISOR_SYSTEM_PROMPT.format(academic_level="pregrado")
    assert "pregrado" in formatted
    assert "Asesor Metodológico" in formatted


def test_problem_formulation_prompt_rendering():
    """Verify PROBLEM_FORMULATION_PROMPT formats cleanly."""
    formatted = prompts.PROBLEM_FORMULATION_PROMPT.format(
        area_of_study="Ingeniería de Software",
        topic="Microservicios y Caching",
        user_input="Queremos evaluar el impacto de Redis en latencia.",
        academic_level="pregrado",
    )
    assert "pregrado" in formatted
    assert "Microservicios y Caching" in formatted
    assert "Redis" in formatted


def test_objectives_prompt_rendering():
    """Verify OBJECTIVES_PROMPT formats cleanly."""
    formatted = prompts.OBJECTIVES_PROMPT.format(
        research_problem="Falta de rendimiento en transacciones distribuidas.",
        research_question="¿Cómo optimizar el throughput mediante saga pattern?",
        approach="cuantitativo",
        academic_level="maestria",
        user_input="Diseñar un framework de eventos.",
    )
    assert "maestria" in formatted
    assert "saga pattern" in formatted
    assert "cuantitativo" in formatted


def test_methodology_design_prompt_rendering():
    """Verify METHODOLOGY_DESIGN_PROMPT formats cleanly."""
    formatted = prompts.METHODOLOGY_DESIGN_PROMPT.format(
        academic_level="doctorado",
        research_question="¿Cuál es la convergencia del algoritmo?",
        general_objective="Demostrar la convergencia matemática del modelo.",
        approach="cuantitativo",
        user_input="Experimento controlado con 1000 iteraciones.",
    )
    assert "doctorado" in formatted
    assert "cuantitativo" in formatted


def test_consistency_audit_prompt_rendering():
    """Verify CONSISTENCY_AUDIT_PROMPT formats cleanly."""
    formatted = prompts.CONSISTENCY_AUDIT_PROMPT.format(
        academic_level="pregrado",
        title="Impacto de RAG en la Redacción Académica",
        research_problem="Alto índice de citas alucinadas en LLMs.",
        research_question="¿Cómo mitigar alucinaciones mediante RAG indexado?",
        hypothesis="El uso de RAG indexado reduce significativamente los errores de citación.",
        general_objective="Evaluar la precisión de citas usando RAG indexado.",
        specific_objectives=["Diagnosticar citas previas", "Implementar RAG", "Medir precisión"],
        approach="cuantitativo",
        design="Experimental puro",
    )
    assert "Experimental puro" in formatted
    assert "Impacto de RAG" in formatted


def test_evidence_verification_prompt_rendering():
    """Verify EVIDENCE_VERIFICATION_PROMPT formats cleanly."""
    formatted = prompts.EVIDENCE_VERIFICATION_PROMPT.format(
        claim="La arquitectura de transformadores fue introducida por Vaswani en 2017.",
        evidence_passages="Vaswani et al. (2017) Attention Is All You Need.",
    )
    assert "Vaswani" in formatted
    assert "La arquitectura de transformadores" in formatted


def test_literature_synthesis_prompt_rendering():
    """Verify LITERATURE_SYNTHESIS_PROMPT formats cleanly."""
    formatted = prompts.LITERATURE_SYNTHESIS_PROMPT.format(
        research_problem="Deficiencias en diagnóstico temprano.",
        research_question="¿Cuál es la precisión de modelos CNN?",
        general_objective="Evaluar la precisión de modelos CNN.",
        section_topic="2.1 Antecedentes Internacionales",
        retrieved_passages="Zhang (2023) reportó 94% de exactitud.",
    )
    assert "Zhang (2023)" in formatted
    assert "Antecedentes Internacionales" in formatted


def test_chapter_drafting_prompt_rendering():
    """Verify CHAPTER_DRAFTING_PROMPT formats cleanly."""
    formatted = prompts.CHAPTER_DRAFTING_PROMPT.format(
        layer_0_methodology="Problema: Citas alucinadas.",
        layer_1_memory="Capítulo 1 aprobado.",
        layer_2_literature="Smith (2023) encontró mejoras del 40%.",
        target_section_info="Capítulo 2: Marco Teórico - 2.1 Antecedentes",
    )
    assert "Marco Teórico" in formatted
    assert "Smith (2023)" in formatted


def test_section_refine_prompt_rendering():
    """Verify SECTION_REFINE_PROMPT formats cleanly."""
    formatted = prompts.SECTION_REFINE_PROMPT.format(
        layer_0_methodology="Enfoque cuantitativo.",
        layer_1_memory="Contexto inicial.",
        current_draft="Texto borrador inicial.",
        user_feedback="Añadir datos estadísticos de la OMS.",
    )
    assert "OMS" in formatted
    assert "Texto borrador inicial" in formatted


def test_section_summary_prompt_rendering():
    """Verify SECTION_SUMMARY_PROMPT formats cleanly and contains Spanish directive."""
    formatted = prompts.SECTION_SUMMARY_PROMPT.format(
        section_title="3.2 Diseño Muestral",
        content="Se seleccionó una muestra probabilística estratificada de n=384 unidades.",
    )
    assert "Diseño Muestral" in formatted
    assert "estratificada" in formatted
    assert "español" in prompts.SECTION_SUMMARY_PROMPT.lower()


def test_jury_panel_audit_prompt_rendering():
    """Verify JURY_PANEL_AUDIT_PROMPT formats cleanly."""
    formatted = prompts.JURY_PANEL_AUDIT_PROMPT.format(
        academic_level="doctorado",
        title="Modelado Causal en Sistemas Distribuidos",
        area_of_study="Ciencias de la Computación",
        research_problem="Ambigüedad causal en microservicios.",
        research_question="¿Cómo inferir grafos DAG de dependencias?",
        general_objective="Construir un algoritmo de inferencia causal en logs distribuidos.",
        specific_objectives=["Recolectar trazas OpenTelemetry", "Inferir DAG", "Evaluar recall"],
        hypothesis="El algoritmo DAG mejora el recall en un 25%.",
        approach="cuantitativo",
        design="Explicativo cuasi-experimental",
        population="Trazas de microservicios en producción",
        sample="50,000 trazas distribuidas",
        instruments=["OpenTelemetry Collector", "Benchmark causal"],
        analysis_technique="Pruebas de independencia condicional",
        drafted_sections_summary="Capítulo 1 y 2 aprobados",
        citation_count=12,
        citations_summary="Pearl (2009), Spirtes (2000)",
    )
    assert "Dr. Arístides Valenzuela" in formatted
    assert "OpenTelemetry" in formatted
    assert "doctorado" in formatted


def test_defense_questions_generation_prompt_rendering():
    """Verify DEFENSE_QUESTIONS_GENERATION_PROMPT formats cleanly."""
    formatted = prompts.DEFENSE_QUESTIONS_GENERATION_PROMPT.format(
        academic_level="maestria",
        title="Tesis de Maestría en Ciberseguridad",
        research_question="¿Cómo evaluar la encriptación homomórfica?",
        general_objective="Evaluar la seguridad de encriptación homomórfica.",
        hypothesis="La encriptación homomórfica reduce fugas de datos sin degradar el throughput.",
        approach="cuantitativo",
        design="Experimental",
        population="Transacciones financieras cifradas",
        sample="100,000 operaciones",
        instruments=["Benchmark AES vs CKKS"],
        analysis_technique="ANOVA y pruebas t de Student",
        sections_summary="5 capítulos completos",
        known_flaws="Falta justificar el sobrecosto computacional.",
    )
    assert "Dr. Camilo Restrepo" in formatted
    assert "sobrecosto computacional" in formatted


def test_defense_reply_evaluation_prompt_rendering():
    """Verify DEFENSE_REPLY_EVALUATION_PROMPT formats cleanly."""
    formatted = prompts.DEFENSE_REPLY_EVALUATION_PROMPT.format(
        juror_name="Dr. Demetrio Sotomayor",
        juror_role="abogado_del_diablo",
        question="¿Por qué no consideró bases de datos columnares como Cassandra?",
        focus_area="Supuestos y Explicaciones Alternativas",
        academic_level="pregrado",
        student_answer="Se descartó Cassandra debido a que la carga de trabajo es 90% lecturas atómicas clave-valor.",
    )
    assert "Cassandra" in formatted
    assert "Dr. Demetrio Sotomayor" in formatted


def test_bias_and_contradiction_detection_prompt_rendering():
    """Verify BIAS_AND_CONTRADICTION_DETECTION_PROMPT formats cleanly."""
    formatted = prompts.BIAS_AND_CONTRADICTION_DETECTION_PROMPT.format(
        academic_level="maestria",
        title="Estudio de Robustez en Sistemas Autónomos",
        approach="cuantitativo",
        design="Experimental",
        research_question="¿Cuál es la tasa de fallas bajo ruido estocástico?",
        general_objective="Determinar la tasa de fallas.",
        specific_objectives=["Inyectar ruido", "Medir degradación"],
        hypothesis="El controlador adaptativo reduce fallas en un 30%.",
        variables=["Nivel de ruido", "Tasa de error"],
        population="100 simulaciones de vuelo",
        sample="30 trayectorias críticas",
        instruments=["Simulador Gazebo"],
        analysis_technique="Regresión logística",
        sections_full_text="Capítulo 3: Metodología detallada...",
    )
    assert "Gazebo" in formatted
    assert "Sistemas Autónomos" in formatted
