"""Canonical academic thesis outline and section templates for Latin American and international universities."""

from dataclasses import dataclass
from typing import Literal

from thesisforge.models import AcademicLevel, ResearchApproach, SectionDraftDTO, SectionStatus


@dataclass(frozen=True)
class SectionTemplate:
    """Canonical blueprint for a thesis section or chapter subsection."""

    section_id: str
    chapter_number: int
    order_index: int
    title: str
    description: str
    guidance: str
    applicable_approaches: tuple[ResearchApproach, ...] = (
        ResearchApproach.CUANTITATIVO,
        ResearchApproach.CUALITATIVO,
        ResearchApproach.MIXTO,
    )
    applicable_levels: tuple[AcademicLevel, ...] = (
        AcademicLevel.PREGRADO,
        AcademicLevel.MAESTRIA,
        AcademicLevel.DOCTORADO,
    )
    requires_rag: bool = False
    section_type: Literal["introduction", "theory", "methods", "results", "conclusions"] = (
        "introduction"
    )


CANONICAL_THESIS_OUTLINE: list[SectionTemplate] = [
    # --- CAPÍTULO 1: EL PROBLEMA DE INVESTIGACIÓN ---
    SectionTemplate(
        section_id="sec_1_1",
        chapter_number=1,
        order_index=1,
        title="1.1 Planteamiento y Descripción del Problema",
        description="Diagnóstico riguroso estructurado en los 8 Movimientos del Problema: Macro -> Micro -> Evidencia Empírica -> Magnitud -> Consecuencias (3 niveles) -> Vacío de Conocimiento -> Estado del Arte -> Síntesis.",
        guidance="Desarrolla los 8 movimientos secuenciales con datos empíricos locales y citación APA 7, evitando el síndrome del marco teórico disfrazado.",
        section_type="introduction",
    ),
    SectionTemplate(
        section_id="sec_1_2",
        chapter_number=1,
        order_index=2,
        title="1.2 Formulación de Preguntas de Investigación",
        description="Pregunta principal formal conteniendo los 5 componentes anatómicos (Unidad de análisis, Foco, Contexto, Temporalidad, Tipo de relación/proceso) y subpreguntas derivadas.",
        guidance="Formula interrogantes con partículas no dicotómicas (¿En qué medida...?, ¿De qué manera...?, ¿Cómo se relaciona...?) sin verbos vacuos.",
        section_type="introduction",
    ),
    SectionTemplate(
        section_id="sec_1_3",
        chapter_number=1,
        order_index=3,
        title="1.3 Objetivos de la Investigación",
        description="Objetivo general isomorfo a la pregunta principal (Regla de Oro: OG = PG en infinitivo) y 3 a 5 objetivos específicos ordenados por fases (Diagnóstica, Diseño/Intervención, Evaluación).",
        guidance="Inicia con verbos de nivel taxonómico coherente con el diseño (no usar tareas como 'revisar literatura' o 'aplicar encuestas').",
        section_type="introduction",
    ),
    SectionTemplate(
        section_id="sec_1_4",
        chapter_number=1,
        order_index=4,
        title="1.4 Justificación e Importancia del Estudio",
        description="Fundamentación en 4 dimensiones obligatorias (Teórica, Práctica/Social, Metodológica, Educativa/Institucional) culminando en la Formulación Negativa.",
        guidance="Desglosa las 4 dimensiones y cierra obligatoriamente con el párrafo de Formulación Negativa: qué consecuencias adversas o vacíos persistirán si no se investiga.",
        section_type="introduction",
    ),
    SectionTemplate(
        section_id="sec_1_5",
        chapter_number=1,
        order_index=5,
        title="1.5 Delimitación y Limitaciones de la Investigación",
        description="Diferenciación estricta entre Delimitaciones (fronteras elegidas: espacial, temporal, conceptual, poblacional) y Limitaciones (restricciones reales redactadas con la fórmula de 4 componentes).",
        guidance="Redacta cada limitación con: 1. Declaración de la restricción -> 2. Efecto potencial -> 3. Mitigación metodológica -> 4. Afirmación que no se hará.",
        section_type="introduction",
    ),
    # --- CAPÍTULO 2: MARCO TEÓRICO Y CONCEPTUAL ---
    SectionTemplate(
        section_id="sec_2_1",
        chapter_number=2,
        order_index=6,
        title="2.1 Antecedentes de la Investigación",
        description="Síntesis crítica de estudios previos internacionales y nacionales de los últimos 5 años.",
        guidance="Estructura cada antecedente con autor, año, objetivo, metodología y aporte relevante.",
        requires_rag=True,
        section_type="theory",
    ),
    SectionTemplate(
        section_id="sec_2_2",
        chapter_number=2,
        order_index=7,
        title="2.2 Bases Teóricas y Fundamentación Científica",
        description="Desarrollo conceptual de las teorías y modelos que sustentan las variables de estudio.",
        guidance="Confronta posturas de autores clave y fundamenta el modelo conceptual adoptado.",
        requires_rag=True,
        section_type="theory",
    ),
    SectionTemplate(
        section_id="sec_2_3",
        chapter_number=2,
        order_index=8,
        title="2.3 Definición de Términos Básicos",
        description="Glosario conceptual y operativo de términos técnicos empleados en la tesis.",
        guidance="Define con precisión técnica y respaldo bibliográfico los términos indispensables.",
        requires_rag=True,
        section_type="theory",
    ),
    SectionTemplate(
        section_id="sec_2_4",
        chapter_number=2,
        order_index=9,
        title="2.4 Hipótesis y Operacionalización de Variables",
        description="Hipótesis general y específicas con matriz de variables o categorías de análisis.",
        guidance="Define variables independientes, dependientes e intervinientes con sus indicadores.",
        applicable_approaches=(ResearchApproach.CUANTITATIVO, ResearchApproach.MIXTO),
        section_type="theory",
    ),
    # --- CAPÍTULO 3: MARCO METODOLÓGICO ---
    SectionTemplate(
        section_id="sec_3_1",
        chapter_number=3,
        order_index=10,
        title="3.1 Enfoque, Tipo y Nivel de Investigación",
        description="Justificación del paradigma epistemológico, alcance (descriptivo, correlacional, explicativo) y diseño.",
        guidance="Articula el método con la naturaleza de la pregunta de investigación.",
        section_type="methods",
    ),
    SectionTemplate(
        section_id="sec_3_2",
        chapter_number=3,
        order_index=11,
        title="3.2 Población, Muestra y Unidad de Análisis",
        description="Caracterización del universo poblacional, cálculo muestral y criterios de inclusión/exclusión.",
        guidance="Detalla si el muestreo es probabilístico o no probabilístico y la representatividad.",
        section_type="methods",
    ),
    SectionTemplate(
        section_id="sec_3_3",
        chapter_number=3,
        order_index=12,
        title="3.3 Técnicas e Instrumentos de Recolección de Datos",
        description="Descripción de cuestionarios, entrevistas, fichas de observación y pruebas de validez/confiabilidad.",
        guidance="Presenta el coeficiente Alfa de Cronbach / juicio de expertos o rigor cualitativo.",
        section_type="methods",
    ),
    SectionTemplate(
        section_id="sec_3_4",
        chapter_number=3,
        order_index=13,
        title="3.4 Técnicas de Procesamiento y Análisis de Datos",
        description="Software estadístico o cualitativo utilizado y pruebas estadísticas aplicadas.",
        guidance="Describe pruebas de normalidad, contraste de hipótesis o análisis temático reflexivo.",
        section_type="methods",
    ),
    SectionTemplate(
        section_id="sec_3_5",
        chapter_number=3,
        order_index=14,
        title="3.5 Consideraciones Éticas y Rigor Científico",
        description="Consentimiento informado, confidencialidad, no maleficencia y trazabilidad.",
        guidance="Garantiza el cumplimiento de comités de ética institucionales.",
        section_type="methods",
    ),
    # --- CAPÍTULO 4: RESULTADOS Y DISCUSIÓN ---
    SectionTemplate(
        section_id="sec_4_1",
        chapter_number=4,
        order_index=15,
        title="4.1 Presentación y Análisis de Resultados",
        description="Secuencia en 3 niveles: Depuración y verificación de supuestos -> Nivel 1 Descriptivos (M, DT, asimetría, frecuencias) -> Nivel 2 Inferenciales por objetivo específico (o análisis cualitativo en 4 movimientos por categorías).",
        guidance="Regla operativa: ninguna tabla o cita va sola (cada dato se presenta y analiza en el mismo movimiento). Reporte APA 7 completo con estadístico, gl, p, tamaño del efecto e IC 95%.",
        section_type="results",
    ),
    SectionTemplate(
        section_id="sec_4_2",
        chapter_number=4,
        order_index=16,
        title="4.2 Contrastación de Hipótesis / Triangulación de Datos",
        description="Contraste formal del sistema de hipótesis (H0, H1, decisión sobre H0 e interpretación sustantiva) o Triangulación cualitativa en 3 movimientos (Convergencias, Divergencias, Síntesis) / Joint Display mixto con metainferencias.",
        guidance="Cero HARKing o p-hacking. Reporte íntegro de resultados negativos o nulos. En cualitativo, incluir activamente casos negativos y discrepantes.",
        section_type="results",
    ),
    SectionTemplate(
        section_id="sec_4_3",
        chapter_number=4,
        order_index=17,
        title="4.3 Discusión de Resultados",
        description="Estructura en 4 Movimientos: Síntesis de hallazgos -> Confrontación con la literatura (Convergencia, Divergencia y Extensión) -> Implicaciones (Teóricas, Prácticas, Metodológicas) -> Limitaciones y Líneas Futuras.",
        guidance="Responde a las 5 preguntas de la discusión. Confronta divergencias con antecedentes y declara explícitamente el aporte original ('esta tesis demostró que...').",
        requires_rag=True,
        section_type="results",
    ),
    # --- CAPÍTULO 5: CONCLUSIONES Y RECOMENDACIONES ---
    SectionTemplate(
        section_id="sec_5_1",
        chapter_number=5,
        order_index=18,
        title="5.1 Conclusiones",
        description="Inferencias y síntesis de significado organizadas por correspondencia isomórfica con los objetivos específicos (N objetivos = N conclusiones) más Conclusión General en 3 movimientos.",
        guidance="Cadena descendente: Resultado -> Conclusión. Eleva la abstracción sin repetir números ni estadísticos del Cap. IV. Clasifica por certeza epistémica (confirmatoria, tentativa, de proceso). Cero citas nuevas.",
        section_type="conclusions",
    ),
    SectionTemplate(
        section_id="sec_5_2",
        chapter_number=5,
        order_index=19,
        title="5.2 Recomendaciones",
        description="Acciones operacionales y viables organizadas por destinatario explícito (Docentes/Aula, Instituciones, Políticas/Ministerios, Formación docente, Comunidad investigadora).",
        guidance="Estructura cada recomendación en 4 componentes: 1. Destinatario y acción en infinitivo -> 2. Hallazgo/conclusión de derivación -> 3. Condiciones de viabilidad -> 4. Mecanismo o indicador de seguimiento.",
        section_type="conclusions",
    ),
    SectionTemplate(
        section_id="sec_5_3",
        chapter_number=5,
        order_index=20,
        title="5.3 Aportes a la Comunidad Científica y Transferencia Social",
        description="Declaración de contribución al conocimiento en 4 dimensiones (Teórica, Práctica, Metodológica, Social/Transferencia) y declaración de originalidad disciplinar.",
        guidance="Explicita qué sabe el campo que no sabía antes (novedad de objeto, contexto, teoría, método o aplicación), mecanismos de transferencia y devolución de resultados a participantes.",
        section_type="conclusions",
    ),
]


def get_default_thesis_sections(
    approach: ResearchApproach = ResearchApproach.CUANTITATIVO,
    academic_level: AcademicLevel = AcademicLevel.PREGRADO,
) -> list[SectionDraftDTO]:
    """Derive standard SectionDraftDTO list tailored to project approach and level."""
    sections: list[SectionDraftDTO] = []
    for template in CANONICAL_THESIS_OUTLINE:
        if approach not in template.applicable_approaches:
            continue
        if academic_level not in template.applicable_levels:
            continue

        draft = SectionDraftDTO(
            section_id=template.section_id,
            title=template.title,
            chapter_number=template.chapter_number,
            order_index=template.order_index,
            content="",
            summary="",
            status=SectionStatus.PENDING,
            word_count=0,
            citations_used=[],
            version=1,
        )
        sections.append(draft)

    return sections
