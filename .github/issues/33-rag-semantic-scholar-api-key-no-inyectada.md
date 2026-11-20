### Descripción del Problema
Aunque la aplicación permite configurar la clave API de **Semantic Scholar** tanto en variables de entorno (`THESISFORGE_SEMANTIC_SCHOLAR_API_KEY` / `AppSettings.semantic_scholar_api_key`) como desde la **Bóveda BYOK** en la interfaz web (`gui/index.html` y `gui/js/settings.js`), el cliente `SemanticScholarClient` siempre realiza las búsquedas en modo anónimo sin API key, quedando expuesto a límites estrictos de tasa pública (HTTP 429).

### Causa Raíz
1. En `src/thesisforge/rag/service.py` (línea 55):
   ```python
   self.semantic_scholar = SemanticScholarClient(cache=self.cache)
   ```
   `RAGService.__init__` instancia `SemanticScholarClient` dejando `api_key=None` (sin parámetro o sin recibirla desde el contenedor DI).
2. En `src/thesisforge/api/deps.py` (líneas 69–85):
   `get_rag_service()` instancia `RAGService` sin consultar `settings.semantic_scholar_api_key` ni `SecureKeyStoreRepository.get_key("semantic_scholar")`, a pesar de que `src/thesisforge/config.py` (línea 126), `gui/index.html` (líneas 565–588) y `gui/js/settings.js` (línea 22) contemplan y almacenan esa clave explícitamente.

### Solución Esperada (Good First Issue)
1. Permitir pasar `semantic_scholar_api_key: str | None = None` en `RAGService.__init__` (y reenviarlo a `SemanticScholarClient(cache=self.cache, api_key=semantic_scholar_api_key)`).
2. En `get_rag_service()` (`src/thesisforge/api/deps.py`), resolver la clave priorizando `SecureKeyStoreRepository.get_key("semantic_scholar")` con fallback a `settings.semantic_scholar_api_key` (y aplicar el mismo patrón si algún comando CLI construye `RAGService`).
3. Añadir una prueba unitaria verificando que `SemanticScholarClient` incluye la cabecera `x-api-key` cuando la clave está presente en la bóveda o en `AppSettings`.
