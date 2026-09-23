# Arquitectura de ThesisForge

Este documento describe la arquitectura de software, los principios de diseño, el modelo de datos y las garantías de seguridad de **ThesisForge**.

---

## 1. Visión y Principios de Diseño

ThesisForge está diseñado bajo los siguientes principios arquitectónicos:

1. **Flujo de datos unidireccional:** Las capas superiores dependen de las inferiores, nunca al revés (`Routers` $\rightarrow$ `Services` $\rightarrow$ `Repositories` $\rightarrow$ `Database`).
2. **I/O no bloqueante estricto:** Ninguna llamada síncrona o de disco bloquea el Event Loop de Python.
3. **Seguridad por diseño (Zero Trust & Defense in Depth):** Toda entrada externa pasa por validación de esquemas (Pydantic v2), filtrado SSRF antes de realizar peticiones de red y cifrado en reposo para credenciales.
4. **Desacoplamiento BYOK (Bring Your Own Key):** La lógica de negocio no depende de un único proveedor de LLM; las llamadas se enrutan mediante adaptadores con interfaces unificadas.

---

## 2. Diagrama de Capas

```text
+-------------------------------------------------------------------+
|                        CAPA DE PRESENTACIÓN                       |
|   PyWebView Desktop GUI (.exe)  /  SPA Web (Tailwind + Alpine.js) |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                          CAPA HTTP / API                          |
|   FastAPI App  |  Security Headers Middleware  |  CORS Guard      |
|   Routers: /api/projects, /api/advisor, /api/rag, /api/generate   |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                          CAPA DE SERVICIOS                        |
|   AdvisorService       -> Máquina de estados y entrevista         |
|   RAGService           -> Búsqueda académica e indexación         |
|   DraftService         -> Generación modular con memoria          |
|   ExportService        -> Compilador DOCX / APA 7                 |
|   LLMRouter            -> LiteLLM + Tenacity Retries              |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        CAPA DE PERSISTENCIA                       |
|   ProjectRepository    -> SQLite Asíncrono (aiosqlite / WAL)      |
|   SecureKeyStore       -> Cifrado Fernet (AES-128-CBC / SHA-256)  |
|   VectorStoreAdapter   -> ChromaDB embebido local                 |
+-------------------------------------------------------------------+
```

---

## 3. Componentes Principales

### 3.1 Core de Seguridad (`src/thesisforge/core/`)
- **`assert_safe_academic_url`:** Previene ataques SSRF resolviendo el DNS y bloqueando rangos IP de subredes privadas RFC 1918, loopback IPv4/IPv6 (`127.0.0.1`, `::1`), direcciones link-local (`169.254.169.254`, `fe80::/10`) y subredes reservadas.
- **`LocalKeyVault`:** Implementa cifrado simétrico Fernet de 256 bits para proteger las claves de API de los usuarios en su base de datos local SQLite.
- **`StructuredJsonFormatter`:** Emite logs en formato JSON de una sola línea sanitizados contra inyección de saltos de línea (CWE-117) y enmascara tokens sensibles (`sk-...`, `Bearer ...`).
- **`utc_now`:** Garantiza el uso consistente de marcas de tiempo UTC con zona horaria explícita (`datetime.now(timezone.utc)`).

### 3.2 Dominio & Modelos (`src/thesisforge/models.py`)
- **`ProjectStateDTO`:** Entidad agregada raíz que almacena el estado completo del proyecto de investigación (problema, objetivos, hipótesis, citas validadas y secciones redactadas).
- **`CitationDTO`:** Metadatos normalizados de fuentes bibliográficas reales (DOI, autores, año, resumen, formato APA 7).
- **`MethodologyDTO`:** Ficha metodológica con validación de enfoque, diseño, población, muestra e instrumentos.
- **`SectionDraftDTO`:** Borrador estructurado de cada capítulo con contador de palabras, citas vinculadas y versión.

### 3.3 Router LLM (`src/thesisforge/llm/`)
- **`LLMRouter`:** Gestiona el despacho de peticiones a múltiples proveedores (OpenRouter, Gemini, Groq, Ollama, OpenAI, Anthropic) utilizando `litellm`.
- **Estrategia de reintentos:** Implementa reintentos asíncronos con `tenacity.AsyncRetrying` y retroceso exponencial, desactivando la espera en entornos de prueba (`environment == "test"`).
- **Modo JSON estructurado:** Valida y extrae cargas JSON limpiando automáticamente delimitadores de bloques de código markdown.

### 3.4 Asesor Metodológico (`src/thesisforge/advisor/`)
- **`AdvisorStateMachine`:** Controla la secuencia de pasos de la entrevista y calcula el porcentaje de avance.
- **`MethodologyValidator`:** Ejecuta auditorías de consistencia metodológica verificando la presencia de verbos taxonómicos en infinitivo, la formulación de preguntas y la coherencia de las hipótesis.
- **`AdvisorService`:** Orquesta la interacción con el usuario y el LLM, actualizando el estado del proyecto en la base de datos.

### 3.5 Persistencia (`src/thesisforge/repository/`)
- **`DatabaseManager`:** Administra conexiones asíncronas SQLite mediante `aiosqlite`, activando el modo WAL (`journal_mode = WAL`) y el soporte de claves foráneas.
- **`ProjectRepository`:** Proporciona operaciones CRUD transaccionales sobre la tabla `projects`.
- **`SecureKeyStoreRepository`:** Almacena y recupera claves de API cifradas en la tabla `keystore`.

