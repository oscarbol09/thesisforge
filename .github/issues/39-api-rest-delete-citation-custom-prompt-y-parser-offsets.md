### Descripción del Problema
Se identificaron tres defectos acotados en contratos REST e indexación de fragmentos que devuelven respuestas falsamente exitosas, descartan parámetros del cliente o calculan desplazamientos incorrectos:

### Evidencia en Código
1. **`DELETE` de cita inexistente devuelve HTTP `200` (`src/thesisforge/api/routes_literature.py`, líneas 217–227):**
   `delete_project_citation` filtra `project.validated_citations`, reescribe y guarda el proyecto en SQLite incluso cuando `citation_id` no existía en la lista, devolviendo siempre `200 {"status": "deleted"}` en lugar de `404 Not Found`.
   *(Nota: verificar que `DELETE /api/projects/{id}` ya devuelve `404 PROJECT_NOT_FOUND` vía `ProjectNotFoundError`, a diferencia del endpoint de citas).*
2. **`GenerateDraftRequest.custom_prompt` aceptado e ignorado (`src/thesisforge/api/routes_drafting.py`, líneas 28–35 y 83–98):**
   El esquema Pydantic acepta `custom_prompt` (`max_length=5000`), pero el controlador `POST .../generate` nunca lo reenvía ni lo incorpora a la generación en `DraftService.generate_section(...)`.
3. **Deriva de `char_start` / `char_end` al chunkear PDFs (`src/thesisforge/rag/parser.py`, líneas 154–168):**
   Al avanzar entre chunks solapados dentro de una misma página, el cursor actualiza `char_cursor = char_end` sin restar la longitud real del overlap retrocedido, provocando que los offsets `char_start` y `char_end` se desvíen en chunks posteriores.

### Solución Esperada (Good First Issue)
1. En `delete_project_citation` (`routes_literature.py`), comprobar si la lista filtrada redujo su tamaño; si `citation_id` no estaba presente, evitar escritura innecesaria en BD y responder con HTTP `404` (`ResourceNotFoundError` o `HTTPException(404)` con formato de error estándar).
2. Conectar `body.custom_prompt` en `routes_drafting.py` hacia `DraftService.generate_section` (cuarentenado con `<user_input>` al inyectarlo en el prompt, o eliminarlo explícitamente del contrato si no está soportado).
3. En `src/thesisforge/rag/parser.py`, calcular el siguiente `char_cursor` descontando el solapamiento (`next_cursor = max(char_end - overlap_len, char_cursor + 1)` o buscar la posición real del chunk siguiente) y cubrirlo con tests unitarios.
