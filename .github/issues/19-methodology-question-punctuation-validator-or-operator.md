### Descripción del Problema
En el validador metodológico de preguntas de investigación (`src/thesisforge/advisor/validators.py`), la regla que comprueba que la pregunta esté formulada con signos de interrogación permite preguntas con signos incompletos debido a un error lógico de operador booleano (`or` en lugar de `and`).

### Causa Raíz
En `src/thesisforge/advisor/validators.py` (líneas 125-129):
```python
if not (cleaned.startswith("¿") or cleaned.endswith("?")):
    issues.append(
        "La pregunta de investigación debe estar formulada con signos de interrogación formales (¿...?)."
    )
```

Bajo la lógica actual:
- Si la pregunta inicia con `¿` pero no tiene el signo de cierre `?` (ej. `"¿Cómo influye la inteligencia artificial en la deserción escolar"`), `cleaned.startswith("¿")` es `True`, por lo que la condición `not (True or False) == not (True) == False`. **No se reporta ningún error.**
- Si la pregunta omite el signo de apertura `¿` (típico anglicismo ortográfico: `"Cómo influye la inteligencia artificial en la deserción escolar?"`), `cleaned.endswith("?")` es `True`. **Tampoco se reporta error.**

En la lengua española y en la redacción formal de tesis académicas, es obligatorio el uso de ambos signos de interrogación (`¿` al inicio y `?` al final).

### Solución Esperada (Good First Issue)
1. Corregir la condición lógica en `validators.py`:
   ```python
   if not (cleaned.startswith("¿") and cleaned.endswith("?")):
       issues.append(
           "La pregunta de investigación debe estar formulada con signos de interrogación formales al inicio y al final (¿...?)."
       )
   ```
2. Actualizar o agregar tests en `tests/unit/test_advisor_validators.py` verificando que:
   - Preguntas sin `¿` inicial fallen.
   - Preguntas sin `?` final fallen.
   - Preguntas con `¿...?` pasen sin advertencias.
