### Descripción del Problema
> **Nota de alcance:** La resolución del conflicto de versión optimista y el manejo de fragmentos RAG durante la importación de bundles `.thesisforge` están cubiertos en `#39`. Este issue se centra específicamente en la vulnerabilidad CWE-409 (Zip Bomb por confianza en cabeceras ZIP falsificables) y en el bloqueo síncrono del event loop durante la exportación/importación.

Al importar un paquete `.thesisforge`, `ProjectBundleService` valida el límite de 15 MB leyendo `info.file_size` (metadato declarado por el propio ZIP y trivialmente falsificable) antes de invocar `zf.read(...)` en memoria sin cota real de lectura. Además, tanto `ExportService` como `ProjectBundleService` ejecutan operaciones pesadas de `python-docx`, `zipfile` e I/O síncrono de disco directamente en el event loop de FastAPI.

### Evidencia en Código
1. En `src/thesisforge/export/bundle.py`:
   - Líneas 139–147 (`import_bundle`): comprueba `info.file_size > 15 * 1024 * 1024` usando el tamaño declarado en el directorio central del archivo ZIP.
   - Líneas 155, 164 y 241: llama directamente a `zf.read(...)` para cargar entradas completas en RAM sin lectura acotada por flujo ni control acumulado total descomprimido en streaming.
2. Bloqueo síncrono en corrutinas `async def`:
   - `src/thesisforge/export/service.py` (líneas 51, 77 y 106) ejecuta la compilación DOCX (`python-docx`) y lectura de bytes síncrona dentro del event loop.
   - `src/thesisforge/export/bundle.py` (líneas 77, 111 y 282) ejecuta compresión/descompresión `zipfile` y lectura/escritura síncrona (`read_bytes`/`write_bytes`) directamente dentro de funciones `async def`.

### Reproducción Verificada
- Se construyó un `.zip` de `25,722` bytes en el que tanto la cabecera local como el directorio central declaraban falsamente `info.file_size == 10`.
- Bajo medición con `tracemalloc`, `zf.read('project.json')` superó el chequeo inicial de `info.file_size` y alcanzó un pico de `54.43 MB` asignados en RAM antes de que `zipfile` lanzara `BadZipFile` al llegar al final del flujo (EOF). Un archivo manipulado con mayor ratio o múltiples entradas amplifica la presión de memoria antes de cualquier rechazo.

### Comportamiento Esperado
1. Reemplazar `zf.read(...)` en `ProjectBundleService` por lectura incremental en chunks mediante `zf.open(info)` verificando estrictamente en cada bloque tanto el máximo por entrada como un presupuesto acumulado total de bytes descomprimidos (lanzando error de dominio antes de asignar decenas de MB en memoria).
2. Descargar el trabajo CPU-intensivo y de I/O síncrona de disco (`python-docx`, `zipfile`, `read_bytes`/`write_bytes`) mediante `asyncio.to_thread(...)` en `ExportService` y `ProjectBundleService` para no bloquear el event loop de FastAPI.
3. Añadir un test automatizado que verifique el rechazo acotado ante cabeceras ZIP falsificadas (Zip Bomb CWE-409).
