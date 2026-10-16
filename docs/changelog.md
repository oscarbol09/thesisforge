# Registro de Cambios (Changelog)

Todas las modificaciones notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

### Added
- **Control Universal de Concurrencia Optimista (`src/thesisforge/models.py`, `src/thesisforge/repository/project_repository.py`, `TF-REPO-001`):**
  - Inclusión de `version: int = Field(default=1, ge=1)` en `ProjectStateDTO` unificado con la migración `v3_optimistic_concurrency`.
  - Modificación de `update_project` para requerir y verificar atómicamente la versión (`expected_version=project.version`), lanzando `ProjectVersionConflictError` ante escrituras concurrentes obsoletas en todos los servicios de dominio.
- **Precedencia Formal de Configuración Twelve-Factor (`src/thesisforge/config.py`, `TF-CONFIG-001-R1`):**
  - Implementación de `AppSettings.settings_customise_sources` estableciendo la jerarquía canónica: `defaults < config.yaml < environment variables`.
  - Pydantic Settings garantiza que las variables de entorno (`THESISFORGE_*`) tengan prioridad sobre overrides de `config.yaml`, y estos sobre los valores predeterminados del modelo.
- **Validación Estructural de Integridad y Autenticidad HMAC en Bundles (`src/thesisforge/export/bundle.py`, `tests/unit/test_project_bundle.py`, `TF-EXPORT-001-R1`, `TF-EXPORT-001-R2`):**
  - Soporte de firma digital criptográfica HMAC-SHA256 (`signature_hmac_sha256`) en el manifiesto con verificación estricta en tiempo constante (`hmac.compare_digest`), distinguiendo formalmente integridad (SHA-256) de autenticidad.
  - Verificación de compatibilidad con versiones mayores (`format_version` compatible `1.x`).
  - Validación cruzada estricta de correspondencia entre `manifest.json` y `project.json` para `title`, `academic_level` y `phase`.
  - Verificación de consistencia del contenido de los archivos Markdown derivados en `sections/` contra la carga canónica de `project.json`.
- **Pruebas de Resiliencia y Regresión de Reindexación (`tests/unit/test_rag_documents_and_routes.py`, `TF-TEST-001`, `TF-TEST-002`):**
  - Pruebas exhaustivas para reindexación con contenido modificado (`PDF v1 -> PDF v2`) confirmando diferenciación de hashes, ausencia de fragmentos obsoletos y actualización de citas.
  - Pruebas de simulación de fallos en parsing y almacenamiento vectorial demostrando la preservación de fragmentos en SQLite y la reconstrucción exitosa mediante `rebuild_chroma_from_sqlite()`.
- **Rigor Epistémico & Grounding Negation-Aware (`src/thesisforge/rag/citation_guard.py`):**
  - Implementación de `_check_negation_in_proximity` con tokens prepositivos (`window=2`) para verbos y predicados (`no`, `sin`, `nunca`, `jamás`, `not`, `never`, etc.), penalizando severamente (factor `0.2x`) asimetrías de polaridad para impedir falsos positivos en afirmaciones contradichas por la literatura.
  - Incorporación de `epistemic_notice` en `EvidenceVerdictDTO` advirtiendo formalmente que la correspondencia léxica/semántica no sustituye la validación ontológica ni metodológica concluyente del estudio original.
- **Transparencia en Flujo PRISMA 2020 (`src/thesisforge/rag/prisma.py`, `src/thesisforge/rag/service.py`):**
  - Adición de `is_exploratory_synthesis: bool` y `protocol_notice` en `PRISMAFlowReport`.
  - Rotulación explícita como `# Diagrama de Flujo de Literatura (Inspirado en PRISMA 2020 - Síntesis Exploratoria)` cuando el flujo se deriva de citas ya indexadas sin búsqueda estructurada previa, documentando los requisitos para revisiones sistemáticas formales (PROSPERO, cribado ciego y análisis RoB).
- **Transparencia en Jurado Evaluador & Scoring Heurístico (`src/thesisforge/jury/evaluator.py`, `src/thesisforge/models.py`):**
  - Etiquetado explícito con `is_fallback=True` e `is_synthetic_persona=True` en jurados omitidos y evaluaciones basadas en reglas.
  - Exposición de la matriz de ponderación (`scoring_rubric`: Metodología 35%, Literatura 25%, Empírico 25%, Crítico 15%) y aviso formal `rubric_notice` en `JuryEvaluationReportDTO`, clarificando su naturaleza pedagógica orientativa.
