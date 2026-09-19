# Changelog

Todas las modificaciones notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

### Planned
- Motor RAG con clientes asíncronos para Semantic Scholar, ArXiv y CrossRef (Sprint 2).
- Indexación de documentos locales con ChromaDB y chunking léxico de 1500 caracteres con 200 de solapamiento.
- Generador modular de capítulos con memoria jerárquica contextual (Sprint 3).

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
