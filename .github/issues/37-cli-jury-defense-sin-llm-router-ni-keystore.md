### Descripción del Problema
Los subcomandos CLI `jury-audit` y `defense-start` ejecutan la auditoría de tribunal y la simulación de defensa oral sin inyectar `LLMRouter` ni leer las claves configuradas en la bóveda (`SecureKeyStoreRepository`) o entorno. En consecuencia, ambos comandos caen siempre en el modo determinista/heurístico de fallback incluso cuando el usuario ya configuró sus claves BYOK.

### Evidencia en Código
- En `src/thesisforge/cli.py`:
  - Subcomando `jury-audit` (**líneas 346–358**): instancia `JuryService(db_manager=db, project_repo=repo, jury_repo=jury_repo)` omitiendo `llm_router=...`.
  - Subcomando `defense-start` (**líneas 447–460**): instancia igualmente `JuryService(db_manager=db, project_repo=repo, jury_repo=jury_repo)` sin `llm_router=...`.
  - (Nota: `_run_draft_init_cli` en la línea 269 sigue el mismo patrón de omisión al instanciar el servicio, aunque el `init` estructural no invoca al LLM).

### Solución Esperada (Good First Issue)
1. Crear un helper reutilizable en `src/thesisforge/cli.py` (o reutilizar la fábrica de settings/keystore) que inicialice `SecureKeyStoreRepository` y `LLMRouter` con las claves BYOK disponibles cuando haya proveedor configurado.
2. Pasar `llm_router` a `JuryService(...)` en `jury-audit` y `defense-start` (manteniendo tolerancia al fallback determinista si no existe ninguna clave o si el usuario usa un flag `--offline`).
3. Añadir pruebas unitarias en `tests/unit/test_cli.py` verificando que `JuryService` recibe una instancia de `LLMRouter` en ambos subcomandos cuando hay configuración/claves disponibles.
