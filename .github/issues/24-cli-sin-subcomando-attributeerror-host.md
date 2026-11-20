### Descripción del Problema
Ejecutar el binario `thesisforge` sin subcomandos (el caso de uso predeterminado esperado para iniciar el servidor web/API según `cli.py:807`) falla inmediatamente con una excepción no controlada `AttributeError`:

```text
Traceback (most recent call last):
  File ".../thesisforge/cli.py", line 808, in main
    host = args.host or settings.host
           ^^^^^^^^^
AttributeError: 'Namespace' object has no attribute 'host'
```

### Causa Raíz
En `src/thesisforge/cli.py`:
- Los argumentos `--host`, `--port` y `--reload` se registran únicamente en el subparser `run_parser` (líneas 548–565) y en `gui_parser` (`--host`, `--port`), NO en el parser raíz `parser`.
- Sin embargo, la rama de ejecución por defecto (líneas 807–814) combina `args.command == "run" or args.command is None` y accede directamente a `args.host` y `args.port`:
  ```python
  elif args.command == "run" or args.command is None:
      host = args.host or settings.host
      port = args.port or settings.port
      reload = (
          bool(args.reload)
          if (hasattr(args, "reload") and args.reload)
          else (settings.environment == "development")
      )
  ```
- Cuando `args.command is None`, el `argparse.Namespace` devuelto no posee los atributos `host` ni `port`.
- Adicionalmente, activar `reload = (settings.environment == "development")` de forma implícita cuando se ejecuta `thesisforge` fuera del directorio fuente de desarrollo (o desde un paquete instalado en `site-packages`) puede hacer que Uvicorn observe un directorio incorrecto con reloaders en segundo plano.

### Comportamiento Esperado
1. Utilizar `getattr(args, "host", None) or settings.host` y `getattr(args, "port", None) or settings.port` para evitar el `AttributeError` cuando `args.command is None`.
2. Activar `reload=True` únicamente cuando el usuario pase explícitamente `--reload` o cuando exista un árbol fuente de desarrollo local (sin romper ejecuciones globales desde `site-packages`).
3. Añadir una prueba unitaria en `tests/unit/test_cli.py` invocando `main()` con `sys.argv = ["thesisforge"]` (sin subcomando) verificando que invoca `uvicorn.run(...)` sin errores.

### Reproducción Verificada
```bash
uv run python -c "import sys; sys.argv=['thesisforge']; from thesisforge.cli import main; main()"
```
Produce `AttributeError: 'Namespace' object has no attribute 'host'`.
