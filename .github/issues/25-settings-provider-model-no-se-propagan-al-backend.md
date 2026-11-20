### Descripción del Problema
Cuando un usuario abre el modal de configuración **Bóveda BYOK** en la interfaz web (`gui/index.html` / `gui/js/settings.js`), selecciona un proveedor distinto a OpenRouter (por ejemplo **Google Gemini**, **Groq**, **OpenAI**, **NVIDIA NIM** u **Ollama 100% local**) y un modelo específico:
1. El botón **"Probar Conexión"** funciona correctamente porque `testConnection()` envía explícitamente `provider` y `model` en el cuerpo de `POST /api/settings/test-connection`.
2. Al hacer clic en **"Guardar Cambios"**, la aplicación muestra éxito (`"Proveedor configurado: groq (llama-3.3-70b-versatile)"`).
3. Sin embargo, al ir a **Asesor Metodológico**, **Redacción**, **Auditoría de Jurado** o **Defensa Oral**, el backend **ignora completamente** el proveedor y modelo elegidos y sigue intentando invocar `openrouter` con `anthropic/claude-3.5-sonnet`, fallando si el usuario no tiene una clave de OpenRouter.

### Causa Raíz
1. En `gui/js/settings.js` (líneas 183–210), `saveSettings()` únicamente guarda `default_provider` y `default_model` en el `localStorage` del navegador (`tf_byok_settings`), y solo envía las claves API (`POST /api/settings/keys`) al backend.
2. Ningún módulo del frontend (`gui/js/app.js`, `advisor.js`, `drafting.js`, `jury.js`, `defense.js`) adjunta el proveedor ni el modelo seleccionado en las peticiones REST o WebSockets.
3. En `src/thesisforge/api/routes_settings.py`, no existe un endpoint para persistir ni actualizar `default_provider` / `default_model` en el backend (SQLite / configuración activa).
4. En `src/thesisforge/llm/router.py` (líneas 150–151 y 279–280):
   ```python
   target_provider = provider or self.settings.default_provider
   raw_model = model or self.settings.default_model
   ```
   Al recibir `provider=None` y `model=None` desde los servicios de dominio (`AdvisorService`, `DraftService`, `MultiAgentJuryEngine`, `ThesisDefenseSimulator`), `LLMRouter` siempre usa los valores estáticos de `AppSettings` (`openrouter` y `anthropic/claude-3.5-sonnet`).

### Comportamiento Esperado
1. Persistir las preferencias de `default_provider` y `default_model` en el backend (p. ej. tabla de preferencias en SQLite o endpoint `GET/PUT /api/settings/preferences` protegido con `get_current_owner`), y/o propagarlas por petición desde `Alpine.store('app').api(...)` y los mensajes WebSocket.
2. En `get_llm_router` / `LLMRouter`, resolver el proveedor y modelo activos desde las preferencias persistidas del usuario antes de recurrir a los defaults de `config.yaml` / `AppSettings`.
3. Añadir pruebas de integración que configuren un proveedor alternativo (`ollama` o `gemini`) y verifiquen que `AdvisorService` / `DraftService` enrutan hacia ese proveedor y no hacia `openrouter`.
