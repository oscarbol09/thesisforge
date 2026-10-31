### Descripción del Problema
El empaquetado de ejecutables de escritorio autónomos para Windows mediante PyInstaller (definido en `.github/workflows/desktop-packaging.yml`) y la ejecución local de `src/thesisforge/desktop/launcher.py` presentan dos fallos críticos que impiden generar o ejecutar el binario `.exe`:

1. **Separador de ruta incorrecto en spec/workflow de Windows:** En Windows, el argumento `--add-data` de PyInstaller requiere punto y coma (`;`) como separador entre la ruta de origen y destino (`gui;gui`), no dos puntos (`:`). La sintaxis `:` causa un error de análisis de argumentos en PyInstaller en Windows (`Unable to parse add-data`).
2. **`launcher.py` no es ejecutable como script o punto de entrada directo:** El archivo `src/thesisforge/desktop/launcher.py` define la función `launch_desktop()`, pero carece del bloque de entrada `if __name__ == "__main__": launch_desktop()`. Si PyInstaller toma `launcher.py` como script raíz, el ejecutable arranca y finaliza inmediatamente en 0ms sin abrir ninguna ventana de PyWebView.

### Causa Raíz
1. En `.github/workflows/desktop-packaging.yml` (o el script de build PyInstaller):
   ```bash
   pyinstaller --noconfirm --onedir --windowed --add-data "gui:gui" --add-data "assets:assets" ... src/thesisforge/desktop/launcher.py
   ```
   En sistemas Windows (donde las rutas pueden contener letras de unidad como `C:\`), PyInstaller reserva `:` y exige `;`.
2. En `src/thesisforge/desktop/launcher.py`:
   No hay `if __name__ == "__main__": launch_desktop()`.
   Además, cuando se empaqueta con PyInstaller (onefile/onedir), `sys._MEIPASS` no está considerado al resolver la ruta hacia `gui/` y `assets/`, lo cual provoca `FileNotFoundError` al iniciar el servidor FastAPI en el subproceso del ejecutable.

### Comportamiento Esperado
1. En `launcher.py`, implementar:
   - Detección de `sys._MEIPASS` para entornos congelados por PyInstaller:
     ```python
     if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
         base_dir = Path(sys._MEIPASS)
     ```
   - Punto de entrada canónico:
     ```python
     if __name__ == "__main__":
         launch_desktop()
     ```
2. En el archivo `.spec` de PyInstaller o en el script de empaquetado multiplataforma, abstraer el separador de `add-data` según el sistema operativo (`os.pathsep` o `;` en Windows y `:` en POSIX).
3. El ejecutable compilado en Windows (`thesisforge.exe`) debe iniciar la ventana nativa de PyWebView y cargar la interfaz gráfica sin cerrarse de inmediato.
