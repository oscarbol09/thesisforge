# `[Bug/Methodology]` `AdvisorService.process_step` persiste etiquetas XML `<user_input>` en los campos canónicos del proyecto

**Etiquetas sugeridas:** `bug`, `methodology`, `help wanted`

---

## Descripción del Problema

Para mitigar *prompt injection*, `AdvisorService.quarantine_input()` envuelve la entrada del usuario entre etiquetas `<user_input>...</user_input>`. Sin embargo, `AdvisorService.process_step()` asigna esa cadena ya contaminada (`safe_input`) directamente a los atributos persistentes de `ProjectStateDTO` en múltiples pasos y bloques de fallback. Como resultado, las etiquetas XML de cuarentena se guardan en SQLite, aparecen en la GUI, se exportan al `.docx` y alteran validadores sintácticos.

## Evidencia en Código

- **Definición de cuarentena (`src/thesisforge/advisor/service.py`, líneas 48-52):**
  ```python
  def quarantine_input(text: str) -> str:
      return f"<user_input>{text}</user_input>"
  ```
- **Asignación en `process_step` (`src/thesisforge/advisor/service.py`, línea 231 y siguientes):**
  Se calcula `safe_input = self.quarantine_input(user_input)` al inicio del método y luego se persiste en `ProjectStateDTO`:
  - **SETUP** (líneas 240-241): `project.title = safe_input`
  - **TOPIC_AND_AREA** (líneas 247-248): `project.topic = safe_input`
  - **PROBLEM_STATEMENT** (bloque `except`, líneas 273-274): `project.research_problem = safe_input`
  - **RESEARCH_QUESTION** (líneas 289-290): asigna `safe_input` a `project.research_question`, e inmediatamente en la línea 291 llama a `validate_research_question(...)` sobre el texto que ahora termina en `</user_input>` en lugar de `?`.
  - **OBJECTIVES** (bloque `except`, líneas 325-326): `project.general_objective = safe_input`
  - **HYPOTHESIS** (líneas 351-352): `project.hypothesis = safe_input`

## Impacto

- **Corrupción de datos del proyecto:** Títulos, temas, preguntas de investigación, objetivos e hipótesis almacenados en BD quedan rodeados de `<user_input>...</user_input>`.
- **Falsos fallos de validación:** En `RESEARCH_QUESTION`, validar la cadena envuelta rompe la comprobación de signos de interrogación (`¿...?`), bloqueando el avance del flujo metodológico incluso cuando el usuario ingresó una pregunta válida.

## Criterios de Aceptación (Fix Propuesto)

1. Usar `safe_input` (`<user_input>...</user_input>`) **exclusivamente** dentro de los mensajes/prompts enviados al LLM.
2. Persistir en `ProjectStateDTO` y pasar a validadores (`validate_research_question`, etc.) la entrada original limpia y normalizada (`user_input.strip()` o valor saneado sin etiquetas XML envolventes).
3. Añadir tests unitarios en `tests/unit/` verificando que ningún campo persistido en `ProjectStateDTO` ni entrada de `validate_research_question` contenga `<user_input>` tras ejecutar `process_step`.
