### Descripción del Problema
Al indexar documentos o consultar fragmentos vectoriales en ChromaDB mediante `ChromaVectorStore`, si el `project_id` procesado genera un identificador que termina en guión bajo `_`, ChromaDB rechaza la creación o acceso a la colección con una excepción no capturada de tipo `InvalidArgumentError`:

```
chromadb.errors.InvalidArgumentError: Validation error: name: Expected a name containing 3-512 characters from [a-zA-Z0-9._-], starting and ending with a character in [a-zA-Z0-9]. Got: proj_..._
```

Esto bloquea por completo la funcionalidad de literatura RAG, ingesta de PDFs y redacción asistida para el proyecto afectado.

### Causa Raíz
En `src/thesisforge/rag/vectorstore.py` (líneas 318-324):
```python
def _get_collection_name(self, project_id: str) -> str:
    """Sanitize project_id into a valid Chroma collection identifier (3-63 chars alphanumeric)."""
    clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", project_id).strip("_").lower()
    if not clean_id:
        clean_id = "default"
    return f"proj_{clean_id[:50]}"
```

El método invoca `.strip("_")` **antes** de recortar la longitud con `[:50]`. Si el carácter en la posición 49 del texto sanitizado resulta ser un guión bajo (por ejemplo, producto de reemplazar un guión medio `-`, espacio o símbolo especial en un UUID o nombre largo de proyecto), el string resultante `clean_id[:50]` termina en `_`.

Al anteponer `proj_`, la cadena final `f"proj_{clean_id[:50]}"` termina en `_`. La especificación de ChromaDB exige estrictamente que el nombre de la colección comience y termine con un carácter alfanumérico `[a-zA-Z0-9]`. Al terminar en `_`, el validador interno de ChromaDB en Rust/Python lanza inmediatamente `InvalidArgumentError`.

### Comportamiento Esperado
1. En `_get_collection_name`, aplicar el strip de guiones bajos **después** del corte de longitud, asegurando que el identificador termine siempre en un carácter alfanumérico:
   ```python
   truncated = clean_id[:50].rstrip("_")
   if not truncated:
       truncated = "default"
   return f"proj_{truncated}"
   ```
2. Añadir tests unitarios en `tests/unit/test_vectorstore.py` que prueben project IDs con caracteres especiales, guiones en la posición límite de 50 caracteres y verifiquen que la colección de ChromaDB se inicialice sin errores.
