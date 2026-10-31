### Descripción del Problema
Al empaquetar y generar la distribución de ThesisForge mediante `uv build` o `pip install thesisforge`, el paquete wheel omitirá completamente los directorios `gui/` y `assets/`.
Como consecuencia, al instalar `thesisforge` en una máquina limpia desde PyPI o wheel y ejecutar el servidor o la aplicación de escritorio (`thesisforge`), la aplicación falla inmediatamente con `RuntimeError: GUI static directory not found`.

### Causa Raíz
1. En `pyproject.toml` (líneas 67-68):
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["src/thesisforge"]
   ```
   Hatchling únicamente empaqueta lo que está contenido dentro de `src/thesisforge`. Los directorios `gui/` y `assets/` se encuentran en la raíz del repositorio y quedan fuera del wheel.

2. En `src/thesisforge/presentation/app.py`:
   ```python
   base_dir = Path(__file__).resolve().parent.parent.parent.parent
   gui_path = base_dir / "gui"
   ```
   La resolución de rutas se basa en la estructura del árbol de desarrollo del repositorio (`Path(__file__).resolve().parent...`), lo cual asume que `gui` está en la raíz del checkout de git. En un entorno instalado vía wheel (`site-packages`), `gui/` no existe en esa ruta relativa.

### Comportamiento Esperado
1. Los archivos estáticos (`gui/` y `assets/`) deben ser incluidos dentro del paquete instalable de Python (por ejemplo, dentro de `src/thesisforge/gui` y `src/thesisforge/assets` o configurados explícitamente en `tool.hatch.build.targets.wheel.shared-data` o `force-include`).
2. La resolución de rutas en `app.py` y `launcher.py` debe utilizar `importlib.resources.files("thesisforge") / "gui"` con fallback ordenado al directorio de desarrollo (`Path.cwd() / "gui"` o `Path(__file__)`).
3. Al ejecutar `uv build` y posteriormente `pip install dist/*.whl`, `thesisforge --cli` y `thesisforge` (modo servidor o GUI) deben levantar sin requerir el código fuente del repositorio clonado.

### Pasos para Reproducir
1. Ejecutar `uv build`.
2. Inspeccionar el contenido del wheel: `unzip -l dist/thesisforge-*.whl`.
3. Constatar que no contiene ningún archivo de `gui/` ni `assets/`.
4. Instalar en un entorno virtual aislado: `pip install dist/thesisforge-*.whl`.
5. Ejecutar `thesisforge`:
   ```
   RuntimeError: GUI static directory not found: ...
   ```
