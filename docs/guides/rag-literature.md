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

## 3. Filtro Anti-Alucinaciones y Claim Grounding

Antes de redactar cualquier sección bibliográfica:

1. **Identificadores Verificados:** Toda cita debe tener un identificador verificado (DOI oficial, ArXiv ID o identificador de documento local cargado).
2. **Comprobación de Respaldo (*Claim-Evidence Grounding* con `CitationGuard`):** El sistema analiza la correspondencia léxica y semántica entre la afirmación del borrador y el contenido de los fragmentos recuperados. Si una afirmación carece de evidencia fáctica en la literatura, el evaluador emite una observación tipada `UNSUPPORTED_CLAIM`.
3. **Formateo APA 7 Automático:** Las citas se formatean en el cuerpo del texto según la normativa APA 7ª edición (`(Apellido, Año)` o `Apellido (Año)`), manejando exhaustivamente 1, 2, 3-20 y 21+ autores.
