# `[Security/Frontend]` Riesgo de XSS almacenado/reflejado en vistas SPA con `x-html="render()"` sin sanitización

**Etiquetas sugeridas:** `bug`, `security`, `frontend`, `help wanted`

---

## Descripción del Problema

La SPA principal renderiza la mayoría de sus vistas inyectando cadenas HTML construidas dinámicamente mediante interpolación `${...}` en directivas `x-html="render()"`. Aunque `app.js` provee `escapeHtml(str)` y `sanitize(rawHtml)` (respaldado por `DOMPurify`), prácticamente todos los componentes de vista omiten escapar o sanitizar datos provenientes de metadatos PDF externos, APIs académicas, salidas de LLM o campos del proyecto.

## Evidencia en Código

- **Contenedor principal (`gui/index.html`, líneas 270-315):**
  Todas las vistas principales (`dashboard`, `advisor`, `literature`, `drafting`, `export`, `jury`, `defense`, `settings`) montan `<div x-html="render()"></div>`.
- **Helpers disponibles (`gui/js/app.js`, líneas 205-221):**
  Existen `escapeHtml(str)` y `sanitize(rawHtml)`, pero en el inventario actual únicamente `gui/js/dashboard.js` (líneas 167-169) aplica `app.escapeHtml(...)`.
- **Interpolaciones sin escapar identificadas:**
  - `gui/js/jury.js` (líneas 145, 152, 159, 169-170, 175, 181, 187, 206, 208-211): interpola `report.summary_dictamen`, `eval.feedback`, `strengths`, `flaws`, `iss.title`, `iss.description` e `iss.recommendation`.
  - `gui/js/defense.js` (líneas 189-193, 205, 217, 258): interpola `t.juror_name`, `t.focus_area`, `t.question`, `t.student_answer`, `t.juror_feedback` y `session.final_remarks`.
  - `gui/js/drafting.js` (líneas 304, 326): interpola `sec.title` y `this.selectedSection.title`.
  - `gui/js/literature.js` (líneas 613-642): interpola `c.title`, `c.authors`, `c.apa_formatted`, `c.journal`, `c.doi`, además de construir un handler inline en la línea 625 con `@click="deleteCitation(${JSON.stringify(c).replace(/"/g, '&quot;')})"`.
  - `gui/js/advisor.js` (líneas 394, 452-453): interpola `project.title`, `stepLabels` y `stepDescriptions`.

## Impacto

- **XSS almacenado / reflejado:** Un documento PDF malicioso, metadatos manipulados desde fuentes externas (`CrossRef`, `Semantic Scholar`, `OpenAlex`, `arXiv`), un proyecto `.json` importado o una respuesta LLM con `<img onerror=...>` / `<svg onload=...>` pueden ejecutar JavaScript arbitrario en la sesión autenticada de la SPA o en el WebView de escritorio.
- En el handler `@click` de `literature.js:625`, comillas simples, backticks o entidades malformadas en el objeto serializado pueden romper o inyectar expresiones AlpineJS.

## Criterios de Aceptación (Fix Propuesto)

1. Aplicar `app.escapeHtml(...)` de forma sistemática a todas las variables de texto plano interpoladas dentro de `render()` en `jury.js`, `defense.js`, `drafting.js`, `literature.js` y `advisor.js` (o pasar el bloque resultante por `app.sanitize(...)` sin romper directivas Alpine necesarias).
2. Reemplazar el patrón `@click="deleteCitation(${JSON.stringify(c)...})"` en `gui/js/literature.js:625` por un atributo de datos seguro o pasando únicamente `c.id` escapado / búsqueda por ID en memoria.
3. Añadir pruebas automatizadas que verifiquen que payloads con `<script>` o `<img src=x onerror=alert(1)>` en títulos, citas o feedback del jurado se renderizan como texto literal inocuo.
