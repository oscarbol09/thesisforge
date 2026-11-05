### Descripción del Problema
En `src/thesisforge/api/app.py` y `src/thesisforge/config.py`, la resolución de directorios para servir los archivos estáticos de la aplicación web y los recursos gráficos se realiza de forma relativa al directorio de trabajo actual (`CWD`), en lugar de resolverse respecto a la ubicación del paquete o mediante `importlib.resources`.

Como consecuencia:
1. Si un usuario ejecuta `thesisforge` desde cualquier directorio que no sea la raíz del repositorio clonado (por ejemplo, desde `C:\Users\usuario\tesis` o como comando global instalado con `pip install thesisforge`), la condición `Path("assets").is_dir()` evalúa a `False`.
2. `/assets/` no se monta en FastAPI, `/favicon.ico` devuelve `HTTP 404 Not Found` y `settings.gui_dir` (`Path("gui")`) tampoco se encuentra, lo que impide cargar la interfaz gráfica en el navegador.

### Causa Raíz
En `src/thesisforge/api/app.py`:
- Línea 351: `assets_path = Path("assets")`
- Línea 357: `fav = Path("assets/favicon.ico")`
- Línea 365: `gui_path = Path(settings.gui_dir)` (donde `settings.gui_dir = "gui"`)

Todas estas rutas dependen de `Path.cwd()`.

### Comportamiento Esperado
1. Implementar una función helper de resolución robusta:
   - Intentar ubicar los recursos dentro del paquete instalado (`importlib.resources.files("thesisforge") / "gui"` y `/ "assets"`).
   - Como respaldo de desarrollo, buscar en `Path(__file__).resolve().parent.parent.parent / "gui"`.
   - Como último recurso, consultar `Path.cwd() / "gui"`.
2. Garantizar que ejecutar `python -m thesisforge` o `thesisforge` desde cualquier carpeta arbitraria del sistema monte correctamente la interfaz y sirva los logos y favicon sin errores 404.
