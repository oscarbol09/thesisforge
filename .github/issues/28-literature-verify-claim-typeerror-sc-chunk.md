# `[Bug/Frontend]` TypeError en verificación de claims (`literature.js`) por desajuste entre `sc.chunk.*` y `CitationDTO`

**Etiquetas sugeridas:** `bug`, `rag`, `frontend`, `good first issue`, `help wanted`

---

## Descripción del Problema

Al usar la funcionalidad de verificación de afirmaciones (*Claim Grounding*) en la pestaña de Literatura, la vista de resultados en AlpineJS intenta acceder a propiedades anidadas bajo `sc.chunk.*` cuando el backend devuelve una lista plana de objetos `CitationDTO` directamente en `supporting_chunks`. Esto provoca errores en tiempo de ejecución (`TypeError`) y rompe el renderizado de la evidencia que respalda la afirmación.

## Evidencia en Código

- **Frontend (`gui/js/literature.js`, líneas 696-702):**
  El bloque de plantilla itera sobre `claimVerdict.supporting_chunks` asumiendo que cada elemento `sc` contiene una subpropiedad `chunk`:
  ```html
  <template x-for="sc in claimVerdict.supporting_chunks" :key="sc.chunk.id">
    ...
    x-text="sc.chunk.title || 'Documento'"
    x-text="'Pág. ' + (sc.chunk.page_number || 1)"
    x-text="'\"' + sc.chunk.text + '\"'"
  ```
- **Backend DTO (`src/thesisforge/models.py`, línea 214):**
  `EvidenceVerdictDTO` define:
  ```python
  supporting_chunks: list[CitationDTO] = Field(default_factory=list)
  ```
- **Guardia de Citas (`src/thesisforge/rag/citation_guard.py`, líneas 146-160):**
  El verificador construye elementos `CitationDTO` planos con atributos de primer nivel (`id`, `title`, `page_number`, `evidence_text`, `abstract`, `chunk_id`, `relevance_score`), sin objeto intermedio `.chunk` ni atributo `.text`.

## Impacto

- **Error de consola en runtime:** Al verificar cualquier claim con fragmentos de soporte, AlpineJS lanza `TypeError: Cannot read properties of undefined (reading 'id')` / `'title'` / `'text'`.
- **UI rota:** El panel de *Claim Grounding* queda vacío o parcial justo en la funcionalidad clave para auditar citas contra los PDFs indexados.

## Criterios de Aceptación (Fix Propuesto)

1. Actualizar `gui/js/literature.js` (líneas 696-702) para enlazar directamente contra la estructura real de `CitationDTO`:
   - `:key="sc.id || sc.chunk_id || $index"`
   - `sc.title || 'Documento'`
   - `'Pág. ' + (sc.page_number || 1)`
   - `sc.evidence_text || sc.abstract || ''` (en lugar de `sc.chunk.text`).
2. Añadir una prueba de contrato o test unitario/E2E ligero que valide el shape JSON devuelto por el endpoint de verificación de claims frente a las propiedades esperadas por la plantilla.
