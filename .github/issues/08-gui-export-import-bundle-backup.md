### Descripción del Problema
ThesisForge implementa en el backend un sistema hermético de archivado y copias de seguridad de proyectos (`.thesisforge`), empaquetando la base de datos del proyecto, metadatos, estado metodológico, referencias bibliográficas y embeddings en un tarball firmado con HMAC-SHA256 para evitar alteraciones accidentales o manipulación maliciosa (`bundle.py`).

Los endpoints backend para esta funcionalidad están implementados:
- `GET /api/projects/{id}/bundle` (exportación y descarga del bundle comprimido)
- `POST /api/projects/bundle` (importación y restauración del proyecto verificando la firma)

No obstante, en la interfaz de usuario (`gui/pages/dashboard.html`, `gui/js/dashboard.js` y `gui/pages/export.html`), no existe ninguna opción en la UI para:
1. Descargar el archivo `.thesisforge` como respaldo desde el panel de proyectos.
2. Arrastrar o subir un archivo `.thesisforge` para restaurar un proyecto existente.

### Comportamiento Esperado
1. En el panel principal de proyectos (`dashboard.html` / `dashboard.js`):
   - Agregar una acción en el menú contextual de cada tarjeta de proyecto: *"Exportar Respaldo (.thesisforge)"*.
   - Agregar un botón principal *"Importar Respaldo"* en la cabecera del dashboard con un input de tipo file para seleccionar el archivo `.thesisforge`.
2. En la pantalla de exportación (`export.html` / `export.js`):
   - Ofrecer el formato `.thesisforge` (Archivo de Respaldo Completo) como una de las opciones junto a Word (`.docx`).
3. Manejo de errores en frontend:
   - Mostrar notificaciones comprensibles si el archivo importado tiene una firma HMAC inválida, está corrupto o ya existe un proyecto con ese identificador.
