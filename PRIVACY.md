# Política de Privacidad — ThesisForge

**Última actualización:** 26 de septiembre de 2026  
**Versión de la Política:** 1.0.0  
**Ámbito de Aplicación:** Aplicación de Escritorio ThesisForge, Servidor Local FastAPI, CLI y Portal de Documentación.

---

## 1. Responsable del Tratamiento y Arquitectura Local-First

ThesisForge es un proyecto de software libre (*Open Source*) desarrollado y mantenido por Oscar Madera ([@oscarbol09](https://github.com/oscarbol09)). 

A diferencia de las plataformas SaaS tradicionales en la nube, ThesisForge está diseñado bajo el principio fundamental de **Privacidad por Diseño (*Privacy by Design*) y Arquitectura Local-First**:

1. **Sin Base de Datos Central:** ThesisForge no aloja una base de datos centralizada que recopile tus proyectos, borradores, datos personales o credenciales.
2. **Almacenamiento Local Exclusivo:** Toda tu información de investigación (títulos, fichas metodológicas, literatura indexada, borradores de capítulos y evaluaciones de jurado) se almacena exclusivamente en tu propia máquina mediante una base de datos SQLite local (`thesisforge.db`) y una base de datos vectorial ChromaDB local (`data/chroma/`).
3. **Control Total:** El usuario ostenta la posesión física y el control criptográfico absoluto sobre sus archivos locales.

---

## 2. Datos Procesados y Finalidades del Tratamiento

| Categoría de Datos | Finalidad Específica | Base Legal (RGPD Art. 6) | Destino / Ubicación |
| :--- | :--- | :--- | :--- |
| **Credenciales de API (BYOK)** | Autenticar llamadas directas de inferencia ante los proveedores configurados por el usuario (OpenRouter, Google Gemini, OpenAI, Groq, NVIDIA NIM). | Ejecución del contrato de uso (Art. 6.1.b) y Consentimiento explícito (Art. 6.1.a). | Cifradas en reposo con Fernet (AES-128-CBC + HMAC-SHA256) en la base de datos local `thesisforge.db`. |
| **Contenido Académico y Borradores** | Estructuración metodológica, formulación de preguntas, redacción modular y simulación de jurados. | Ejecución del servicio solicitado por el usuario (Art. 6.1.b). | Base de datos SQLite local y transferidos únicamente al proveedor de LLM seleccionado durante la solicitud de generación. |
| **Consultas Bibliográficas y DOI** | Recuperación de artículos y verificación de citas indexadas (RAG). | Interés legítimo en la verificación académica (Art. 6.1.f). | Transmitidas a APIs académicas públicas (Semantic Scholar, CrossRef, ArXiv). |
| **Preferencias de Interfaz (Tema, Proyecto Activo)** | Recordar el modo visual (claro/oscuro) y el proyecto seleccionado. | Interés técnico legítimo (Art. 6.1.f). | `localStorage` del navegador local del usuario. |

---

## 3. Transferencias Internacionales de Datos y Proveedores de IA

Cuando configuras claves de API comerciales y solicitas generaciones de texto, los fragmentos relevantes de tu tesis son transmitidos directamente desde tu equipo hacia los servidores del proveedor que tú hayas elegido:

- **OpenRouter:** Sujeto a los [Términos y Privacidad de OpenRouter](https://openrouter.ai/privacy).
- **Google Gemini:** Sujeto a los [Términos de Google AI](https://policies.google.com/privacy).
- **OpenAI:** Sujeto a la [Política de Privacidad de OpenAI](https://openai.com/privacy).
- **Groq Inc:** Sujeto a la [Política de Privacidad de Groq](https://groq.com/privacy-policy/).
- **NVIDIA NIM:** Sujeto a la [Política de Privacidad de NVIDIA](https://www.nvidia.com/en-us/about-nvidia/privacy-policy/).

> [!TIP]
> **Modo 100% Desconectado / Privacidad Total (Zero Cloud Transfer):**  
> Si tu investigación involucra datos altamente confidenciales, patentes o secretos industriales, puedes utilizar **Ollama** con modelos locales (`llama3`, `mistral`, `deepseek`). En este modo, **ningún dato sale de tu computadora** hacia internet.

---

## 4. Derechos del Interesado (RGPD, LOPDGDD, CCPA/CPRA, Ley 1581)

De conformidad con el Reglamento General de Protección de Datos (RGPD UE 2016/679), la Ley Orgánica 3/2018 (LOPDGDD España), la Ley 1581 de 2012 (Colombia) y normativas homólogas internacionales, dispones de los siguientes derechos:

1. **Derecho de Acceso y Portabilidad:** Puedes exportar la totalidad de tus proyectos en formato autocontenido `.thesisforge` o `.docx` en cualquier momento mediante la CLI o la interfaz gráfica.
2. **Derecho de Supresión (Derecho al Olvido):** Al ser un sistema *Local-First*, puedes eliminar permanentemente cualquier proyecto desde la interfaz de usuario, o eliminar la base de datos completa suprimiendo el archivo local `thesisforge.db`.
3. **Derecho de Rectificación:** Todos los campos, citas y borradores son editables en tiempo real por el usuario.

---

## 5. Seguridad de la Información y Bóveda Criptográfica

ThesisForge implementa salvaguardas técnicas robustas:
- **Cifrado Fernet Autenticado:** Las claves de API se cifran localmente en reposo mediante Fernet (AES-128-CBC + HMAC-SHA256) con clave maestra aislada de 256 bits y permisos de archivo restrictivos (0o600 en POSIX).
- **SSRF Guard:** Bloqueo estricto de peticiones hacia redes privadas (RFC 1918) y metadatos de computación en la nube.
- **Sanitización de Logs (CWE-117):** Ofuscación automática de tokens y eliminación de caracteres de control en registros.
- **Cero Telemetría Invasiva:** Las telemetrías externas de LiteLLM y ChromaDB están formalmente desactivadas en el código fuente.


---

## 6. Contacto y Consultas sobre Privacidad

Para consultas, dudas o reportes sobre la gestión de privacidad en este software, puedes comunicarte con el mantenedor a través de:
- **GitHub Issues / Discussions:** [https://github.com/oscarbol09/thesisforge](https://github.com/oscarbol09/thesisforge)
- **Reporte de Seguridad:** Revisar [SECURITY.md](SECURITY.md) para incidentes de seguridad.