- **Tratado Integral de Metodología de la Investigación Científica (`src/thesisforge/llm/prompts.py`, `src/thesisforge/drafting/templates.py`, `src/thesisforge/advisor/validators.py`):**
  - **Capítulo I (Planteamiento del Problema):** Arquitectura en 8 movimientos, formulación de preguntas con 5 componentes anatómicos no dicotómicos, regla de oro de objetivos ($OG \equiv PG$), justificación en 4 dimensiones con formulación negativa y fórmula de limitaciones en 4 pasos.
  - **Capítulo IV (Resultados y Discusión):** Distinción conceptual (*Resultado $\to$ Análisis $\to$ Discusión*), secuencia cuantitativa en 3 niveles, reporte APA 7 en 4 componentes ($M/DT$, estadístico con $gl$, $p$-exacto sin cero inicial, tamaño del efecto con IC 95%), análisis cualitativo en 4 movimientos con casos discrepantes, triangulación en 3 movimientos, *Joint Display* mixto dialógico y auditoría de los 20 errores metodológicos fatales de jurado.
  - **Capítulo V (Conclusiones y Recomendaciones):** Cadena descendente (*Resultado $\to$ Conclusión $\to$ Implicación $\to$ Recomendación*), principio de correspondencia isomórfica ($N = N$), 3 tipos de conclusiones por certeza epistémica, recomendaciones en 4 componentes por destinatario explícito y sección canónica `sec_5_3` (Aportes a la ciencia y transferencia social / originalidad).

### Security & Hardening
- **Protección y Aislamiento en Handshake y Framing de WebSockets (`src/thesisforge/api/routes_drafting.py`, `src/thesisforge/api/routes_defense.py`, `tests/integration/test_websocket_protection.py`, `TF-WS-001`, `TF-WS-002`, `TF-WS-003`, `TF-TEST-003`):**
  - Validación de existencia de proyecto, sección o sesión previa al handshake (`websocket.accept()`), cerrando con código WS 1008 (Policy Violation) ante accesos inválidos.
  - Negociación formal del subprotocolo WebSocket (`bearer`).
  - Timeout de inactividad de 120s mediante `asyncio.wait_for`.
  - Límite de carga útil de 5.000 caracteres por mensaje para prevenir agotamiento de memoria (`PAYLOAD_TOO_LARGE`).
  - Sanitización exhaustiva de errores en tramas WebSocket, eliminando la filtración de trazas y cadenas crudas mediante códigos semánticos (`LLM_PROVIDER_ERROR`, `INTERNAL_ERROR`).
- **Defensa contra DNS Rebinding y Filtración en Clientes Académicos (`src/thesisforge/core/security.py`, `src/thesisforge/rag/clients/base.py`, `TF-SEC-007`, `TF-SEC-008`, `TF-LLM-001-R1`):**
  - Lista blanca obligatoria `DEFAULT_ALLOWED_ACADEMIC_HOSTS` para Semantic Scholar, CrossRef, arXiv y OpenAlex.
  - Verificación reforzada de direcciones IP resueltas (`is_private`, `is_loopback`, `is_link_local`, `is_reserved`, `is_multicast`).
  - Límite estricto de descarga HTTP a 15 MB con verificación de `Content-Length` y corte en flujo por chunks (`DEFAULT_MAX_RESPONSE_BYTES`).
  - Desinfección de detalles públicos en `AcademicAPIError` protegiendo información sensible en logs privados.
- **Manejadores Globales de Errores de Red y Clientes Académicos (`src/thesisforge/api/app.py`, `tests/integration/test_literature_api_routes.py`):**
  - Registro de excepción explícito para `SSRFBlockedError` respondiendo con HTTP 403 Forbidden y estructura tipada de rechazo.
  - Registro de excepción explícito para `AcademicAPIError` respondiendo con HTTP 502 Bad Gateway y supresión de trazas internas sensibles.
- **Endurecimiento de Despliegue en Contenedores (`docker-compose.yml`, `TF-DOCKER-001`):**
  - Incorporación de `cap_drop: [ALL]`, sistema de archivos raíz de solo lectura (`read_only: true`), `tmpfs: [/tmp]` para archivos efímeros y cuotas de recursos `deploy.resources.limits` (2 CPUs, 2048 MB RAM).
- **Alineación de Quality Gate en Release (`.github/workflows/release.yml`, `TF-CI-001`):**
  - Job `verify-gate` previo al empaquetado y publicación que valida Ruff linter, formato, tipado estricto mypy, Bandit SAST y suite completa de pruebas unitarias, integradas y de propiedades.
