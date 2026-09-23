# Changelog

Todas las modificaciones notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

### Planned
- Empaquetado ejecutable autónomo standalone (.exe, .dmg, AppImage) y distribución en PyPI (Sprint 6 / v1.0.0).

---

## [0.5.1] - 2026-09-23

### Security & Hardening
- **Límite de Tamaño en Subida de PDFs (`src/thesisforge/api/routes_literature.py`):**
  - Establecimiento de un umbral máximo de 50 MB (`MAX_PDF_UPLOAD_BYTES`) en `POST /api/literature/index-pdf` para mitigar ataques de denegación de servicio (DoS) por agotamiento de memoria.
- **Defensa contra DNS Rebinding (TOCTOU) en SSRFGuard:**
  - Implementación de `CustomAsyncHTTPTransport` que enlaza el socket directamente a la IP validada pre-resuelta, eliminando la ventana de vulnerabilidad entre validación DNS y petición HTTP.
- **Bóveda de Claves con Derivación de Sal Criptográfica Única:**
  - Robustecimiento de `LocalKeyVault` para generar y persistir sales PBKDF2 únicas por secreto almacenado.

### Fixed & Improved
- **Manejo Resiliente de WebSockets (`src/thesisforge/api/routes_defense.py`):**
  - Captura defensiva de tipos en `turn_index` ante payloads malformados, retornando un frame de error JSON estructurado sin cerrar la conexión de sustentación oral.
- **Compatibilidad y Migración de Esquemas (`src/thesisforge/models.py`):**
  - Configuración de `extra="ignore"` en todos los DTOs de persistencia central (`ProjectStateDTO`, `CitationDTO`, etc.) para asegurar tolerancia ante migraciones de esquema futuras.
- **Filtro Selectivo de Reintentos en LLMRouter (`src/thesisforge/llm/router.py`):**
  - Introducción del predicado `_is_retryable_llm_error` para omitir reintentos inútiles ante errores 4xx del cliente (400, 401, 403, 404, 422).
- **Higiene de Dependencias y Ciclo de Vida (`src/thesisforge/api/app.py`, `src/thesisforge/rag/clients/base.py`):**
  - Purga automática de registros expirados en `LiteratureCache.prune_expired()` durante el inicio del `lifespan` de FastAPI.
  - Generación dinámica del encabezado `User-Agent` utilizando `__version__` del paquete.
  - Eliminación de chequeos redundantes de proyecto no encontrado en `routes_drafting.py`.
- **Directiva de Idioma en Prompts (`src/thesisforge/llm/prompts.py`):**
  - Prescripción explícita de idioma español en `SECTION_SUMMARY_PROMPT` para preservar la coherencia de la memoria jerárquica.
- **Infraestructura Docker (`Dockerfile`, `docker-compose.yml`):**
  - Empaquetado de la interfaz SPA `gui/` en la etapa de ejecución y gestión desacoplada de variables de entorno con `env_file: .env`.
- **Compilador DOCX APA 7 (`src/thesisforge/export/docx_compiler.py`):**
  - Inserción de campo dinámico Word XML `TOC \o "1-3" \h \z \u` con instrucción explícita de actualización F9/Cmd+A.
  - Desduplicación estricta de referencias bibliográficas combinando normalización de DOIs y tuplas (primer autor, año, título).
  - Jerarquía de 5 niveles de encabezados según estándar APA 7.
- **Evaluador de Jurados Multi-Agente (`src/thesisforge/jury/evaluator.py`):**
  - Normalización robusta de roles contra diacríticos y variantes ortográficas.
  - Ponderaciones calibradas: Metodólogo 35%, Temático 25%, Estadístico 25%, Abogado del Diablo 15%.
  - Regla de veto y umbrales de dictamen alineados ($\ge 95, \ge 80, \ge 70, \ge 50, < 50$).
- **Suite de Pruebas Automatizadas:**
  - 201 pruebas unitarias, de integración, seguridad y de propiedades 100% aprobadas, incluyendo suite completa de renderizado de plantillas de prompts (`test_prompts.py`).

---

## [0.5.0] - 2026-09-23

