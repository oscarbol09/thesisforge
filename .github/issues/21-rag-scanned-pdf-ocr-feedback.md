### Descripción del Problema
Cuando un usuario sube un archivo PDF escaneado (un documento compuesto exclusivamente por imágenes rasterizadas sin capa de texto digital seleccionable) a la pestaña de Literatura (`POST /api/literature/index-pdf`), la extracción de texto mediante PyMuPDF produce 0 fragmentos.

Actualmente, el sistema falla con una excepción genérica:
```
DocumentProcessingError: No se pudieron extraer fragmentos de texto válidos del documento PDF.
```
En la interfaz gráfica, el usuario sólo observa un toast de error que no explica la causa raíz del problema ni ofrece una alternativa de solución.

### Causa Raíz
En `src/thesisforge/rag/parser.py` (línea 256):
```python
page_text = page.get_text("text", sort=True)
if not page_text or not page_text.strip():
    continue
```
Y en `src/thesisforge/rag/service.py` (líneas 311-323):
```python
if not chunks:
    await self._upsert_index_status(...)
    raise DocumentProcessingError(
        "No se pudieron extraer fragmentos de texto válidos del documento PDF."
    )
```
No se detecta si el documento tiene páginas con imágenes pero sin texto, lo cual es el síntoma característico de un PDF escaneado que requiere Reconocimiento Óptico de Caracteres (OCR).

### Solución Esperada (Good First Issue)
1. En `parser.py` o `service.py`, al detectar que un PDF tiene páginas (`len(doc) > 0`) pero 0 caracteres de texto extraído:
   - Inspeccionar si la página contiene imágenes (`len(page.get_images()) > 0`).
   - Lanzar un mensaje específico y accionable:
     ```
     DocumentProcessingError: El PDF subido parece ser un documento escaneado basado en imágenes sin capa de texto digital (OCR). Para indexarlo en ThesisForge, aplica previamente OCR con herramientas como OCRmyPDF, Adobe Acrobat o Tesseract.
     ```
2. Registrar este estado diagnóstico en `document_index_status.error_msg`.
3. Añadir una prueba unitaria simulando un PDF sin texto pero con imágenes para verificar el mensaje educativo de error.
