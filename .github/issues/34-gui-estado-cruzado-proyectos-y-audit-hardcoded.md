### Descripción del Problema
Cambiar de proyecto activo desde el Dashboard o el selector lateral produce contaminación de estado entre proyectos en la SPA, y el Paso 8 del Asesor Metodológico muestra una auditoría siempre en verde con datos estáticos codificados en duro (*hardcoded*) en lugar de leer el estado real del backend.

### Causa Raíz
1. **Contaminación de estado entre proyectos en vistas AlpineJS:**
   - Mientras `gui/js/literature.js` (líneas 51–57) observa `$watch('$store.app.activeProject', ...)` para recargar/limpiar el estado al cambiar de proyecto, los otros cuatro módulos omiten dicho observador:
     - `gui/js/advisor.js` (líneas 79–82)
     - `gui/js/drafting.js` (líneas 23–25)
     - `gui/js/jury.js` (líneas 13–15)
     - `gui/js/defense.js` (líneas 14–16)
   - Al cambiar de proyecto activo, los formularios (`formData`), secciones (`sections`), dictámenes (`latestReport`) y sesiones de defensa (`activeSession`) del proyecto anterior permanecen visibles en memoria.
2. **Auditoría de congruencia hardcoded en Paso 8 (`gui/js/advisor.js`):**
   - En `gui/js/advisor.js` (líneas 929–946), el paso `consistency_audit` renderiza 4 insignias verdes fijas (`Alineado Bloom`, `Congruente`, `Contrastable`, `Verificable`) ignorando por completo el resultado de `statusData?.audit` y el endpoint `GET /api/advisor/{project_id}/consistency-matrix`.
   - Además, la línea 582 imprime el literal sin renderizar `$OG \equiv PG$` directamente como texto en el DOM.

### Comportamiento Esperado
1. Registrar `$watch('$store.app.activeProject', ...)` en `advisor.js`, `drafting.js`, `jury.js` y `defense.js` para resetear el estado transitorio local y recargar los datos del nuevo proyecto (evitando fugas entre tesis distintas).
2. Conectar el Paso 8 de `gui/js/advisor.js` con el estado real (`statusData?.audit` / `GET /api/advisor/{project_id}/consistency-matrix`) para reflejar advertencias, inconsistencias y recomendaciones reales en lugar de insignias estáticas en verde.
3. Reemplazar el literal `$OG \equiv PG$` en `gui/js/advisor.js:582` por notación legible en HTML/Unicode (`OG ≡ PG` o descripción clara).
