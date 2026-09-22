# Catálogo de Issues para Nuevos Contribuidores (Good First Issues)

Este documento contiene la definición completa de tareas diseñadas específicamente para **nuevos contribuidores** (`good first issue` y `help wanted`) en **ThesisForge**. Cada tarea está acotada, modularizada y cuenta con contexto técnico, archivos involucrados y criterios de aceptación.

---

## Issue 1: Conector Académico para OpenAlex API
* **Título:** `feat(rag): add OpenAlex academic search client connector`
* **Etiquetas:** `good first issue`, `help wanted`, `rag`, `enhancement`
* **Nivel de dificultad:** Fácil / Intermedio
* **Archivos a modificar:**
  - [`src/thesisforge/rag/clients/openalex.py`](file:///c:/Users/dario/OneDrive/Documentos/Repositorio_Ayuda/ThesisForge/src/thesisforge/rag/clients/openalex.py) (Nuevo)
  - [`src/thesisforge/rag/clients/__init__.py`](file:///c:/Users/dario/OneDrive/Documentos/Repositorio_Ayuda/ThesisForge/src/thesisforge/rag/clients/__init__.py)
  - [`src/thesisforge/rag/clients/aggregator.py`](file:///c:/Users/dario/OneDrive/Documentos/Repositorio_Ayuda/ThesisForge/src/thesisforge/rag/clients/aggregator.py)
  - `tests/unit/test_openalex_client.py` (Nuevo)

### Descripción:
Actualmente ThesisForge busca literatura a través de Semantic Scholar, ArXiv y CrossRef. [OpenAlex](https://openalex.org/) es un catálogo científico abierto y gratuito con más de 250M de trabajos que no requiere autenticación obligatoria para consultas públicas.

### Requisitos:
1. Implementar `OpenAlexClient` heredando de `BaseAcademicClient` (`src/thesisforge/rag/clients/base.py`).
2. Usar `httpx.AsyncClient` para consumir el endpoint `https://api.openalex.org/works?search={query}&per_page={limit}`.
3. Mapear la respuesta al modelo `AcademicPaper` existente (título, autores, año, resumen, DOI, url de PDF en open access).
4. Agregar pruebas unitarias con `pytest` y fixtures herméticos usando `respx` o `pytest-asyncio`.

---

## Issue 2: Exportación de Citas en Formato BibTeX (.bib)
* **Título:** `feat(export): add BibTeX (.bib) export command for Zotero and Overleaf`
* **Etiquetas:** `good first issue`, `help wanted`, `export`, `cli`
* **Nivel de dificultad:** Fácil
* **Archivos a modificar:**
  - [`src/thesisforge/export/bibtex_formatter.py`](file:///c:/Users/dario/OneDrive/Documentos/Repositorio_Ayuda/ThesisForge/src/thesisforge/export/bibtex_formatter.py) (Nuevo)
  - [`src/thesisforge/cli.py`](file:///c:/Users/dario/OneDrive/Documentos/Repositorio_Ayuda/ThesisForge/src/thesisforge/cli.py)
  - `tests/unit/test_bibtex_export.py` (Nuevo)

### Descripción:
Permitir que los investigadores exporten toda la bibliografía recopilada e indexada en un proyecto a un archivo `.bib` estándar para importarlo directamente en gestores como Zotero, Mendeley o editores LaTeX como Overleaf.

### Requisitos:
1. Crear una función `format_bibtex_entry(paper: AcademicPaper) -> str` que genere entradas estándar `@article{...}` o `@book{...}` con sanitización de caracteres especiales.
2. Añadir el subcomando en la CLI: `thesisforge export-bibtex --project-id <ID> --output ./referencias.bib`.
3. Validar que los campos como `title`, `author`, `year`, `journal`, `doi` y `url` se formateen correctamente.

---

## Issue 3: Formateador de Citas en Estilo Vancouver e IEEE
* **Título:** `feat(citation): add IEEE and Vancouver citation style formatters`
* **Etiquetas:** `good first issue`, `help wanted`, `rag`, `academic`
* **Nivel de dificultad:** Fácil
* **Archivos a modificar:**
  - [`src/thesisforge/rag/ieee_formatter.py`](file:///c:/Users/dario/OneDrive/Documentos/Repositorio_Ayuda/ThesisForge/src/thesisforge/rag/ieee_formatter.py) (Nuevo)
  - [`src/thesisforge/rag/vancouver_formatter.py`](file:///c:/Users/dario/OneDrive/Documentos/Repositorio_Ayuda/ThesisForge/src/thesisforge/rag/vancouver_formatter.py) (Nuevo)
  - [`src/thesisforge/rag/apa_formatter.py`](file:///c:/Users/dario/OneDrive/Documentos/Repositorio_Ayuda/ThesisForge/src/thesisforge/rag/apa_formatter.py) (Como referencia)
  - `tests/unit/test_citation_formatters.py` (Nuevo)

### Descripción:
ThesisForge actualmente cuenta con un formateador estricto para APA 7ª edición. Para estudiantes de ingenierías y ciencias de la salud, es necesario soportar citas numéricas en formato IEEE (`[1]`) y Vancouver (`(1)`).

### Requisitos:
1. Implementar funciones deterministas que tomen una lista de `AcademicPaper` y devuelvan las referencias bibliográficas ordenadas según las reglas de IEEE y Vancouver.
2. Manejar casos de autores corporativos, múltiples autores (>3 y >6) y artículos sin DOI.
3. Incluir pruebas basadas en propiedades o casos de prueba exhaustivos en `pytest`.

---

## Issue 4: Spinner visual y barra de progreso con Rich para el CLI
* **Título:** `enhancement(cli): add Rich spinner and progress bars for RAG indexing and PDF downloads`
* **Etiquetas:** `good first issue`, `help wanted`, `cli`, `ux`
* **Nivel de dificultad:** Fácil
* **Archivos a modificar:**
  - [`src/thesisforge/cli.py`](file:///c:/Users/dario/OneDrive/Documentos/Repositorio_Ayuda/ThesisForge/src/thesisforge/cli.py)
  - [`pyproject.toml`](file:///c:/Users/dario/OneDrive/Documentos/Repositorio_Ayuda/ThesisForge/pyproject.toml) (si se requiere `rich`)

### Descripción:
Al buscar literatura con `thesisforge search-papers` o indexar PDFs pesados en ChromaDB, la consola actualmente imprime texto plano. Agregar indicadores visuales con la biblioteca `rich` mejorará notablemente la experiencia de usuario en terminal.

### Requisitos:
1. Integrar `rich.progress` o `rich.console` en los comandos CLI de larga duración.
2. Mantener la compatibilidad en terminales Windows (PowerShell), Linux y macOS.
3. Asegurar que las salidas en modo `--json` o pipes no se corrompan con secuencias de escape ANSI.
