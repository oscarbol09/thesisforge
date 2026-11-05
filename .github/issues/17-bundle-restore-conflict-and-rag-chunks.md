### Descripción del Problema
El sistema de archivado y copias de seguridad de proyectos (`.thesisforge`), gestionado por `ProjectBundleService` en `src/thesisforge/export/bundle.py`, presenta dos fallos críticos en flujos de restauración y portabilidad:

1. **Conflicto de Concurrencia Optimista al Restaurar un Respaldo Existente:**
   Si un usuario descarga un respaldo `.thesisforge` de su proyecto (con `version: 1`), continúa trabajando en la aplicación (incrementando la versión interna a `version: 4` en SQLite) y posteriormente intenta restaurar el respaldo anterior, la operación falla con `ExportError` debido a un `ProjectVersionConflictError` no controlado.
   
   En `bundle.py` (líneas 251-256):
   ```python
   try:
       await self.repo.get_project(project.id)
       await self.repo.update_project(project)
   except ProjectNotFoundError:
       await self.repo.create_project(project)
   ```
   `update_project` valida que la versión enviada coincida con la de la base de datos. Como la versión del archivo es menor que la actual de la base de datos, SQLite rechaza la actualización (`cursor.rowcount == 0`), abortando la restauración.

2. **Pérdida Completa de Fragmentos RAG y Estado Vectorial:**
   El paquete `.thesisforge` únicamente empaqueta `manifest.json`, `project.json`, `sections/*.md` y `citations.json`. **No exporta** los registros de `document_chunks` ni `document_index_status`.
   Al restaurar un paquete en una máquina limpia, el proyecto contiene los IDs de documentos en `project.indexed_documents`, pero no existen vectores en ChromaDB ni texto en SQLite. Cualquier consulta de RAG, redacción o verificación de afirmaciones falla o devuelve resultados vacíos.

### Comportamiento Esperado
1. En `import_bundle_bytes`, permitir un parámetro o modo de restauración forzada/sobrescritura (`overwrite=True`) que actualice el proyecto ignorando el candado de versión previa o sincronice `project.version = existing.version + 1`.
2. Incluir en el archivo `.thesisforge` la serialización de `document_chunks.json` y `document_index_status.json`, y reindexar automáticamente los vectores en ChromaDB tras la importación utilizando `rebuild_chroma_from_sqlite()`.
3. Tests en `tests/unit/test_project_bundle.py` que comprueben:
   - Restaurar una versión anterior sobre un proyecto con versión superior.
   - Preservación y reconstrucción de vectores tras exportar e importar el paquete.
