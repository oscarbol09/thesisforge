### Descripción del Problema
Los validadores metodológicos, la matriz de consistencia, el flujo del asesor y el auditor de reglas del jurado comprueban únicamente `ResearchApproach.CUANTITATIVO` o `ResearchApproach.CUALITATIVO`, omitiendo por completo el enfoque `ResearchApproach.MIXTO`. En consecuencia, una tesis de enfoque mixto se aprueba sin indicadores operacionalizados, sin validar compatibilidad estadística de escalas ni categorías cualitativas, y sin exigir hipótesis cuando aplica.

### Evidencia en Código
1. En `src/thesisforge/advisor/validators.py`:
   - `validate_operationalization` (línea 298) solo se ejecuta cuando el enfoque es `CUANTITATIVO`, excluyendo `MIXTO`.
   - `validate_qualitative_categories` (línea 316) solo se ejecuta cuando el enfoque es `CUALITATIVO`, excluyendo `MIXTO`.
   - `audit_project` (líneas 387–456) hereda ambas omisiones en la auditoría integral.
2. En `src/thesisforge/advisor/consistency_matrix.py`:
   - Línea 160 (`build_matrix`): condiciona con `if approach == ResearchApproach.CUANTITATIVO and op_vars:`, saltándose la llamada a `check_scale_compatibility` cuando el proyecto usa `ResearchApproach.MIXTO`.
3. En `src/thesisforge/advisor/service.py` y `src/thesisforge/jury/evaluator.py`:
   - `src/thesisforge/advisor/service.py` (línea 100 en `_determine_current_step`) y `src/thesisforge/jury/evaluator.py` (línea 154 en `_run_rule_based_audit`) filtran solo por `CUANTITATIVO`, ignorando el componente cuantitativo de los proyectos `MIXTO`.

### Reproducción Verificada
- Al ejecutar `MethodologyValidator.audit_project` sobre un proyecto `ResearchApproach.MIXTO` con `operationalized_variables` cuyos `indicators` estaban vacíos (`indicators=[]`), la validación de operacionalización no reportó el defecto.
- Al ejecutar `ConsistencyMatrixEngine.build_matrix` en un proyecto `MIXTO` con prueba estadística `"pearson"` asignada a una variable con escala `"nominal"`, la matriz informó `True Compatible`.

### Comportamiento Esperado
1. Incluir `ResearchApproach.MIXTO` junto con `CUANTITATIVO` y `CUALITATIVO` en `validate_operationalization` y `validate_qualitative_categories` (`src/thesisforge/advisor/validators.py`), exigiendo la consistencia de ambos componentes (o de los campos presentes según diseño mixto).
2. Evaluar `check_scale_compatibility` también para `ResearchApproach.MIXTO` en `ConsistencyMatrixEngine.build_matrix` (`src/thesisforge/advisor/consistency_matrix.py`).
3. Considerar `ResearchApproach.MIXTO` en `_determine_current_step` (`src/thesisforge/advisor/service.py`) y en `_run_rule_based_audit` (`src/thesisforge/jury/evaluator.py`).
4. Añadir pruebas unitarias específicas para proyectos `ResearchApproach.MIXTO` cubriendo indicadores vacíos y escalas nominales con pruebas paramétricas.
