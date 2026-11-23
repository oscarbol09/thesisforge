### Descripción del Problema
La SPA presenta cuatro desajustes de estado y contrato entre interfaz y backend:
1. Limpiar el año en el formulario de exportación DOCX envía `year: ""` y provoca un error HTTP `422`.
2. Las opciones `"Calibri (11 pt)"` y `"Arial (11 pt)"` mantienen `font_size_pt: 12` en lugar de `11`.
3. Al reabrir la vista de Ajustes, `syncModelSelection` sobrescribe un modelo personalizado que no esté listado en `MODEL_CATALOG`.
4. En el Paso 6/7 del asesor (`advisor.js`), se crean propiedades estructurales sin controles de edición en la UI y borrar instrumentos en pantalla deja valores obsoletos persistidos en el proyecto.

### Evidencia en Código
1. En `gui/js/export.js`:
   - Línea 204 (`x-model="options.year"` sobre `<input type="number">`): cuando el usuario vacía el campo, Alpine conserva `""` como string en lugar de `null`. En el backend, `ExportOptionsDTO.model_validate({'year': ''})` falla con `ValidationError` (`422`).
   - Líneas 15 y 213–217: las variantes etiquetadas como `"Calibri (11 pt)"` y `"Arial (11 pt)"` conservan `font_size_pt: 12` en el payload de exportación.
2. En `gui/js/settings.js`:
   - Líneas 90–111 (`syncModelSelection`, especialmente líneas 98–104): si el modelo guardado por el usuario no figura en el catálogo predefinido `MODEL_CATALOG`, lo reemplaza automáticamente por `getRecommendedModelForProvider()` al inicializar la pantalla.
3. En `gui/js/advisor.js`:
   - Líneas 194–217, 236–245 y 703–806: inicializa objetos de operacionalización/categorización con campos como `dimensions`, `indicators`, `subcategories`, `coding_criteria` y `saturation_indicator` sin inputs vinculados en el DOM para editarlos, y `syncInstrumentsFromPairs` (línea 242) omite sincronizar cuando la lista de pares queda vacía, conservando `instruments` previos en el estado del proyecto.

### Comportamiento Esperado
1. Convertir `options.year` vacío (`""` / `NaN`) a `null` antes de enviar la petición en `gui/js/export.js` (y opcionalmente usar `x-model.number`), además de aplicar `font_size_pt: 11` cuando se seleccione `"Calibri (11 pt)"` o `"Arial (11 pt)"`.
2. Preservar en `gui/js/settings.js` (`syncModelSelection`) cualquier identificador de modelo personalizado ya guardado por el usuario sin sobrescribirlo por `getRecommendedModelForProvider()` al reabrir la vista.
3. Exponer controles UI en `gui/js/advisor.js` para `dimensions`/`indicators` y `subcategories`/`coding_criteria`/`saturation_indicator` (o eliminar campos huérfanos no editables si no aplican) y asegurar que `syncInstrumentsFromPairs` actualice `instruments` a `[]` cuando el usuario borre todos los pares.
