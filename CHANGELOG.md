# Changelog

Todas las modificaciones notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

### Planned
- Generador modular de capítulos con memoria jerárquica contextual (Sprint 3).
- Compilador de documentos Word (`.docx`) formateados estrictamente según APA 7ª edición.
- Sanitización de tablas exportadas contra inyección de fórmulas (CSV/Excel/Word).
- Streaming de tokens en tiempo real vía WebSockets para redacción asistida.

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
  - Reintentos dinámicos basados en `tenacity.AsyncRetrying` con retroceso exponencial.
  - Soporte para respuestas estructuradas en formato JSON y streaming de tokens.
  - Plantillas de prompts versionadas para asesoría científica y matrices de consistencia.
- **Asesor Metodológico:**
  - Máquina de estados `AdvisorStateMachine` para control lineal de pasos de entrevista.
  - Validador metodológico `MethodologyValidator` con verificación de taxonomía de Bloom, partículas interrogativas formales y consistencia de hipótesis.
  - Servicio `AdvisorService` para orquestar la entrevista y la transición hacia la fase de contextualización.
- **API REST & Middleware:**
  - Endpoints de FastAPI para gestión de proyectos (`/api/projects`) y asesor metodológico (`/api/advisor`).
  - Middleware de cabeceras de seguridad HTTP (CSP, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`).
  - Suite completa de 63 pruebas unitarias, de integración y basadas en propiedades con `Hypothesis` y `pytest-cov` (85.63% de cobertura).
