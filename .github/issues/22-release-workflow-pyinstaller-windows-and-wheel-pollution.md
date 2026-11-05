### Descripción del Problema
En el flujo automatizado de CI/CD para releases de producción (`.github/workflows/release.yml`), se presentan dos fallos de compilación y empaquetado:

1. **Separador de ruta incompatible en PyInstaller para Windows:**
   En la línea 94:
   ```yaml
   pyinstaller --noconfirm --onedir --windowed --name "${{ matrix.artifact_name }}" \
     --collect-all chromadb --collect-all litellm --collect-all fitz --collect-all pymupdf \
     --add-data "gui:gui" src/thesisforge/desktop/launcher.py
   ```
   La matriz ejecuta este paso en `windows-latest`. En Windows, PyInstaller no acepta `:` como separador para `--add-data` debido a la ambigüedad con las letras de unidad (`C:\`), requiriendo obligatoriamente `;` (`"gui;gui"`). La compilación de Windows falla al parsear el comando.

2. **Contaminación de paquetes de escritorio con artefactos wheel de Python:**
   En el runner `ubuntu-latest`, el paso previo (línea 89) ejecuta:
   ```yaml
   uv run python -m build
   ```
   Esto deposita el `.whl` y `.tar.gz` de la distribución en la carpeta `dist/`.
   Posteriormente, el paso de compresión de binarios de escritorio (líneas 103-109) ejecuta:
   ```bash
   cd dist
   tar -czvf "../${{ matrix.artifact_name }}.tar.gz" *
   cd ..
   ```
   El comodín `*` empaqueta indiscriminadamente los wheels de PyPI dentro del archivo comprimido de la aplicación de escritorio de Linux, inflando el tamaño del archivo y mezclando canales de distribución.

### Comportamiento Esperado
1. Parametrizar el separador de `--add-data` según el sistema operativo (`:` en Linux/macOS, `;` en Windows) o utilizar un archivo `thesisforge.spec` con detección dinámica de `os.pathsep`.
2. Aislar los directorios de salida: destinar los wheels a `dist/packages/` y los ejecutables de PyInstaller a `dist/desktop/`, de modo que el comando `tar` comprima únicamente el contenido del directorio del ejecutable de escritorio.