- **Eliminación de tokens en query strings (`src/thesisforge/core/auth.py`, `TF-SEC-001`):**
  - Eliminación completa de la autenticación mediante `?token=` en URLs; soporte exclusivo de `Authorization: Bearer <token>` y encabezado `Sec-WebSocket-Protocol`.
- **Política estricta de emisión de tokens (`src/thesisforge/core/auth.py`, `TF-SEC-002`):**
  - Supresión de la impresión de tokens en stdout en entornos de producción y tests; fallo explícito con `ConfigurationError` si no se puede persistir el token en producción.
- **Defensa contra SSRF en cadenas de redirección (`src/thesisforge/rag/clients/base.py`, `src/thesisforge/rag/clients/arxiv.py`, `TF-SEC-003`):**
  - Bucle manual de verificación asíncrona de cada encabezado `Location` antes de redirigir, interceptando redirecciones maliciosas con un máximo de 5 saltos.
- **Creación atómica de claves y tokens (`src/thesisforge/core/security.py`, `src/thesisforge/core/auth.py`, `TF-DATA-005`):**
  - Uso de `os.open` con `O_CREAT | O_EXCL`, `os.fsync` y reintento ante `FileExistsError` para prevenir condiciones de carrera en inicios concurrentes.

### Fixed & Improved
- **Atomicidad y Recuperación en Reindexación RAG (`src/thesisforge/rag/service.py`, `src/thesisforge/rag/parser.py`, `TF-DATA-001-R1`, `TF-DATA-001-R2`):**
  - Transacción SQLite atómica única (`DELETE` + `INSERT` antes de `commit`) previniendo estados huérfanos si la indexación vectorial falla.
  - Determinismo estricto de chunks incluyendo `project_id` en el identificador (`f"{project_id}_{document_id}_p{page}_c{chunk}_{hash}"`).
  - Habilitación de `rebuild_chroma_from_sqlite()` para recuperar documentos en estado `failed`, promoviéndolos a `indexed` tras reinsertar los vectores.
  - Actualización atómica de citas en `project.validated_citations` al reindexar documentos existentes.

### Fixed
- **Preservación de Estado y Progresión en Asesor Metodológico (`src/thesisforge/advisor/service.py`):**
  - Corregido el bug que devolvía al usuario a la Sección 3 tras guardar entradas, preservando íntegramente los campos de hipótesis, operacionalización de variables y categorías cualitativas.
- **Conformidad CI / Quality Gate (`.github/workflows/ci.yml`):**
  - Corrección de importaciones y reglas de formateo Ruff (`I001`, `SIM102`, `SIM105`), tipado mypy estricto sin errores.
- **[CRITICAL] Concurrencia optimista en proyectos**: Añadida columna `version` a la tabla `projects` (migración v3). `PUT /api/projects/{id}` ahora acepta el header `X-Project-Version`; si la versión no coincide, devuelve HTTP 409 en lugar de sobrescribir silenciosamente cambios concurrentes de la GUI o los WebSockets (`project_repository.update_project_versioned`, `ProjectVersionConflictError`).
- **[HIGH] KeyVault: eliminado fallback silencioso a clave en RAM**: `resolve_or_create_master_key()` ahora lanza `KeyVaultError` en lugar de continuar con una clave efímera cuando falla la escritura en disco. Esto evita que todos los secretos cifrados se vuelvan irrecuperables tras un reinicio.
- **[HIGH] Streaming LLM: retry pre-primer-token**: `stream_completion()` ahora reintenta la conexión con la misma política de backoff exponencial que `complete()`, pero solo antes del primer token. Una vez iniciado el stream, los fallos se propagan inmediatamente como `LLMProviderError` para evitar contenido duplicado.
- **[MEDIUM] Limpieza de ChromaDB al eliminar proyectos**: `DELETE /api/projects/{id}` ya limpiaba la colección Chroma; se clarificó el contrato en el docstring y se verificó la cadena completa de borrado.
- **[MEDIUM] Versión del schema de la base de datos**: Añadida migración v3 (`_v3_add_version_column`) compatible con bases de datos existentes (usa `PRAGMA table_info` para no fallar en upgrades).

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
  - Configuración dinámica de orígenes permitidos `cors_origins` en `AppSettings`.
  - Cabecera `Content-Security-Policy` ajustada para admitir CDNs seguras y WebSockets.
- **Suite de Pruebas Automatizadas:**
  - 186 pruebas automatizadas unitarias, de integración y seguridad 100% aprobadas.

---

## [0.4.0] - 2026-09-22

