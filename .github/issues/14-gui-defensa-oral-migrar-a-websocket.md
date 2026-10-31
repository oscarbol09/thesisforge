### Descripción del Problema
El simulador de defensa oral y jurado multi-agente (`src/thesisforge/presentation/routers/defense.py`) expone dos vías de comunicación con el backend:
1. Un endpoint síncrono REST: `POST /api/defense/{session_id}/reply`
2. Un canal WebSocket bidireccional y reactivo: `WebSocket /api/defense/ws/{session_id}`

En la interfaz de usuario (`gui/pages/defense.html` y `gui/js/defense.js`), las intervenciones del jurado y las respuestas del tesista se implementaron utilizando peticiones HTTP síncronas (`fetch POST /reply`).

### Limitaciones del Enfoque Actual
- **Latencia y falta de streaming:** Cada respuesta del jurado debe esperar a que el LLM complete la generación entera antes de mostrarse en la pantalla (a menudo de 5 a 15 segundos), sin efecto de tipeo en vivo ni retroalimentación visual token a token.
- **Inconsistencia de estado:** Si la conexión HTTP se interrumpe durante una deliberación prolongada, el estado de la sesión puede quedar desfasado.
- **WebSocket ya implementado en el backend:** El backend ya cuenta con la infraestructura completa de WebSockets para deliberación en tiempo real.

### Comportamiento Esperado
1. Refactorizar `gui/js/defense.js` para conectarse a `WebSocket /api/defense/ws/${sessionId}` (enviando el token en el protocolo `Sec-WebSocket-Protocol` según los estándares de seguridad de ThesisForge).
2. Renderizar los turnos de interrogatorio de los jurados (Metodólogo, Especialista Temático, Crítico Escéptico y Presidente) de forma reactiva y con efecto streaming de tokens.
3. Mostrar indicadores de "Jurado deliberando..." mientras se reciben los eventos en el socket.
