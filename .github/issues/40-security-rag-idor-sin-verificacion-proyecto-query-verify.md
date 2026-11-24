### Descripción del Problema
Los endpoints de literatura RAG `POST /api/literature/query-context` y `POST /api/literature/verify-claim`, junto con los métodos internos de `RAGService` (`query_relevant_chunks`, `verify_claim` y `rebuild_chroma_from_sqlite`), no comprueban que el `project_id` solicitado exista ni que pertenezca al propietario autenticado (`owner_id`). A diferencia del resto de operaciones de `RAGService`, cualquier peticionario que envíe un `project_id` inexistente o ajeno recibe `HTTP 200` en lugar de `404` y rompe el aislamiento entre proyectos.

### Evidencia en Código
1. En `src/thesisforge/rag/service.py`:
   - `rebuild_chroma_from_sqlite` (líneas 164–193), `query_relevant_chunks` (líneas 503–520) y `verify_claim` (líneas 566–581) omiten la verificación `await self.repo.get_project(project_id)`.
   - En contraste, los métodos vecinos del mismo servicio (`get_document_index_statuses` en línea 145, `index_pdf_document` en línea 274, `delete_document` en línea 473, `add_citation_to_project` en línea 534 y `build_prisma_flow` en línea 592) sí llaman a `await self.repo.get_project(project_id)` para validar existencia y `owner_id` (lanzando `ProjectNotFoundError`).
2. En `src/thesisforge/api/routes_literature.py`:
   - `query_relevant_context` (líneas 136–149) y `verify_claim_grounding` (líneas 152–162) pasan `request.project_id` directamente al servicio sin validar propiedad del proyecto.

### Reproducción Verificada
- `POST /api/literature/query-context` y `POST /api/literature/verify-claim` con un `project_id` inexistente respondieron `HTTP 200` (`[]` y `is_supported: False` respectivamente) en lugar de `HTTP 404`.
- Invocar `RAGService.query_relevant_chunks("proj_secret_a", ...)` desde una instancia con un `owner_id` distinto (`owner_b` frente a `owner_a`, propietario real de `"proj_secret_a"`) ejecutó la consulta sobre Chroma/RAG sin lanzar `ProjectNotFoundError`.

### Comportamiento Esperado
1. Validar `await self.repo.get_project(project_id)` al inicio de `query_relevant_chunks`, `verify_claim` y `rebuild_chroma_from_sqlite` en `src/thesisforge/rag/service.py`.
2. Asegurar que ambos endpoints (`POST /api/literature/query-context` y `POST /api/literature/verify-claim`) devuelvan `HTTP 404` ante un `project_id` inexistente o perteneciente a otro `owner_id`.
3. Añadir tests unitarios y de integración API cubriendo `404` en proyectos inexistentes y aislamiento cruzado entre `owner_a` y `owner_b`.
