# Política de Seguridad

El equipo de **ThesisForge** se toma muy en serio la seguridad de la información. Valoramos el apoyo de la comunidad de seguridad y de código abierto para mantener esta herramienta segura para investigadores y estudiantes.

---

## Versiones Soportadas

Ofrecemos actualizaciones y parches de seguridad para las siguientes versiones:

| Versión | Estado de Soporte |
| :--- | :---: |
| 0.1.x | Soportada |
| < 0.1.0 | Sin soporte |

---

## Reportar una Vulnerabilidad

> [!IMPORTANT]
> **Por favor, NO reportes vulnerabilidades de seguridad a través de problemas (issues) públicos en GitHub.**

Si descubres una vulnerabilidad en ThesisForge, repórtala de manera privada mediante:

1. **GitHub Security Advisory:** Dirígete a la pestaña de [Security Advisories](https://github.com/oscarbol09/thesisforge/security/advisories/new) de este repositorio y haz clic en **"Report a vulnerability"**.
2. **Contacto Directo:** Alternativamente, contacta directamente al mantenedor a través de su perfil de GitHub ([@oscarbol09](https://github.com/oscarbol09)).

### Qué incluir en tu reporte
- Tipo de incidente (por ejemplo: bypass de SSRF, exposición de credenciales locales, inyección de fórmulas, ejecución remota o salto de validaciones).
- Rutas de los archivos fuente afectados.
- Pasos detallados para reproducir el problema (código de prueba de concepto o payload utilizado).
- Propuesta de mitigación o parche si la tienes identificada.

---

## Garantías y Arquitectura de Seguridad

ThesisForge implementa defensas en profundidad:

1. **SSRF Guard (`thesisforge.core.security.assert_safe_academic_url`):**
   - Resuelve el DNS de toda URL externa antes de emitir peticiones HTTP.
   - Bloquea estrictamente direcciones loopback (`127.0.0.1`, `::1`), subredes privadas RFC 1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), direcciones link-local (`169.254.169.254`) e interfaces reservadas.
2. **Bóveda Local de Claves (`thesisforge.repository.keystore_repository.SecureKeyStoreRepository`):**
   - Cifrado simétrico Fernet de 256 bits para todas las claves de API BYOK guardadas en SQLite local.
   - Las claves se descifran en memoria solo al ejecutar llamadas al router LLM y nunca se devuelven en texto plano en la API.
3. **Defensa contra Log Injection (CWE-117):**
   - El logger estructurado JSON sanitiza retornos de carro (`\r`, `\n`) de las entradas del usuario y enmascara tokens sensibles.
4. **Sanitización contra Inyección de Fórmulas:**
   - La capa de exportación prefija con un apóstrofe (`'`) cualquier celda de tabla que inicie con `=`, `+`, `-`, `@` o tabulaciones para proteger la apertura en Microsoft Word o Excel.