### 3.6 Motor RAG y Literatura Académica (`src/thesisforge/rag/`)
- **`SemanticScholarClient`, `ArxivClient`, `CrossRefClient`:** Clientes asíncronos con protección SSRF y reintentos exponenciales para consulta de catálogos académicos globales.
- **`AcademicSearchAggregator`:** Orquesta búsquedas concurrentes multi-fuente y desduplica resultados por DOI canónico y firma autor-título-año.
- **`LiteratureCache`:** Caché persistente en SQLite con TTL configurable (48h) y purga periódica para prevenir rate limits.
- **`PDFDocumentParser`:** Extractor PyMuPDF con sanitización contra Prompt Injection y chunking estructurado por oraciones completas.
- **`ChromaVectorStore`:** Motor de indexación vectorial local sobre ChromaDB con embeddings deterministas ligeros (`FastLocalEmbeddingFunction`).
- **`APA7Formatter`:** Formateador estricto de citaciones parentéticas, narrativas y lista de referencias bajo normas APA 7ª edición.
- **`CitationGuard`:** Validador de DOIs y verificador de respaldo de afirmaciones (*claim-evidence grounding*) con umbrales configurables.

### 3.7 Motor de Redacción Modular & Memoria Jerárquica (`src/thesisforge/drafting/`)
- **`templates.py`:** Esquemas canónicos de 5 capítulos (19 secciones temáticas) para investigaciones cuantitativas, cualitativas y mixtas.
- **`HierarchicalMemoryManager`:** Ensambla el contexto de 4 capas (Capa 0: Núcleo metodológico inmutable; Capa 1: Resúmenes de capítulos previos; Capa 2: Fragmentos RAG relevantes; Capa 3: Directrices específicas de la sección).
- **`DraftService`:** Orquesta la generación de borradores, streaming por WebSockets, revisiones interactivas y aprobación de secciones con generación automática de resúmenes.
- **`sanitizer.py`:** Sanitización defensiva contra Formula Injection (CWE-1236) en celdas de tablas y depuración de bloques de código markdown.

### 3.8 Compilador DOCX & Exportación APA 7 (`src/thesisforge/export/`)
- **`APA7DocxCompiler`:** Generador de documentos Word `.docx` con cumplimiento estricto de normas APA 7ma edición (márgenes de 2.54 cm, tipografía Times New Roman 12pt, interlineado doble, 5 niveles de títulos, tablas sin bordes verticales, sangría francesa en referencias y portada académica).
- **`ExportService`:** Servicio asíncrono para exportación directa a memoria (`bytes`) y almacenamiento en disco.

### 3.9 Tribunal Académico Multi-Agente & Sustentación Oral Socrática (`src/thesisforge/jury/`)
- **`MultiAgentJuryEngine`:** Panel doctoral multi-perspectiva (Metodólogo, Especialista Temático, Auditor Estadístico, Abogado del Diablo) que combina auditorías deterministas de consistencia con evaluación cualitativa profunda asistida por LLM para calificar el proyecto (0.0 a 100.0) y emitir dictámenes oficiales.
- **`ThesisDefenseSimulator`:** Simulador interactivo de sustentación oral por turnos que genera rondas de preguntas incisivas y evalúa la solidez argumentativa, pertinencia empírica y reconocimiento de limitaciones de las réplicas del tesista.
- **`JuryService`:** Fachada de orquestación que administra el ciclo de vida de auditorías, sesiones de defensa oral y transiciones de fase del proyecto a `REVIEW` y `COMPLETED`.
- **`JuryRepository`:** Persistencia transaccional SQLite para informes de jurado (`jury_evaluations`) y sesiones de defensa (`defense_sessions`).

### 3.10 Interfaz Web SPA & Lanzador de Escritorio (`gui/`, `src/thesisforge/desktop/`)
- **SPA Monomando (`gui/`):** Aplicación cliente construida sobre HTML5 semántico, Alpine.js y Tailwind CSS servida directamente desde FastAPI sin dependencias de compilación en Node.js ni empaquetadores externos.
- **Sistema de Tokens Semánticos (`gui/css/tokens.css`):** Implementa el principio 60-30-10 con variables CSS para modos claro/oscuro, radios sobrios de 6px/8px, tipografía tabular y micro-interacciones rápidas (150ms-220ms).
- **Sanitización Defensiva en DOM:** Sanitización estricta de cualquier contenido generado por LLM mediante `DOMPurify` antes de su renderizado.
- **Lanzador Nativo PyWebView (`src/thesisforge/desktop/launcher.py`):** Asigna puertos TCP libres en loopback de forma dinámica, levanta el servidor Uvicorn en un hilo daemon en segundo plano, verifica el estado de salud mediante sondeo a `/health` y embebe la interfaz en una ventana nativa de escritorio con soporte de herramientas de desarrollo.

---

## 4. Estrategia de Pruebas y Calidad

El proyecto aplica una pirámide de pruebas automatizadas:

| Nivel de Prueba | Herramienta | Enfoque |
| :--- | :--- | :--- |
| **Unitarias** | `pytest` + `pytest-asyncio` | Aislamiento de lógica de negocio, validadores y transformaciones DTO. |
| **Basadas en Propiedades** | `Hypothesis` | Invariantes de cifrado/descifrado y sanitización sobre 100+ casos aleatorios. |
| **Integración HTTP** | `httpx.AsyncClient` | Ciclo completo de endpoints REST y middleware de seguridad. |
| **Tipado Estricto** | `mypy --strict` | Cero tipos dinámicos o implícitos en el código de producción. |
| **Seguridad SAST** | `bandit -r src/ -ll` | Análisis estático de vulnerabilidades y buenas prácticas de seguridad. |
