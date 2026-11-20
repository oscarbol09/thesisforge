# `[Bug/Methodology]` `AdvisorService.assist_drafting` envía `{academic_level}` literal al LLM y descarta `scope_limitations`

**Etiquetas sugeridas:** `bug`, `methodology`, `good first issue`, `help wanted`

---

## Descripción del Problema

El método `AdvisorService.assist_drafting()` presenta dos defectos concretos en la asistencia metodológica de Fase 1:
1. Pasa `ADVISOR_SYSTEM_PROMPT` sin formatear su placeholder `{academic_level}` en las tres ramas de componente asistido.
2. Para `component == "scope_limitations"`, apunta a un `target_section_id = "sec_1_5"` cuando `project.sections` todavía está vacío y nunca actualiza `project.scope_limitations`, por lo que activar `auto_apply=True` descarta el texto generado.

## Evidencia en Código

- **Placeholder sin formatear:**
  - `src/thesisforge/llm/prompts.py` (línea 4): `ADVISOR_SYSTEM_PROMPT` requiere el parámetro `{academic_level}`.
  - `src/thesisforge/advisor/service.py` (líneas 549-550, 570-571 y 600-601): las llamadas al `llm_router` pasan `ADVISOR_SYSTEM_PROMPT` en crudo sin `.format(academic_level=...)` (a diferencia de `process_step` en la línea 232, que sí lo formatea).
- **Pérdida de `scope_limitations` (`src/thesisforge/advisor/service.py`, líneas 587-619):**
  - En la rama `component == "scope_limitations"`, establece `target_section_id = "sec_1_5"` pero omite asignar `project.scope_limitations = result.get("draft_text", "")`.
  - Como en la Fase 1 de diseño metodológico `project.sections` aún no se ha inicializado con las secciones de Fase 2, `auto_apply=True` no encuentra `"sec_1_5"` ni persiste `project.scope_limitations`.

## Impacto

- **Degradación de prompts:** El modelo recibe literalmente `{academic_level}` en las instrucciones de sistema en lugar de `Pregrado`, `Maestría` o `Doctorado`.
- **Pérdida silenciosa de contenido:** El borrador de alcances y limitaciones generado con `auto_apply=True` nunca queda guardado en el estado del proyecto (`project.scope_limitations`).

## Criterios de Aceptación (Fix Propuesto)

1. Formatear `ADVISOR_SYSTEM_PROMPT.format(academic_level=...)` (con el mismo criterio o helper reutilizado de `process_step`) en las tres ramas de `assist_drafting()`.
2. En la rama `component == "scope_limitations"`, asignar `project.scope_limitations = result.get("draft_text", "")` cuando `auto_apply=True` (manteniendo además la actualización de la sección `sec_1_5` si ya existiera en `project.sections`).
3. Añadir tests unitarios que verifiquen que `system_prompt` enviado al router no contiene `{academic_level}` y que `project.scope_limitations` persiste tras `assist_drafting(..., component="scope_limitations", auto_apply=True)`.