### Added
- **Interfaz de Usuario Web SPA (`gui/`):**
  - Shell HTML5 monomando estructurado con Alpine.js y Tailwind CSS sin necesidad de build steps ni Node.js.
  - Sistema de tokens semánticos (`gui/css/tokens.css`, `gui/css/components.css`) basado en la regla 60-30-10 (60% neutro Zinc/Stone, 30% superficies, 10% acento Cobalt `#2563eb`).
  - Módulos interactivos completos para las 6 fases de la investigación:
    - **Portafolio / Dashboard (`gui/js/dashboard.js`):** Tarjetas de proyecto con telemetría en vivo, filtros de nivel y búsqueda por texto, esqueletos de carga anti-CLS y eliminación controlada.
    - **Asesor Metodológico (`gui/js/advisor.js`):** Stepper visual de 9 pasos guiado por la máquina de estados determinista, formularios dinámicos para objetivos y variables, y panel de orientación socrática en vivo.
    - **Literatura & RAG (`gui/js/literature.js`):** Búsqueda académica federada (Semantic Scholar, ArXiv, CrossRef), subida e indexación directa de PDFs en ChromaDB con PyMuPDF, biblioteca de citas APA 7 y verificador anti-alucinaciones de afirmaciones (*claim grounding*).
    - **Redacción Capitular (`gui/js/drafting.js`):** Esquema canónico de 5 capítulos (19 secciones), streaming de tokens en tiempo real mediante WebSocket bidireccional (`/api/drafting/ws/...`), edición manual y aprobación de secciones con síntesis automática en memoria jerárquica.
    - **Compilador Word APA 7 (`gui/js/export.js`):** Formulario de configuración de metadatos institucionales y directrices tipográficas con descarga de binario `.docx`.
    - **Tribunal de Jurados (`gui/js/jury.js`):** Visualización de dictámenes doctorales, rúbrica dimensional 0-100 por jurado y tabla de defectos detectados con recomendaciones.
    - **Defensa Oral Socrática (`gui/js/defense.js`):** Simulador de sustentación interactiva por turnos con evaluación de réplicas y cálculo de veredicto final.
    - **Gestión BYOK (`gui/js/settings.js`):** Modal de configuración de proveedores LLM (OpenRouter, Gemini, OpenAI, Groq, NVIDIA NIM, Ollama) y almacenamiento local cifrado.
- **Lanzador de Escritorio Nativo PyWebView (`src/thesisforge/desktop/`):**
  - Módulo `src/thesisforge/desktop/launcher.py` que descubre puertos TCP libres dinámicamente, inicia Uvicorn en un hilo daemon, realiza sondeo de salud contra `/health` y embebe la SPA en una ventana nativa de escritorio con soporte de DevTools.
  - Subcomando CLI `thesisforge gui [--port N] [--debug]` para iniciar la aplicación con un solo comando.
  - Dependencia `pywebview>=5.0.0` incorporada en `pyproject.toml`.
