# Política de Cookies y Almacenamiento Local — ThesisForge

**Última actualización:** 26 de septiembre de 2026  
**Versión:** 1.0.0

---

## 1. ¿Utiliza ThesisForge Cookies Tradicionales?

ThesisForge opera principalmente como una aplicación de una sola página (SPA) y herramienta de escritorio local. **ThesisForge no utiliza cookies HTTP de rastreo publicitario ni cookies de terceros para monitorear tu comportamiento de navegación.**

El sistema utiliza la tecnología estándar de almacenamiento local web (**`localStorage`**) proporcionada por tu navegador con fines estrictamente técnicos y funcionales.

---

## 2. Inventario de Almacenamiento Local (`localStorage`)

A continuación se detallan todas las claves almacenadas en tu navegador y su finalidad técnica exclusiva:

| Clave de Almacenamiento | Tipo | Finalidad Técnica | Duración / Persistencia | Carácter |
| :--- | :---: | :--- | :---: | :---: |
| `tf_theme` | Técnico / Preferencia | Almacena la preferencia de tema visual (`light` o `dark`) seleccionada por el usuario. | Persistente (hasta borrado manual) | Estrictamente Necesaria |
| `tf_active_project_id` | Técnico / Sesión | Recuerda el identificador del proyecto activo para restaurar la vista al recargar la página. | Persistente (hasta cambio o borrado) | Estrictamente Necesaria |
| `tf_cookie_consent` | Técnico / Cumplimiento | Registra que el usuario ha sido informado sobre el uso de almacenamiento local técnico. | Persistente (hasta borrado) | Estrictamente Necesaria |
| `tf_instance_token` | Técnico / Seguridad | Almacena el token de autorización de instancia para comunicar con el backend local FastAPI. | Persistente por sesión local | Estrictamente Necesaria |

---

## 3. Ausencia de Cookies de Rastreo y Analíticas de Terceros

- ❌ **No Google Analytics / Google Tag Manager.**
- ❌ **No Meta Pixel / Facebook Tracking.**
- ❌ **No Cookies de perfilado comercial o publicidad comportamental.**
- ❌ **No Scripts de grabación de pantalla de terceros (Hotjar, CrazyEgg).**

---

## 4. Cómo Gestionar o Eliminar los Datos Almacenados

Puedes inspeccionar, vaciar o eliminar los datos de almacenamiento local en cualquier momento a través de la configuración de tu navegador web:

- **Google Chrome / Chromium / Brave / Edge:** Presiona `F12` o `Ctrl+Shift+I` $\rightarrow$ Pestaña **Application** (Aplicación) $\rightarrow$ **Local Storage** $\rightarrow$ Clic secundario en el origen $\rightarrow$ **Clear**.
- **Mozilla Firefox:** Presiona `F12` $\rightarrow$ Pestaña **Almacenamiento** $\rightarrow$ **Almacenamiento local** $\rightarrow$ Eliminar todo.
- **Safari:** Preferencias $\rightarrow$ Privacidad $\rightarrow$ Administrar datos del sitio web $\rightarrow$ Eliminar.
