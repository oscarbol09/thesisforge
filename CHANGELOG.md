# Changelog

Todas las modificaciones notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

### Planned
- Motor de auditoría y defensa de tesis en simulación de jurado evaluador (Sprint 4).
- Interfaz gráfica web interactiva para visualización en tiempo real y edición sincronizada.

---

## [0.3.0] - 2026-09-21

### Added
- **Redacción Modular por Capítulos y Memoria Jerárquica Contextual:**
  - Plantillas canónicas de tesis en 5 capítulos estructurados (`src/thesisforge/drafting/templates.py`), con esquemas diferenciados para metodologías cuantitativas, cualitativas y mixtas abarcando 19 secciones temáticas.
  - Administrador de memoria en 4 capas (`HierarchicalMemoryManager` en `src/thesisforge/drafting/memory.py`):
    - *Capa 0 (Núcleo Metodológico)*: Problema de investigación, pregunta general, hipótesis, variables y objetivos.
    - *Capa 1 (Memoria Capitular Previa)*: Resúmenes sintetizados de secciones y capítulos aprobados para garantizar coherencia sintáctica e ilación lógica sin saturar la ventana de contexto del LLM.
    - *Capa 2 (Evidencia RAG Indexada)*: Fragmentos bibliográficos recuperados de la literatura científica indexada.
    - *Capa 3 (Directrices de Sección)*: Descripción, criterios de calidad y orientaciones específicas del tesista.
  - Servicio de redacción `DraftService` (`src/thesisforge/drafting/service.py`) con soporte completo para inicialización capitular, generación asistida, streaming en tiempo real, revisión iterativa y aprobación con síntesis automática.
  - Prompts de redacción científica anti-AI (`src/thesisforge/llm/prompts.py`) que imponen registro académico riguroso, especificidad empírica, voz activa y eliminación total de muletillas generadas por IA.
- **Compilador DOCX APA 7ª Edición y Servicio de Exportación:**
  - Compilador de documentos Word `APA7DocxCompiler` (`src/thesisforge/export/docx_compiler.py`) que implementa la totalidad de directrices editoriales APA 7:
    - Márgenes estándar de 2.54 cm (1.0 pulgada) en los 4 bordes.
    - Tipografía configurable (Times New Roman 12 pt, Calibri 11 pt) e interlineado doble (2.0) sin espaciado extra.
    - Portada para estudiante y profesional con metadatos institucionales y de asesor.
    - 5 niveles oficiales de encabezados APA (Centrado/Negrita, Alineado a la izquierda/Negrita, Cursiva, Sangrado).
    - Renderizado de tablas APA 7 con bordes horizontales limpios y sin líneas verticales.
    - Sección de Referencias con sangría francesa (1.27 cm) y ordenación alfabética automática.
    - Numeración de página en el encabezado superior derecho mediante campo XML de Word.
  - Servicio de exportación `ExportService` (`src/thesisforge/export/service.py`) para compilación asíncrona a memoria y archivo en disco.
- **Seguridad Defensiva en Documentos (AppSec & CWE-1236):**
  - Sanitizador `sanitize_cell_value` (`src/thesisforge/drafting/sanitizer.py`) que neutraliza caracteres peligrosos (`=`, `+`, `-`, `@`, `\t`, `\r`) en tablas de Word/Excel para prevenir ataques de Formula Injection (CWE-1236), preservando literales numéricos válidos.
  - Filtro `clean_draft_markup` para depurar delimitadores de markdown y bloques espurios antes del guardado.
- **Endpoints REST, WebSockets y Subcomandos CLI:**
  - Endpoints REST en `/api/drafting` para inicializar esquemas, listar secciones, generar borradores, editar contenido, refinar texto y aprobar capítulos.
  - Endpoint WebSocket `/api/drafting/ws/{project_id}/{section_id}` para streaming interactivo bidireccional con eventos `start`, `token` y `complete`.
  - Endpoint REST `POST /api/export/projects/{project_id}/docx` con retorno de adjuntos Word `.docx`.
  - Subcomandos de consola: `thesisforge draft-init`, `thesisforge draft-list` y `thesisforge export-docx`.
- **Documentación Oficial y Suite de Pruebas:**
  - Manual de Usuario Oficial en español (`docs/user-guide/MANUAL_DE_USUARIO.md`) que cubre el flujo integral de las tres fases.
  - 124 pruebas unitarias, de integración y basadas en propiedades (Hypothesis) ejecutadas con 100% de aprobación.

---

## [0.2.0] - 2026-09-19

