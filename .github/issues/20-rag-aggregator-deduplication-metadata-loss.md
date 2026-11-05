### Descripción del Problema / Mejora
En el agregador concurrente de literatura académica (`src/thesisforge/rag/clients/aggregator.py`), el algoritmo de deduplicación descarta artículos arbitrariamente basándose en el orden de llegada de las fuentes concurrentes.

Si un registro de preprint preliminar (por ejemplo, de ArXiv) ingresa primero a la lista de deduplicación sin DOI formal ni datos de publicación revisada por pares, y posteriormente llega el artículo formal publicado en revista desde CrossRef o Semantic Scholar con el mismo título/año/autor:
El agregador descarta el registro de CrossRef por coincidencia de huella (`signature in seen_signatures`), perdiendo metadatos cruciales como el DOI oficial, volumen, número, revista indexada y enlace de acceso abierto.

### Causa Raíz
En `src/thesisforge/rag/clients/aggregator.py` (líneas 117-146):
```python
for paper in papers:
    norm_doi = _normalize_doi(paper.doi)
    if norm_doi:
        if norm_doi in seen_dois:
            continue
        seen_dois.add(norm_doi)

    norm_title = _normalize_title(paper.title)
    first_author = ...
    signature = f"{norm_title[:60]}:{year_str}:{first_author}"

    if signature in seen_signatures and norm_title:
        continue

    seen_signatures.add(signature)
    deduped.append(paper)
```
La lógica es de tipo "el primero que llega gana" (*first-come, first-served*). No evalúa la riqueza del registro (`has_doi`, longitud del abstract, presencia de metadatos de revista).

### Comportamiento Esperado
1. Implementar una estrategia de fusión y enriquecimiento (*merge & enrich*):
   - Si se detecta un duplicado por firma de título/año/autor o por DOI:
     - Si el nuevo registro tiene DOI y el existente no, reemplazar el existente o fusionar los campos vacíos (DOI, venue, url, open_access_pdf, abstract).
     - Si el nuevo registro tiene un resumen (abstract) más extenso o detallado, enriquecer el registro conservado.
2. Añadir tests unitarios en `tests/unit/test_academic_aggregator.py` asegurando que al combinar un resultado sin DOI con un resultado idéntico con DOI de CrossRef, el resultado final conserve siempre el DOI y los metadatos más completos.
