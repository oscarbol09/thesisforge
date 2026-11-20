### Descripción del Problema
La dependencia FastAPI `get_rag_service()` instancia un `RAGService` completamente nuevo en cada petición HTTP, abriendo clientes `httpx.AsyncClient` y conexiones `chromadb.PersistentClient` que nunca se cierran ni se reutilizan. En uso prolongado o bajo concurrencia, esto provoca fuga de descriptores de archivos/sockets, inicializaciones repetidas de ChromaDB en disco y degradación progresiva de latencia.

### Evidencia en Código
1. En `src/thesisforge/api/deps.py` (líneas 69–85):
   - `get_rag_service()` crea un `RAGService` nuevo por cada request (sin `@lru_cache`, sin estado compartido en `app.state` y sin bloque `yield` + `await rag.close()`).
2. En `src/thesisforge/rag/service.py` (líneas 55–72) y `src/thesisforge/rag/clients/base.py` (líneas 57–77):
   - Cada instancia de `RAGService` crea cuatro clientes académicos HTTP (`SemanticScholarClient`, `OpenAlexClient`, `CrossRefClient`, `ArXivClient`), cada uno con su propio `httpx.AsyncClient` persistente.
   - Si `get_rag_service()` no se comparte mediante singleton ni invoca `aclose()`, los pools de conexión quedan huérfanos tras finalizar la petición HTTP.
   - Paralelamente, `ChromaVectorStore` reabre `PersistentClient` desde disco en cada operación de literatura, redacción o jurado.

### Comportamiento Esperado
1. Gestionar el ciclo de vida del `ChromaVectorStore` (y opcionalmente de los clientes HTTP académicos compartidos) a nivel de aplicación en `lifespan` (`src/thesisforge/api/app.py`) o como singleton seguro reutilizado desde `deps.py`, cerrando ordenadamente los `httpx.AsyncClient` en el shutdown de la app (`await client.close()`).
2. Si por diseño se requiere instanciación por petición (por ejemplo, si cambia dinámicamente la clave de Semantic Scholar), usar dependencia generadora `async def get_rag_service(...) -> AsyncIterator[RAGService]` con `try ... yield ... finally: await rag_service.close()` sin duplicar el `ChromaVectorStore` en disco.
3. Añadir una prueba que verifique el cierre limpio de los clientes HTTP o la reutilización del store entre peticiones consecutivas.
