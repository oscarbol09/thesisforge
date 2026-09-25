# RAG y Búsqueda de Literatura Real

Una de las principales debilidades de los modelos de lenguaje comercial (ChatGPT, Claude) es la invención de citas bibliográficas, autores y DOIs falsos (*alucinaciones*).

ThesisForge implementa un motor RAG (**Retrieval-Augmented Generation**) diseñado específicamente para literatura científica, con conectores asíncronos a repositorios abiertos y validación rigurosa de fuentes.

---

## 1. Fuentes Indexadas en Tiempo Real

ThesisForge se conecta de manera asíncrona a las siguientes bases de datos científicas abiertas:

1. **Semantic Scholar Academic Graph API (`SemanticScholarClient`):** Acceso a más de 200 millones de papers, resúmenes, métricas de citación, años de publicación y enlaces a PDFs en Open Access.
2. **ArXiv API (`ArxivClient`):** Búsqueda de preprints en ciencias de la computación, física, matemáticas, biología cuantitativa y estadística con parseo seguro XML (`defusedxml`).
3. **CrossRef API (`CrossRefClient`):** Validación cruzada de metadatos de publicación y resolución canónica de DOIs oficiales.
4. **Agregador Federado (`AcademicSearchAggregator`):** Búsqueda concurrente multi-fuente con desduplicación inteligente por DOI normalizado y firma autor-título-año, respaldado por una capa de caché SQLite con TTL configurable (48 horas).

---

## 2. Búsqueda Vectorial Local (Tus Propios PDFs)

Puedes subir tus propios archivos PDF (artículos, libros, tesis previas) para que el asistente redacte utilizando tus documentos como contexto:

- **Extracción de Texto con PyMuPDF (`PDFDocumentParser`):** Extracción rápida de texto con detección temprana de archivos protegidos o cifrados (`doc.is_encrypted`).
- **Aislamiento contra Prompt Injection:** El texto extraído de documentos de terceros se encapsula dentro de etiquetas semánticas de aislamiento para evitar ataques indirectos de inyección de instrucciones.
- **Chunking Contextual:** División en fragmentos de 1500 caracteres con solapamiento de 200 caracteres para preservar la semántica del párrafo.
- **Indexación Vectorial Local (`ChromaVectorStore`):** Almacenamiento local mediante ChromaDB con colecciones aisladas por proyecto, saneamiento alfanumérico estricto de nombres (longitud máxima de 63 caracteres) y embeddings deterministas (`FastLocalEmbeddingFunction`).

---

## 3. Flujo de Revisión Sistemática PRISMA 2020

ThesisForge implementa el protocolo **PRISMA 2020** (Page et al., 2021) para producir flujos de búsqueda bibliográfica auditables y reproducibles, especialmente útil en revisiones sistemáticas de literatura y metaanálisis.

### Fases del Protocolo PRISMA 2020

```text
┌─────────────────────────┐
│  FASE 1: IDENTIFICACIÓN   │  Registros por fuente (Semantic Scholar, ArXiv, CrossRef)
│  Duplicados eliminados   │  + registros inelegibles por automatización
└─────────────────────────┘
          │
┌─────────────────────────┐
│  FASE 2: CRIBADO         │  Cribado título/resumen + causas de exclusión
└─────────────────────────┘
          │
┌─────────────────────────┐
│  FASE 3: ELEGIBILIDAD    │  Texto completo evaluado + excluidos con causa
└─────────────────────────┘
          │
┌─────────────────────────┐
│  FASE 4: INCLUSIÓN       │  Estudios incluidos en la síntesis final
└─────────────────────────┘
```

### Generar el flujo PRISMA de un proyecto

```bash
# Via API REST
POST /api/literature/prisma-flow/{project_id}?query=machine+learning+healthcare&excluded_screening=15
```

La respuesta incluye el reporte completo en JSON. Para obtener el diagrama de flujo en texto estructurado listo para copiar en un capítulo, llama a `.to_markdown_flowchart()` sobre el objeto `PRISMAFlowReport` desde el código Python:

```python
from thesisforge.rag.prisma import PRISMAFlowReport

report = PRISMAFlowReport(project_id="proj-123", query_string="metodología cuantitativa")
report.record_database_search("Semantic Scholar", 120)
report.record_database_search("ArXiv", 45)
report.record_deduplication(18)
report.record_screening(screened=147, excluded=89, reasons={"Fuera de alcance temático": 52, "Idioma no incluido": 37})
report.record_eligibility(sought=58, not_retrieved=4, assessed=54, excluded=22,
                          reasons={"Sin acceso a texto completo": 14, "Diseño no elegible": 8})

print(report.to_markdown_flowchart())
```

### Campos del reporte (`PRISMAFlowReport`)

| Campo | Descripción |
| :--- | :--- |
| `identification.database_counts` | Registros por fuente (p. ej. `{"semantic_scholar": 120}`) |
| `identification.duplicate_records_removed` | Duplicados eliminados antes del cribado |
| `screening.records_excluded` | Excluidos por título/resumen con causas |
| `eligibility.reports_assessed_for_eligibility` | Evaluados a texto completo |
| `included.new_studies_included` | Estudios finales incluídos en la síntesis |
| `included.included_citation_ids` | IDs de las citas registradas en el proyecto |

---

## 4. Filtro Anti-Alucinaciones y Claim Grounding

Antes de redactar cualquier sección bibliográfica:

1. **Identificadores Verificados:** Toda cita debe tener un identificador verificado (DOI oficial, ArXiv ID o identificador de documento local cargado).
2. **Comprobación de Respaldo (*Claim-Evidence Grounding* con `CitationGuard`):** El sistema analiza la correspondencia léxica y semántica entre la afirmación del borrador y el contenido de los fragmentos recuperados. Si una afirmación carece de evidencia fáctica en la literatura, el evaluador emite una observación tipada `UNSUPPORTED_CLAIM`.
3. **Formateo APA 7 Automático:** Las citas se formatean en el cuerpo del texto según la normativa APA 7ª edición (`(Apellido, Año)` o `Apellido (Año)`), manejando exhaustivamente 1, 2, 3-20 y 21+ autores.
