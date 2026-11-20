### Descripción del Problema
El simulador de **Defensa Oral** desde la interfaz web (`gui/js/defense.js`) es completamente inoperable: cada vez que el tesista redacta su réplica y hace clic en **"Emitir Réplica al Jurado"**, el servidor rechaza la petición con `HTTP 422 Unprocessable Entity`.

### Causa Raíz
1. En `src/thesisforge/api/routes_defense.py` (líneas 26–35), el contrato de entrada `SubmitReplyRequest` declara `extra="forbid"` y exige obligatoriamente `turn_index`:
   ```python
   class SubmitReplyRequest(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

       turn_index: int = Field(ge=0, description="Índice del turno de defensa a responder")
       student_answer: str = Field(min_length=1, max_length=5000, ...)
   ```
2. Sin embargo, en `gui/js/defense.js` (líneas 52–63), `submitAnswer()` omite `turn_index` al construir el JSON:
   ```javascript
   const updated = await Alpine.store('app').api(`/api/defense/sessions/${this.activeSession.id}/reply`, {
     method: 'POST',
     body: JSON.stringify({
       student_answer: this.studentAnswer.trim()
     })
   });
   ```
   Pydantic rechaza el payload por falta del campo requerido `turn_index`.
3. Adicionalmente, en `gui/js/defense.js` (línea 39), `startDefense()` envía `?turns=${this.totalTurns}` como parámetro de query string al endpoint `POST /api/defense/projects/{project_id}/start`, parámetro que `routes_defense.py:43-52` no acepta ni procesa (solo recibe `StartDefenseRequest(force_new=...)`), impidiendo además forzar una nueva sesión al finalizar una defensa previa si quedara alguna en curso.

### Comportamiento Esperado
1. Enviar `turn_index: this.activeSession.current_turn_index` dentro del payload JSON en `defense.js:submitAnswer()`.
2. Alinear `startDefense()` en `defense.js` para enviar el cuerpo JSON `{ force_new: Boolean(this.activeSession) }` acorde a `StartDefenseRequest` en `routes_defense.py` (y, si se desea configurar turnos, soportarlo explícitamente en el backend o eliminar el parámetro huérfano `?turns=`).
3. Nota: Esta corrección inmediata desbloquea la defensa oral REST mientras se aborda la migración reactiva por WebSocket descrita en #34.
