### Descripción del Problema
El endpoint WebSocket de sustentación oral (`/api/defense/ws/{session_id}`) no captura errores de dominio `ThesisForgeError`, por lo que cualquier turno fuera de secuencia o error de sesión colapsa la conexión con `INTERNAL_ERROR`. Adicionalmente, los prompts de defensa y redacción aún interpolan entradas de usuario sin etiquetas `<user_input>` en cuarentena, y la edición manual de secciones (`update_section_content`) deja congelada la versión de la sección.

### Evidencia en Código
1. Colapso de WebSocket ante errores de dominio en `src/thesisforge/api/routes_defense.py`:
   - Líneas 192–197 (`defense_websocket_endpoint`): invoca `await jury_service.submit_defense_answer(...)` sin capturar `ThesisForgeError` (`DefenseSessionError`, `DefenseTurnNotFoundError`). La excepción alcanza el `except Exception` general de la línea 235, enviando `INTERNAL_ERROR` y cerrando el WebSocket.
2. Ausencia de cuarentena XML `<user_input>` en prompts de defensa y redacción:
   - `src/thesisforge/jury/defense.py` (línea 327): `student_answer` se inserta delimitado únicamente con triple comilla `"""..."""`.
   - `src/thesisforge/drafting/service.py` (líneas 265 y 306): `user_feedback` en `revise_section_draft` y `stream_revise_section_draft` se inyecta con `"""..."""` sin `<user_input>`.
   - `src/thesisforge/drafting/memory.py` (línea 152): `user_guidance` en `build_drafting_context` tampoco utiliza cuarentena XML `<user_input>`.
3. Versión estática tras edición manual en `src/thesisforge/drafting/service.py`:
   - Líneas 341–362 (`update_section_content`): guarda el nuevo contenido de la sección sin incrementar `section.version += 1`.

### Reproducción Verificada
- Enviar un mensaje `reply` fuera de orden (`turn_index=2`) al WebSocket `/api/defense/ws/{session_id}` devolvió `{'event': 'error', 'error_code': 'INTERNAL_ERROR', ...}` y cerró la conexión lanzando `WebSocketDisconnect`.
- Tras invocar `DraftService.update_section_content(...)` sobre una sección existente, el campo `version` permaneció en `1`.

### Comportamiento Esperado
1. Capturar explícitamente `ThesisForgeError` en `defense_websocket_endpoint` (`src/thesisforge/api/routes_defense.py`) para responder con un evento `error` estructurado y código de dominio manteniendo viva la sesión WebSocket ante turnos inválidos o fuera de orden.
2. Envolver `student_answer`, `user_feedback` y `user_guidance` con `quarantine_input(...)` (`<user_input>...</user_input>`) antes de ensamblar prompts para el LLM.
3. Incrementar `section.version += 1` dentro de `DraftService.update_section_content` (`src/thesisforge/drafting/service.py`).
4. Añadir pruebas unitarias/WebSocket cubriendo respuestas `reply` fuera de orden, sanitización `<user_input>` e incremento de versión en ediciones manuales.