### Added
- **Tribunal Académico Multi-Agente & Motor de Auditoría Científica (`src/thesisforge/jury/`):**
  - Panel evaluador multi-perspectiva compuesto por 4 roles doctorales independientes (`MultiAgentJuryEngine` en `src/thesisforge/jury/evaluator.py`):
    - *Dr. Arístides Valenzuela (Metodólogo y Epistemólogo)*: Audita consistencia interna, delimitación espacio-temporal, congruencia de objetivos e hipótesis y validez metodológica.
    - *Dra. Beatriz Salamanca (Especialista Temática)*: Evalúa suficiencia del estado del arte, pertinencia de literatura indexada y profundidad teórica.
    - *Dr. Camilo Restrepo (Auditor Estadístico y Cuantitativo)*: Evalúa representatividad muestral, idoneidad de instrumentos de medición y supuestos de pruebas estadísticas.
    - *Dr. Demetrio Sotomayor (Evaluador Crítico / Abogado del Diablo)*: Cuestiona supuestos no declarados, sesgos de confirmación y explicaciones causales alternativas.
  - Motor híbrido de auditoría científica que combina reglas deterministas con análisis semántico profundo asistido por LLM.
  - Sistema de calificación multidimensional ponderado (0.0 a 100.0) y cálculo de dictámenes oficiales académicos: *Aprobado con Distinción ($\ge 95$)*, *Aprobado ($\ge 80$)*, *Modificaciones Menores ($\ge 70$)*, *Modificaciones Mayores ($\ge 50$)* y *No Aprobado ($< 50$)*.
- **Simulador Interactivo de Sustentación Oral Socrática (`src/thesisforge/jury/defense.py`):**
  - Motor de defensa por turnos `ThesisDefenseSimulator` que genera 4 preguntas desafiantes contextualizadas al nivel académico del estudiante (Pregrado, Maestría, Doctorado) y a las debilidades del proyecto.
  - Evaluación analítica de réplicas orales considerando solidez argumentativa, respaldo empírico, terminología disciplinar y reconocimiento honesto de limitaciones.
- **Persistencia Transaccional de Dictámenes y Sesiones (`src/thesisforge/repository/jury_repository.py`):**
  - Repositorio asíncrono SQLite `JuryRepository` para almacenamiento estructurado de informes de jurado (`jury_evaluations`) y sesiones de defensa oral (`defense_sessions`).
- **Endpoints REST, WebSockets y Comandos CLI:**
  - Rutas REST `/api/jury` y `/api/defense`.
  - Endpoint WebSocket `/api/defense/ws/{session_id}` para sustentación interactiva bidireccional en tiempo real.
  - Subcomandos de consola CLI: `thesisforge jury-audit --project-id <id>` y `thesisforge defense-start --project-id <id>`.

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
  - Servicio de redacción `DraftService` con streaming en tiempo real vía WebSockets (`/api/drafting/ws/...`).
- **Compilador DOCX APA 7ª Edición y Servicio de Exportación:**
  - Compilador `APA7DocxCompiler` con márgenes de 2.54 cm, tipografía formal, doble espacio, 5 niveles de encabezados, tablas sanitizadas (CWE-1236), sangría francesa y Tabla de Contenidos (TOC).
- **Manual de Usuario Oficial:**
  - Manual ilustrado integral (`docs/user-guide/MANUAL_DE_USUARIO.md`).

---

## [0.2.0] - 2026-09-19

### Added
- **Clientes Académicos Asíncronos:**
  - `SemanticScholarClient`, `ArxivClient`, `CrossRefClient`, `AcademicSearchAggregator` y `LiteratureCache` (SQLite con TTL 48h).
- **Indexación y Recuperación Vectorial (RAG):**
  - `PDFDocumentParser` (PyMuPDF con sanitización anti-Prompt Injection y chunking contextual por oraciones) y `ChromaVectorStore`.
- **Formateo APA 7ª Edición y Citation Guard:**
  - `APA7Formatter` y `CitationGuard` para claim-evidence grounding y validación de DOIs.

---

## [0.1.0] - 2026-09-18

### Added
- **Core de Seguridad & Persistencia:**
  - SSRF Guard (`assert_safe_academic_url`), cifrado simétrico Fernet `LocalKeyVault`, structured JSON logging (CWE-117) y base de datos asíncrona SQLite WAL (`DatabaseManager`).
- **Router LLM BYOK:**
  - `LLMRouter` con soporte para OpenRouter, Gemini, Groq, Ollama, OpenAI, Anthropic y NVIDIA NIM.
