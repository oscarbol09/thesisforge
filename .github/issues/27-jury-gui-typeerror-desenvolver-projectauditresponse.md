### Descripción del Problema
En la pestaña **5. Auditoría de Jurado** (`gui/js/jury.js`), al hacer clic en **"Auditar con Tribunal Doctoral"**, la petición al backend tiene éxito, pero el frontend colapsa inmediatamente en consola con un error de JavaScript (`TypeError`), dejando la interfaz rota sin mostrar el dictamen emitido.

### Causa Raíz
Existe una discrepancia entre el esquema de respuesta de `POST /api/jury/projects/{project_id}/audit` y el del histórico `GET .../evaluations/latest`:

1. En `src/thesisforge/api/routes_jury.py` (líneas 16–42):
   ```python
   class ProjectAuditResponse(BaseModel):
       model_config = ConfigDict(extra="forbid")
       success: bool = True
       project_id: str
       report: JuryEvaluationReportDTO
   ```
   El endpoint `POST /audit` devuelve un sobre `ProjectAuditResponse` donde el dictamen está anidado bajo la propiedad `.report`. (Por el contrario, `GET /evaluations/latest` retorna directamente `JuryEvaluationReportDTO`).

2. En `gui/js/jury.js` (líneas 38–43):
   ```javascript
   const report = await Alpine.store('app').api(`/api/jury/projects/${project.id}/audit`, {
     method: 'POST'
   });
   this.latestReport = report;
   Alpine.store('app').toast('success', 'Auditoría Completada', `El tribunal emitió el dictamen: ${this.getVerdictLabel(report.verdict)}.`);
   ```
   Como `jury.js` no desenvuelve `response.report`:
   - `report.verdict` es `undefined`.
   - En `render()` (línea 152), `report.overall_score.toFixed(1)` lanza `TypeError: Cannot read properties of undefined (reading 'toFixed')`, rompiendo el renderizado de Alpine.js.

### Solución Esperada (Good First Issue)
1. En `gui/js/jury.js`, extraer el objeto real del dictamen:
   ```javascript
   const data = await Alpine.store('app').api(`/api/jury/projects/${project.id}/audit`, {
     method: 'POST'
   });
   const report = data?.report || data;
   this.latestReport = report;
   ```
2. Añadir protecciones defensivas opcionales en `render()` (p. ej. `Number(report.overall_score ?? 0).toFixed(1)`).
3. Verificar manualmente o mediante prueba E2E que tras ejecutar la auditoría se muestren la calificación global, las 4 tarjetas de jurado y la lista de hallazgos.
