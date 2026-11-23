### Descripción del Problema
El formateador APA 7 (`APA7Formatter`) invierte autores institucionales y partículas de apellidos como si fueran nombres de pila, mientras que el exportador BibTeX (`BibTeXExporter`) omite palabras clave acentuadas del español al generar claves de cita y rechaza años históricos anteriores a 1800 en el citekey aunque los imprima en el campo `year`.

### Evidencia en Código
1. En `src/thesisforge/rag/apa_formatter.py` (líneas 8–35, `_parse_author_name`):
   - A diferencia de `ieee_formatter.py` y `vancouver_formatter.py`, `apa_formatter.py` carece de detección de autores corporativos (`_is_corporate_author`) y de manejo de partículas nobiliarias (`NAME_PARTICLES`), dividiendo ciegamente cualquier cadena por espacios.
2. En `src/thesisforge/export/bibtex_exporter.py`:
   - Línea 104 (`extract_title_keyword`): aplica `re.findall(r"\b[A-Za-z0-9]+\b", title)` **antes** de normalizar tildes/diacríticos con `slugify_ascii`. Toda palabra con vocal acentuada o `ñ` queda excluida del match ASCII.
   - Línea 129 (`generate_citekey`): restringe la extracción de año en el citekey con `1800 <= year <= 2100`, de modo que una fuente clásica anterior a 1800 cae en `nodate` dentro de la clave mientras conserva su año real en `year = {...}`.

### Reproducción Verificada
- `APA7Formatter.format_reference_entry(...)`:
  - `"World Health Organization"` se formateó como `"Organization, W. H."`.
  - `"Organización Mundial de la Salud"` se formateó como `"Salud, O. M. D. L."`.
  - `"Ludwig van Beethoven"` se formateó como `"Beethoven, L. V."`.
- `extract_title_keyword("Educación y diseño")` devolvió `"y"` y `extract_title_keyword("Análisis metodológico")` devolvió `"doc"`.
- `BibTeXExporter` para `year=1781` generó el registro `@misc{garcianodatesuperior,` a la vez que imprimía `year = {1781},`.

### Comportamiento Esperado
1. Incorporar heurística de autor corporativo (`_is_corporate_author`) y manejo de partículas (`NAME_PARTICLES`) en `src/thesisforge/rag/apa_formatter.py` reutilizando/alineando la lógica ya existente en `ieee_formatter.py` / `vancouver_formatter.py`.
2. Normalizar tildes y caracteres latinos con `slugify_ascii` **antes** de tokenizar palabras en `extract_title_keyword` (`src/thesisforge/export/bibtex_exporter.py`).
3. Ampliar el rango de años válidos en `generate_citekey` (por ejemplo `1 <= year <= 2100`, en sintonía con `CitationDTO`) para evitar `nodate` en obras anteriores a 1800.
4. Añadir pruebas unitarias para autores corporativos en inglés/español, partículas, títulos con tildes/`ñ` y citekeys históricos.