- **Integración de Archivos Estáticos en FastAPI (`src/thesisforge/api/app.py`, `src/thesisforge/config.py`):**
  - Montaje de `gui/` como `StaticFiles(directory="gui", html=True)` sin colisionar con rutas REST ni WebSockets.
  - Configuración dinámica de orígenes permitidos `cors_origins` en `AppSettings` (resolviendo Issue #12).
  - Cabecera `Content-Security-Policy` ajustada para admitir CDNs seguras y WebSockets.
- **Suite de Pruebas Automatizadas:**
  - 9 nuevas pruebas de integración y unitarias para la entrega de archivos estáticos y el orquestador PyWebView, alcanzando un total de **177 pruebas automatizadas 100% aprobadas**.

---

## [0.4.0] - 2026-09-22

### Added
- **Tribunal Académico Multi-Agente & Motor de Auditoría Científica (`src/thesisforge/jury/`):**
  - Panel evaluador multi-perspectiva compuesto por 4 roles doctorales independientes (`MultiAgentJuryEngine` en `src/thesisforge/jury/evaluator.py`):
    - *Dr. Arístides Valenzuela (Metodólogo y Epistemólogo)*: Audita consistencia interna, delimitación espacio-temporal, congruencia de objetivos e hipótesis y validez metodológica.
    - *Dra. Beatriz Salamanca (Especialista Temática)*: Evalúa suficiencia del estado del arte, pertinencia de literatura indexada y profundidad teórica.
    - *Dr. Camilo Restrepo (Auditor Estadístico y Cuantitativo)*: Evalúa representatividad muestral, idoneidad de instrumentos de medición y supuestos de pruebas estadísticas.
    - *Dr. Demetrio Sotomayor (Evaluador Crítico / Abogado del Diablo)*: Cuestiona supuestos no declarados, sesgos de confirmación y explicaciones causales alternativas.
  - Motor híbrido de auditoría científica que combina reglas deterministas (falta de hipótesis en diseños experimentales, cero citas RAG, capítulos sin aprobar) con análisis semántico profundo asistido por LLM.
  - Sistema de calificación multidimensional ponderado (0.0 a 100.0) y cálculo de dictámenes oficiales académicos: *Aprobado con Distinción ($\ge 95$)*, *Aprobado ($\ge 80$)*, *Modificaciones Menores ($\ge 70$)*, *Modificaciones Mayores ($\ge 50$)* y *No Aprobado ($< 50$)*.
- **Simulador Interactivo de Sustentación Oral Socrática (`src/thesisforge/jury/defense.py`):**
  - Motor de defensa por turnos `ThesisDefenseSimulator` que genera 4 preguntas desafiantes contextualizadas al nivel académico del estudiante (Pregrado, Maestría, Doctorado) y a las debilidades del proyecto.
  - Evaluación analítica de réplicas orales considerando solidez argumentativa, respaldo empírico, terminología disciplinar y reconocimiento honesto de limitaciones.
  - Transición automática del estado del proyecto a `COMPLETED` cuando la sustentación resulta aprobada con éxito.
- **Persistencia Transaccional de Dictámenes y Sesiones (`src/thesisforge/repository/jury_repository.py`):**
  - Repositorio asíncrono SQLite `JuryRepository` para almacenamiento estructurado de informes de jurado (`jury_evaluations`) y sesiones de defensa oral (`defense_sessions`).
  - Índices optimizados sobre `project_id`, `created_at` y `status`.
- **Modelos de Dominio y Excepciones Tipadas (`src/thesisforge/models.py`, `src/thesisforge/exceptions.py`):**
  - Enums: `JurorRole`, `AuditSeverity`, `AuditIssueType`, `JuryVerdict`, `DefenseStatus`.
  - DTOs Pydantic v2: `AuditIssueDTO`, `JurorDimensionScoreDTO`, `JuryEvaluationReportDTO`, `DefenseTurnDTO`, `DefenseSessionDTO`.
  - Excepciones de dominio: `JuryEvaluationError`, `DefenseSessionError`, `DefenseTurnNotFoundError`.
- **Endpoints REST, WebSockets y Comandos CLI:**
  - Rutas REST `/api/jury`: `POST /projects/{id}/audit`, `GET /projects/{id}/evaluations/latest`, `GET /projects/{id}/evaluations`, `GET /evaluations/{id}`.
  - Rutas REST `/api/defense`: `POST /projects/{id}/start`, `POST /sessions/{id}/reply`, `GET /sessions/{id}`, `GET /projects/{id}/sessions`.
  - Endpoint WebSocket `/api/defense/ws/{session_id}` para sustentación interactiva bidireccional en tiempo real con eventos `session_state`, `reply`, `turn_evaluated` y `defense_completed`.
  - Subcomandos de consola CLI: `thesisforge jury-audit --project-id <id>` y `thesisforge defense-start --project-id <id>`.
- **Suite de Pruebas Automatizadas y Aseguramiento de Calidad:**
  - 24 nuevas pruebas unitarias, de integración y basadas en propiedades (`Hypothesis`), alcanzando un total de 148 pruebas automatizadas ejecutadas con 100% de aprobación.
  - Tipado estricto `mypy --strict` validado en 56 archivos sin excepciones.

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
