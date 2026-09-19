# Seguridad y AppSec en ThesisForge

ThesisForge incorpora mecanismos de defensa en profundidad para proteger al investigador contra riesgos de seguridad comunes en aplicaciones asistidas por IA.

---

## SSRF Guard (Server-Side Request Forgery)

Cuando el sistema descarga artículos científicos de URLs proporcionadas por APIs o el usuario, `SSRFGuard` ejecuta una validación de dos pasos antes de abrir cualquier socket de red:

```mermaid
graph TD
    URL["URL a Descargar (Paper / PDF)"] --> DNS["Resolución DNS"]
    DNS --> CHECK{"¿La IP resuelta pertenece a rangos privados o de loopback?"}
    CHECK -->|Sí: 127.0.0.1, 10.0.0.0/8, 192.168.0.0/16, etc.| BLOCK["Bloqueo Inmediato (SecurityError)"]
    CHECK -->|No: IP Pública Válida| FETCH["Petición Httpx Segura"]
```

---

## Key Vault Local

- Las claves de API introducidas por el usuario (OpenRouter, OpenAI, Gemini) se cifran en reposo con **Fernet**.
- Cada registro en la base de datos almacena el vector cifrado junto con su tag de autenticación HMAC.
- Ningún endpoint de la API devuelve las claves en texto plano tras su registro.

---

## Sanitización de Logs (CWE-117)

- `StructuredLogger` procesa todas las cadenas de texto del usuario eliminando secuencias de retorno de carro (`\r`) y salto de línea (`\n`).
- Evita ataques de inyección de logs donde un atacante falsifica entradas de auditoría en los archivos de registro.

---

## Defensa contra Formula Injection (CSV / XLSX / DOCX)

- Si un investigador procesa tablas de datos donde las celdas comienzan con caracteres de fórmula (`=`, `+`, `-`, `@`), ThesisForge prefija automáticamente la celda con un apóstrofe (`'`).
- Esto evita que Microsoft Excel o LibreOffice Calc ejecuten fórmulas maliciosas cuando el usuario abre el archivo exportado.
