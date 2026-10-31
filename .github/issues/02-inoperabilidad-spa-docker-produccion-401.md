---
title: "[BUG]: El Frontend SPA queda inaccesible con HTTP 401 en Docker/Producción y las descargas fallan por falta de autenticación"
labels: ["bug", "critical", "auth", "docker", "frontend", "security"]
assignees: []
---

## Descripción del Error
Cuando ThesisForge se ejecuta en entorno de producción o mediante `docker compose up` (`THESISFORGE_ENVIRONMENT=production`):
1. Todas las peticiones API devuelven `401 Unauthorized` (`MISSING_TOKEN`), pero no existe ninguna interfaz, modal o campo en la configuración para que el usuario ingrese el token de instancia generado por el servidor.
2. Los botones de descarga de Word (`.docx`) y BibTeX (`.bib`) en `gui/js/export.js` y `gui/js/literature.js` ejecutan llamadas directas a `window.fetch()` sin adjuntar el header `Authorization: Bearer <token>`, fallando inmediatamente con error 401.
3. El WebSocket de redacción en `gui/js/drafting.js` llama a `new WebSocket(wsUrl)` sin pasar el token en el subprotocolo `Sec-WebSocket-Protocol`, siendo rechazado por el backend con código WS 1008.

## Componente Afectado
`Seguridad, Autenticación y SPA (gui/js/app.js, gui/js/export.js, gui/js/drafting.js)`

## Pasos para Reproducir
1. Ejecutar el proyecto con Docker: `docker compose up`.
2. Abrir `http://localhost:8000` en el navegador.
3. Se observan notificaciones de error "Se requiere autenticación" sin posibilidad de autenticarse desde la interfaz gráfica.

## Causa Raíz
- `gui/index.html` y `gui/js/settings.js` no proveen interfaz para configurar `tf_instance_token`.
- `gui/js/export.js:32` y `gui/js/export.js:80` usan `fetch()` nativo crudo en lugar de pasar headers de autenticación.
- `gui/js/drafting.js:149` inicializa `new WebSocket(wsUrl)` sin subprotocolo negociado.

## Solución Propuesta
1. Agregar en el modal de configuración (`gui/index.html` y `gui/js/settings.js`) una sección para visualizar e ingresar el Token de Instancia, guardándolo en `localStorage.setItem('tf_instance_token', token)`.
2. En `export.js` y `literature.js`, adjuntar los headers de autenticación antes de invocar `fetch()`:
   ```javascript
   const token = localStorage.getItem('tf_instance_token');
   const headers = { 'Content-Type': 'application/json' };
   if (token) headers['Authorization'] = `Bearer ${token}`;
   ```
3. En `drafting.js`, enviar el subprotocolo en la inicialización:
   ```javascript
   const token = localStorage.getItem('tf_instance_token');
   const subprotocols = token ? ['bearer', token] : [];
   const ws = new WebSocket(wsUrl, subprotocols);
   ```
