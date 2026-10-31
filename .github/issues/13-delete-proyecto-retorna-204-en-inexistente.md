### Descripción del Problema
En el router de proyectos (`src/thesisforge/presentation/routers/projects.py`), el endpoint para eliminar un proyecto:
```python
DELETE /api/projects/{id}
```
Actualmente ejecuta la operación de borrado en el repositorio y siempre retorna `HTTP 204 No Content`, incluso si el identificador `id` no corresponde a ningún proyecto existente en la base de datos SQLite.

### Comportamiento Esperado (Buenas Prácticas REST)
1. Si el proyecto con el UUID indicado no existe en la base de datos, el endpoint debe responder con:
   ```
   HTTP 404 Not Found
   {"detail": "Project with id '<id>' not found"}
   ```
2. Si el proyecto existe y se elimina con éxito, debe responder con `HTTP 204 No Content`.
3. Actualizar o añadir tests en `tests/unit/test_projects_router.py` validando ambos casos:
   - Eliminación exitosa -> 204.
   - Eliminación de UUID inexistente -> 404.
