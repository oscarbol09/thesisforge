### Descripción del Problema / Propuesta (RFC)
En la hoja de ruta de ThesisForge (`ROADMAP.md` y `ARCHITECTURE.md`), se proyecta la exportación de proyectos a formatos académicos de ingeniería y ciencias exactas, específicamente **LaTeX** estructurado compatible con compilación en Overleaf y TeX Live local.

Actualmente, el sistema sólo compila a formato Word (`.docx`) mediante `docx_compiler.py`. Muchos investigadores de ciencias de la computación, física, matemáticas e ingeniería requieren presentar sus trabajos de grado en plantillas LaTeX estándar con archivos `.bib` para BibTeX/BibLaTeX.

### Especificación de la Característica
1. **Nuevo Compilador (`src/thesisforge/infrastructure/exporters/latex_compiler.py`)**:
   - Generación de estructura modular en archivo `.zip`:
     - `main.tex`: Estructura del documento con preámbulo, paquetes estándar (`babel`, `csquotes`, `amsmath`, `hyperref`, `booktabs`, `biblatex`), portada formal y comandos `\input{chapters/...}`.
     - `chapters/`: Un archivo `.tex` por cada capítulo del proyecto (p. ej. `01_introduccion.tex`, `02_marco_teorico.tex`, etc.).
     - `references.bib`: Entradas BibTeX limpias extraídas de la base de datos de literatura del proyecto (con claves de citación estables `AuthorYear`).
   - Conversión de markdown a comandos LaTeX básicos (negrita, cursiva, listas, tablas y entornos matemáticos `\begin{equation}`).
   - Escape de caracteres especiales de TeX (`%`, `$`, `&`, `_`, `#`, `{`, `}`, `^`, `~`).

2. **Integración en la API**:
   - Extender `ExportFormat` enum con `LATEX = "latex"`.
   - Modificar `POST /api/export/{project_id}` para generar y retornar el `.zip` con el proyecto LaTeX listo para compilar.

3. **Interfaz Gráfica**:
   - Añadir la tarjeta de selección "LaTeX / Overleaf (ZIP con .tex y .bib)" en la vista `export.html`.
