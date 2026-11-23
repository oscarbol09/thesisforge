### Descripción del Problema
El limpiador textual `detoxify_text` destruye la estructura Markdown de los borradores académicos (párrafos `\n\n`, encabezados `#` y viñetas `-`), descarta líneas cortas de `<= 3` caracteres, rompe frases ante abreviaturas comunes del español (`p.`, `pp.`, `Dr.`, `Dra.`, `vs.`, `cfr.`) y pierde detección en `STANDARD_CITATION_PATTERN` con autores multi-palabra o con tildes/guiones.

### Evidencia en Código
1. En `src/thesisforge/drafting/detox.py`:
   - Líneas 128–133 (`split_into_sentences`): filtra segmentos con longitud `<= 3` caracteres (línea 133) y no contempla abreviaturas académicas habituales (`p.`, `pp.`, `Dr.`, `Dra.`, `vs.`, `cfr.`) en su lista de exclusiones (línea 131).
   - Líneas 265–295 (`detoxify_text`): procesa el borrador completo pasándolo por `split_into_sentences` y recombinándolo mediante `" ".join(...)` (líneas 287–294), aplastando encabezados, listas y separaciones de párrafo en una sola línea continua, además de alterar capitalizaciones iniciales.
   - Líneas 76–84 (`STANDARD_CITATION_PATTERN`): su patrón regex de cita APA/parentética no casa adecuadamente con múltiples autores unidos por `&`/`y` ni apellidos hispanos con guiones o acentos.

### Reproducción Verificada
- Al ejecutar `detoxify_text` sobre texto Markdown con encabezados, párrafos y viñetas, la salida colapsó los saltos estructurales en un bloque plano (`- Primer... - No.`), eliminó fragmentos breves y dejó minúscula inicial tras ciertos reemplazos (p. ej. `este`).
- `STANDARD_CITATION_PATTERN.findall("Según (Pérez & López, 2023) y (García-Márquez, 1982).")` devolvió `[]`.

### Comportamiento Esperado
1. Preservar la estructura por bloques/párrafos/líneas Markdown en `detoxify_text` (procesando párrafo a párrafo o bloque a bloque sin unir todo el documento con `" ".join(...)`, manteniendo intactos encabezados, saltos `\n\n` y viñetas `-` / `*` y preservando mayúsculas al inicio de oración).
2. Ampliar la lista de abreviaturas en `split_into_sentences` (`p.`, `pp.`, `Dr.`, `Dra.`, `vs.`, `cfr.`, entre otras) y evitar la eliminación silenciosa de fragmentos cortos significativos.
3. Corregir `STANDARD_CITATION_PATTERN` para reconocer citas en español con `&` / `y`, caracteres Unicode/diacríticos y apellidos compuestos con guion.
4. Añadir tests unitarios que verifiquen preservación de Markdown, abreviaturas académicas y extracción de citas multi-autor en español.
