### Descripción del Problema
El subsistema de observabilidad (`StructuredJsonFormatter`) descarta todos los stack traces emitidos con `logger.exception(...)`, falla con `TypeError` al registrar objetos `Path` en `extra` y no enmascara claves API de proveedores BYOK como Groq (`gsk_...`) o NVIDIA NIM (`nvapi-...`). Adicionalmente, el endpoint `POST /api/settings/test-connection` devuelve `str(exc)` sin sanitizar en su respuesta HTTP JSON, pudiendo filtrar claves presentes en URLs de error (por ejemplo `?key=AIza...` de Gemini).

### Evidencia en Código
1. En `src/thesisforge/core/logging.py`:
   - Líneas 75–76 (`StructuredJsonFormatter.format`): la condición `if record.exc_info and record.exc_text:` comprueba únicamente `record.exc_text` sin llamar antes a `self.formatException(record.exc_info)`. En las llamadas estándar a `logger.exception(...)`, `record.exc_text` es `None` hasta invocar el formateo de excepción, por lo que `"exception"` nunca aparece en el JSON emitido. Esto silencia los tracebacks registrados en `src/thesisforge/llm/router.py` (líneas 185 y 337), `src/thesisforge/api/routes_defense.py` (línea 236) y `src/thesisforge/api/routes_drafting.py` (línea 243).
   - Línea 112: `json.dumps(log_payload, ensure_ascii=False)` carece de `default=str`, por lo que pasar un `Path` en `extra` rompe el formateador.
   - Líneas 12–19 (`SECRET_PATTERNS`): cubre prefijos `sk-`, `ghp_`, `gho_`, `AIza`, `Bearer ` y `keyvault:`, pero omite prefijos reales del catálogo BYOK como Groq (`gsk_...`) y NVIDIA NIM (`nvapi-...`).
2. En `src/thesisforge/api/routes_settings.py`:
   - Líneas 175–178 (`test_llm_connection`): el bloque `except Exception as exc:` construye `TestConnectionResponse(status="error", message=f"Error al conectar con '{clean_model}': {str(exc)}", ...)` enviando `str(exc)` directo por HTTP sin aplicar `sanitize_log_message(...)`.

### Reproducción Verificada
- Registrar una excepción con `logger.exception(...)` a través de `StructuredJsonFormatter.format()` produjo JSON sin campo `"exception"`.
- Incluir `Path("data/test.db")` en `extra` lanzó `TypeError: Object of type WindowsPath is not JSON serializable`.
- `sanitize_log_message(...)` dejó intactos tokens de formato `gsk_...` y `nvapi-...`.
- Al simular una excepción de proveedor en `POST /api/settings/test-connection`, el cuerpo JSON HTTP `200` expuso literalmente `https://generativelanguage.googleapis.com/v1?key=AIzaSyDummyKey1234567890123456789012345` dentro de `message`.

### Comportamiento Esperado
1. En `StructuredJsonFormatter.format()`, formatear `record.exc_text = self.formatException(record.exc_info)` cuando `record.exc_info` esté presente y `not record.exc_text`, e incluir `default=str` en `json.dumps(...)` (y sanitizar strings dentro de `extra` si aplica).
2. Ampliar `SECRET_PATTERNS` para redactar claves `gsk_...` (Groq) y `nvapi-...` (NVIDIA NIM), además de otros prefijos del catálogo si corresponde.
3. Sanitizar `str(exc)` con `sanitize_log_message` (o devolver un mensaje seguro sin URLs/credenciales crudas) en `POST /api/settings/test-connection` (`src/thesisforge/api/routes_settings.py`).
4. Añadir pruebas unitarias para tracebacks en JSON, serialización de `Path`, nuevos patrones en `SECRET_PATTERNS` y no exposición de `?key=` en `test-connection`.
