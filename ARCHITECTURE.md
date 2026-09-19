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
