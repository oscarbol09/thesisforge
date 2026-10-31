### Descripción del Problema / Mejora
ThesisForge se diseñó con un enfoque primario en la norma **APA 7ª edición** para ciencias sociales, humanidades y salud. Sin embargo, para proyectos de ingeniería de sistemas, telecomunicaciones, medicina y ciencias de la salud, las instituciones académicas exigen estilos de citación numéricos como:
- **IEEE** (citas numéricas entre corchetes `[1]`, orden de aparición).
- **Vancouver** (citas en superíndice o paréntesis, orden de citación).

En `src/thesisforge/presentation/schemas.py` o en las opciones del exportador (`ExportOptionsDTO`), no existe un selector para elegir el estilo de citación ni la lógica para formatear referencias numéricas.

### Tareas a Realizar (Good First Issue)
1. **Modelos (`schemas.py` o `domain/models`)**:
   - Agregar el campo `citation_style: CitationStyle = CitationStyle.APA7` con soporte para `CitationStyle.IEEE` y `CitationStyle.VANCOUVER`.
2. **Formateo de Referencias**:
   - Implementar un formateador modular que, al seleccionar IEEE o Vancouver, reemplace las citas parentéticas `(Autor, 2024)` en el texto por números de índice correlativos `[1]` y ordene la lista bibliográfica final según el orden de aparición en el texto en lugar de orden alfabético.
3. **Frontend**:
   - Agregar un selector desplegable de estilo de citación en `export.html` (APA 7ª, IEEE, Vancouver).
4. **Pruebas**:
   - Crear pruebas unitarias verificando la asignación correcta de índices y el renderizado final de la bibliografía.
