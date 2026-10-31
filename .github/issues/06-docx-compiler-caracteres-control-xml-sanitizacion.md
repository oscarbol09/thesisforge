### Descripción del Problema
Al exportar un proyecto de tesis a formato Word (`.docx`) mediante el compilador APA 7 (`src/thesisforge/infrastructure/exporters/docx_compiler.py`), si el texto generado por el LLM o extraído desde abstracts/PDFs científicos contiene caracteres de control ASCII (como bytes nulos `\x00`, form feeds `\x0c`, backspaces `\x08` u otros caracteres en el rango `[\x00-\x08\x0B-\x0C\x0E-\x1F]`), la librería subyacente `python-docx` / `lxml` lanza una excepción no capturada de validación XML:
```
ValueError: All strings must be XML compatible: Unicode or ASCII, no NULL bytes or control characters
```
Esto genera un error 500 en el endpoint `POST /api/export/{project_id}` y el usuario no puede descargar su documento de tesis.

### Causa Raíz
Los LLMs (especialmente cuando citan PDFs con codificaciones extrañas o extracción OCR defectuosa) ocasionalmente emiten caracteres de control de bajo nivel.
En `docx_compiler.py`, los párrafos, títulos, celdas de tabla y citas bibliográficas se insertan directamente en el documento con `doc.add_paragraph(...)` sin una etapa previa de sanitización de caracteres XML no válidos.

### Comportamiento Esperado
1. Implementar una función utilitaria de sanitización estricta para XML 1.0 (que filtre caracteres en los rangos prohibidos `[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x84\x86-\x9F]`) antes de escribir texto en `docx_compiler.py`.
2. Aplicar la sanitización a todos los campos textuales del proyecto: título, autor, afiliación, secciones de capítulos, tablas y referencias bibliográficas.
3. Añadir tests unitarios en `tests/unit/test_docx_compiler.py` verificando que entradas con bytes `\x00`, `\x08`, `\x0c` se limpien transparentemente y el documento `.docx` se genere y abra sin corrupción.
