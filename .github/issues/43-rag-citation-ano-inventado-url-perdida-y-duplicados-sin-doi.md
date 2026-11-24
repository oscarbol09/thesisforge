### Descripción del Problema
El flujo de citas y RAG altera metadatos académicos reales al inventar años cuando faltan datos, descarta campos relevantes (`url` y `category`) al persistir una referencia en el proyecto, duplica citas idénticas cuando no tienen DOI y bloquea fuentes históricas anteriores a 1800 en `DocumentChunkDTO`.

### Evidencia en Código
1. Año inventado cuando el dato es nulo:
   - `src/thesisforge/rag/citation_guard.py` (línea 150): `year=chunk.year or 2024` fabrica el año `2024` sobre fragmentos sin año en lugar de preservar `None` / `(s.f.)`.
   - `src/thesisforge/rag/service.py` (líneas 430–432 en `index_pdf_document`) y `gui/js/literature.js` (línea 184): recurren a `utc_now().year` / `new Date().getFullYear()` cuando falta el año de publicación, contradiciendo el propio manejo `paper.year || 's.f.'` de `gui/js/literature.js` (línea 551).
2. Descarte de metadatos y duplicación de citas sin DOI:
   - `src/thesisforge/api/routes_literature.py` (líneas 184–193 en `add_citation_to_project`): construye el `CitationDTO` omitiendo `url` y `category` provenientes de la petición.
   - `src/thesisforge/rag/service.py` (líneas 522–564, específicamente 559–562 en `add_citation_to_project`): la lógica anti-duplicados solo inspecciona `doi`; cualquier cita sin DOI añadida más de una vez se guarda duplicada.
3. Inconsistencia histórica `< 1800`:
   - `src/thesisforge/models.py` (línea 195): `DocumentChunkDTO.year` restringe `ge=1800`, mientras que `CitationDTO.year` (línea 160) ya admite `ge=1`.

### Reproducción Verificada
- `CitationGuard.verify_claim_evidence` sobre un chunk sin año devolvió `supporting_chunks[0].year == 2024`.
- `DocumentChunkDTO(year=1781, ...)` lanzó `ValidationError` por `ge=1800`.
- Invocar `add_citation_to_project` dos veces seguidas con la misma cita sin DOI persistió 2 entradas duplicadas en el proyecto.
- `POST /api/literature/citations/{project_id}` devolvió `url: None` tras enviar una cita con URL.

### Comportamiento Esperado
1. Permitir `year: int | None` sin inventar `2024` ni el año actual en `CitationGuard`, `RAGService.index_pdf_document` y `gui/js/literature.js`, preservando `(s.f.)` cuando no exista año verificado.
2. Preservar `url` y `category` al construir e insertar `CitationDTO` en `routes_literature.py` (`add_citation_to_project`), y ampliar la deduplicación en `RAGService.add_citation_to_project` mediante clave normalizada de título + primer autor + año cuando `doi` sea `None`.
3. Alinear `DocumentChunkDTO.year` en `src/thesisforge/models.py` con `CitationDTO.year` (`ge=1`).