### Added
- **Clientes Académicos Asíncronos:**
  - `SemanticScholarClient` para búsqueda en el catálogo de Semantic Scholar Graph API v1 con filtrado temporal, recuperación de resúmenes y enlaces a PDFs Open Access.
  - `ArxivClient` para búsqueda de preprints en ArXiv API con parseo seguro de feeds Atom mediante `defusedxml.ElementTree`.
  - `CrossRefClient` para resolución canónica de metadatos bibliográficos y verificación de DOIs oficiales.
  - `AcademicSearchAggregator` para orquestar búsquedas concurrentes multi-fuente con desduplicación inteligente por DOI normalizado y firma autor-título-año.
  - Capa de caché persistente `LiteratureCache` respaldada en SQLite con TTL configurable (48 horas por defecto) y purga periódica para prevenir rate limits.
- **Indexación y Recuperación Vectorial (RAG):**
  - Extractor y segmentador `PDFDocumentParser` basado en PyMuPDF (`fitz`) con chunking contextual estructurado por oraciones completas (1500 caracteres, 200 de solapamiento).
  - Sanitización estricta contra Prompt Injection en texto extraído delimitado en prompts con etiquetas semánticas de aislamiento.
  - Motor vectorial local `ChromaVectorStore` sobre ChromaDB con soporte para colecciones por proyecto y embeddings ligeros deterministas (`FastLocalEmbeddingFunction`).
- **Formateo APA 7ª Edición y Compuerta de Citación:**
  - Formateador estricto `APA7Formatter` que genera citaciones parentéticas, narrativas y entradas de lista de referencias bajo normas APA 7 (manejo exhaustivo de 1, 2, 3-20 y 21+ autores).
  - Validador `CitationGuard` que asegura que los DOIs existan y verifica que los fragmentos recuperados realmente respalden las afirmaciones científicas (*claim-evidence grounding*) mediante análisis léxico y verificación asistida por LLM con umbrales configurables.
- **Endpoints REST y Herramientas CLI:**
  - Rutas FastAPI bajo `/api/literature`: `/search`, `/verify-doi`, `/projects/{id}/documents` y `/projects/{id}/context`.
  - Comando CLI `thesisforge search-papers` con renderizado en tabla formateada y citas APA 7 automáticas.
- **Suite de Pruebas y Aseguramiento de Calidad:**
  - 93 pruebas unitarias, de integración y basadas en propiedades (`Hypothesis`, `respx`) con 83.32% de cobertura de código.

---

## [0.1.0] - 2026-09-18

### Added
- **Core de Seguridad:**
  - Guardia de seguridad contra SSRF (`assert_safe_academic_url`) que resuelve nombres de host y bloquea rangos de IP privadas RFC 1918, bucles locales (loopback) y metadatos de nube.
  - Bóveda simétrica local `LocalKeyVault` basada en Fernet (AES-128-CBC + HMAC-SHA256) para cifrar claves de API BYOK en reposo.
  - Logger estructurado JSON con prevención de Log Injection (CWE-117) y enmascaramiento automático de secretos y tokens.
  - Utilidades estrictas de tiempo UTC (`utc_now()`, `format_iso_utc()`, `parse_iso_utc()`).
- **Modelos de Dominio:**
  - Esquemas Pydantic v2 inmutables y validados: `ProjectStateDTO`, `CitationDTO`, `MethodologyDTO`, `SectionDraftDTO`, `ProjectSummaryDTO`.
  - Enums tipados: `AcademicLevel`, `ResearchApproach`, `ProjectPhase`, `SectionStatus`.
  - Jerarquía de excepciones de dominio (`ThesisForgeError`, `SecurityError`, `SSRFBlockedError`, `KeyVaultError`, `ProjectNotFoundError`, `InvalidPhaseTransitionError`, `MethodologyValidationError`, `LLMProviderError`).
- **Persistencia Asíncrona:**
  - Gestor de base de datos `DatabaseManager` con soporte para SQLite asíncrono vía `aiosqlite`, modo WAL y base de datos compartida en memoria para pruebas.
  - Repositorio de proyectos `ProjectRepository` con operaciones CRUD completas y consultas ordenadas por fecha de actualización.
  - Repositorio seguro de claves `SecureKeyStoreRepository` para gestión de credenciales BYOK por proveedor.
- **Router LLM BYOK:**
  - Módulo `LLMRouter` con soporte para OpenRouter, Google Gemini, Groq, Ollama, OpenAI, Anthropic y NVIDIA NIM.
