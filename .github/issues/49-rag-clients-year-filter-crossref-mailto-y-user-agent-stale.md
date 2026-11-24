### Descripción del Problema
> **Nota de alcance:** La inyección de la API key de `SemanticScholarClient` desde `AppSettings` / Bóveda BYOK está cubierta en `#56` (PR `#68`). Este issue recoge exclusivamente los defectos restantes en `AcademicSearchAggregator`, `RAGServiceResources` y los clientes `CrossRefClient` / `ArxivClient`.

El buscador académico combinado (`AcademicSearchAggregator`) ignora los filtros `year_start` y `year_end` al consultar ArXiv y CrossRef, las factorías de dependencias `RAGServiceResources` / `get_rag_service` no propagan `settings.crossref_mailto` hacia CrossRef/OpenAlex, y los clientes HTTP de CrossRef y ArXiv envían un `User-Agent` desactualizado (`ThesisForge/0.1.0`) en lugar de la versión real del paquete (`0.6.0`).

### Evidencia en Código
1. Filtro temporal ignorado en `src/thesisforge/rag/clients/aggregator.py` (líneas 78–86):
   - Al despachar búsquedas en paralelo, `AcademicSearchAggregator` reenvía `year_start` y `year_end` únicamente a `semantic_scholar` y `openalex`, omitiéndolos al invocar a `arxiv` y `crossref`.
2. Configuración `crossref_mailto` no propagada:
   - `src/thesisforge/config.py` (línea 127) define `crossref_mailto` en `AppSettings`.
   - `src/thesisforge/rag/resources.py` (líneas 37–38) y `src/thesisforge/api/deps.py` (línea 91) instancian `CrossRefClient` y `OpenAlexClient` sin pasar `mailto=settings.crossref_mailto` (perdiendo acceso al *polite pool* de las APIs académicas).
3. `User-Agent` desactualizado en clientes académicos:
   - `src/thesisforge/rag/clients/crossref.py` (línea 27) y `src/thesisforge/rag/clients/arxiv.py` (línea 34) fijan el literal `"ThesisForge/0.1.0"` en lugar de usar `__version__` (`0.6.0`).

### Reproducción Verificada
- Inspección directa en Runtime confirmó `CrossRefClient().user_agent` y `ArxivClient().user_agent` devolviendo `"ThesisForge/0.1.0"` frente a la versión `0.6.0` del paquete.

### Comportamiento Esperado
1. Soportar y propagar los parámetros `year_start` y `year_end` en `CrossRefClient` (p. ej. filtro `from-pub-date` / `until-pub-date`) y `ArxivClient` (o filtrado consistente en rango de fechas) desde `AcademicSearchAggregator`.
2. Inyectar `settings.crossref_mailto` al construir `CrossRefClient` y `OpenAlexClient` dentro de `RAGServiceResources` (`src/thesisforge/rag/resources.py`) y el respaldo de `get_rag_service` (`src/thesisforge/api/deps.py`).
3. Reemplazar los strings literales `"ThesisForge/0.1.0"` por `f"ThesisForge/{__version__}"` en `crossref.py` y `arxiv.py`.
4. Añadir pruebas unitarias verificando parámetros de fecha en CrossRef/ArXiv, inyección de `crossref_mailto` y cabecera `User-Agent`.
