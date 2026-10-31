### Descripción del Problema
En el modelo del Asesor Metodológico (`src/thesisforge/domain/models/advisor.py`), el enum `AdvisorStep` define varios pasos avanzados de la máquina de estados de asesoría de investigación:
- `PARADIGM_AND_APPROACH`
- `OPERATIONALIZATION`
- `CATEGORIES`
- `ETHICS_AND_SAMPLING`

Sin embargo, en el servicio de orquestación metodológica (`src/thesisforge/domain/services/advisor_service.py`), la lógica de transición y los prompts específicos para estos pasos están parcialmente implementados o carecen de ramas explícitas de transición en el flujo guiado de la entrevista.

### Impacto
Si el usuario o el asesor intenta transicionar hacia estos estados, el servicio cae en la rama por defecto o no presenta las preguntas socráticas adecuadas para la operacionalización de variables o consideraciones bioéticas.

### Tareas a Realizar (Ideal para colaboradores / Good First Issue)
1. Revisar `src/thesisforge/domain/models/advisor.py` y `src/thesisforge/domain/services/advisor_service.py`.
2. Completar los manejadores de estado (`_handle_paradigm_and_approach`, `_handle_operationalization`, `_handle_ethics_and_sampling`) con sus respectivas directrices metodológicas para investigación cuantitativa y cualitativa.
3. Asegurar que las transiciones entre estados sean deterministas y válidas según el tipo de enfoque metodológico seleccionado en el proyecto.
4. Agregar pruebas unitarias en `tests/unit/test_advisor_service.py` que verifiquen el ciclo completo de la máquina de estados a través de todos los pasos definidos en `AdvisorStep`.
