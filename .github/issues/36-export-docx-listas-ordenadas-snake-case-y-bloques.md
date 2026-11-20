### Descripción del Problema
El compilador APA 7 a Microsoft Word (`APA7DocxCompiler`) presenta cuatro defectos de formato en la generación de documentos `.docx`:
1. Las listas numeradas pierden su numeración consecutiva (`1.`, `2.`, `3.`) y muestran `"1.  "` en todos los elementos.
2. Las palabras o identificadores en `snake_case` y URLs con guiones bajos (`_`) se parten erróneamente en segmentos en cursiva.
3. Los bloques de código delimitados (```` ```...``` ````) y ecuaciones de bloque (`$$...$$`) se degradan a párrafos planos en línea.
4. La sección **Referencias** se ordena alfabéticamente por nombre de pila cuando los autores están almacenados como `"Nombre Apellido"` y omite reutilizar `APA7Formatter` en el fallback.

### Evidencia en Código
En `src/thesisforge/export/docx_compiler.py`:
1. **Listas ordenadas (`líneas 343–348` y `443–460`):**
   `_render_list_item` ignora el número capturado en `num_match.group(1)` y escribe literalmente `"1.  "`, además de crear `p.add_run(bullet_prefix)` sin aplicar la tipografía/tamaño configurados del documento.
2. **Regex de cursivas sobre `snake_case` (`línea 656`):**
   El patrón `_[^_]+_` detecta guiones bajos intraléxicos (por ejemplo `project_id_v2` o rutas URL), convirtiendo fragmentos intermedios en itálicas inesperadas.
3. **Bloques de código y ecuaciones (`líneas 300–362`):**
   El parser de líneas no contempla bloques multi-línea ```` ``` ```` ni `$$...$$`, por lo que caen en `_render_paragraph` y se aplastan como texto ordinario.
4. **Ordenación y formato de Referencias (`líneas 578–583` y `599–647`):**
   Ordena usando `c.authors[0].lower()`, lo cual ordena por `"ashish vaswani"` (`A`) en vez de `"vaswani"` (`V`). Asimismo, el fallback de generación de referencia no delega en `APA7Formatter` (`src/thesisforge/rag/apa_formatter.py`).

### Comportamiento Esperado
1. Preservar `f"{num_match.group(1)}.  "` en listas numeradas y aplicar la fuente/tamaño activos al run del prefijo en `_render_list_item`.
2. Restringir la detección de cursivas con `_` únicamente a límites de palabra (`(?<!\w)_([^_\n]+?)_(?!\w)`) para no corromper identificadores `snake_case` ni URLs.
3. Dar soporte específico en el bucle de parseo Markdown a bloques ```` ``` ```` (fuente monoespaciada / bloque) y ecuaciones `$$...$$` (párrafo centrado/destacado).
4. Ordenar la bibliografía APA 7 por apellido normalizado del primer autor y delegar el formateo fallback en `APA7Formatter`.
5. Añadir pruebas unitarias sobre un `.docx` generado con `python-docx` verificando numeración `1./2./3.`, integridad de `mi_variable_test`, bloques de código y orden alfabético por apellido.
