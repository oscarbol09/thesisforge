## Descripción del Cambio

Por favor incluye un resumen claro del cambio, su motivación y qué problema resuelve. Menciona las decisiones de diseño relevantes.

Corrige o se relaciona con # (número de issue)

---

## Tipo de Cambio

- [ ] Corrección de error (bug fix no disruptivo)
- [ ] Nueva funcionalidad (feature)
- [ ] Actualización de documentación (guías, referencias, tutoriales)
- [ ] Optimización de rendimiento
- [ ] Mejora de seguridad (SSRF, sanitización, cifrado)
- [ ] Mejora en suite de pruebas (nuevas pruebas unitarias, de integración o de propiedades)
- [ ] Cambio con impacto disruptivo (breaking change)

---

## Lista de Verificación de Calidad

Por favor asegúrate de que se cumplan los siguientes puntos antes de solicitar una revisión:

- [ ] **Pruebas Automatizadas:** Los cambios incluyen pruebas y la suite completa pasa con cobertura:
  ```bash
  uv run pytest tests/ -v --cov=thesisforge
  ```
- [ ] **Chequeo Estricto de Tipos:** Mypy pasa sin errores:
  ```bash
  uv run mypy
  ```
- [ ] **Linter y Formato:** El código cumple con las reglas de Ruff:
  ```bash
  uv run ruff check src/ tests/
  uv run ruff format --check src/ tests/
  ```
- [ ] **Auditoría de Seguridad:** Bandit no reporta incidentes de severidad media o alta:
  ```bash
  uv run bandit -r src/ -ll
  ```
- [ ] **I/O Asíncrono No Bloqueante:** No existen llamadas bloqueantes (`requests.get`, `time.sleep`, llamadas síncronas a disco) en funciones `async def`.
- [ ] **Marcas de Tiempo UTC:** Todas las instancias de fecha y hora utilizan `timezone.utc`.
- [ ] **Documentación:** Se actualizaron los docstrings y archivos de documentación relevantes (si aplica).

