# Registro de Cambios (Changelog)

Todas las modificaciones notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

### Planned
- Empaquetado ejecutable autónomo standalone (.exe, .dmg, AppImage) y distribución en PyPI (Sprint 6 / v1.0.0).

---

## [0.5.1] - 2026-09-23

### Security & Hardening
- **Defensa contra DNS Rebinding (TOCTOU) en SSRFGuard:**
  - Implementación de `CustomAsyncHTTPTransport` que enlaza el socket directamente a la IP validada pre-resuelta, eliminando la ventana de vulnerabilidad entre validación DNS y petición HTTP.
- **Bóveda de Claves con Derivación de Sal Criptográfica Única:**
  - Robustecimiento de `LocalKeyVault` para generar y persistir sales PBKDF2 únicas por secreto almacenado.

### Fixed & Improved
- **Compilador DOCX APA 7 (`src/thesisforge/export/docx_compiler.py`):**
  - Inserción de campo dinámico Word XML `TOC \o "1-3" \h \z \u` con instrucción explícita de actualización F9/Cmd+A.
  - Desduplicación estricta de referencias bibliográficas combinando normalización de DOIs y tuplas (primer autor, año, título).
  - Jerarquía de 5 niveles de encabezados según estándar APA 7.
- **Evaluador de Jurados Multi-Agente (`src/thesisforge/jury/evaluator.py`):**
  - Normalización robusta de roles contra diacríticos y variantes ortográficas.
  - Ponderaciones calibradas: Metodólogo 35%, Temático 25%, Estadístico 25%, Abogado del Diablo 15%.
  - Regla de veto y umbrales de dictamen alineados ($\ge 95, \ge 80, \ge 70, \ge 50, < 50$).
- **SPA Frontend & Resiliencia WebSocket (`gui/js/`):**
  - Manejo de reconexión con *exponential backoff* en sockets de redacción capitular y sustentación oral.
  - Mejora de contraste tipográfico y accesibilidad WCAG 2.2 en componentes oscuros y modales.

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
