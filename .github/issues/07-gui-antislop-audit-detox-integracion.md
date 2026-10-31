### Descripción del Problema
ThesisForge cuenta con un motor especializado de auditoría y desintoxicación de prosa generada por IA (`src/thesisforge/domain/services/detox.py`), el cual detecta muletillas clásicas de IA (p. ej. *"crucial destacar"*, *"en resumen"*, *"un tapiz complejo"*, *"es imperativo subrayar"*), calcula la varianza de longitud de oraciones y audita la especificidad empírica.

Existe un endpoint backend en la API REST:
`POST /api/drafting/{project_id}/sections/{section_id}/quality-audit`
que retorna el análisis de calidad con puntuación y advertencias de *slop*.

Sin embargo, en la interfaz web (`gui/pages/drafting.html` y `gui/js/drafting.js`), no existe ningún botón, tarjeta o indicador visual que permita al usuario ejecutar esta auditoría sobre la sección redactada o visualizar las sugerencias de desintoxicación estilística. La funcionalidad está huérfana en el frontend.

### Tareas a Realizar (Ideal para principiantes / Good First Issue)
1. **Frontend (`gui/pages/drafting.html`)**:
   - Añadir un botón accesible *"Auditar Estilo & Slop IA"* junto a los controles de edición y generación de la sección.
   - Diseñar un modal o panel lateral desplegable para mostrar la puntuación de calidad (0 a 100), la lista de frases detectadas como muletillas de IA y recomendaciones de mejora de ritmo oracional.
2. **Lógica JS (`gui/js/drafting.js`)**:
   - Conectar el evento click del botón para invocar `POST /api/drafting/${projectId}/sections/${sectionId}/quality-audit` pasando el token de autenticación (`Authorization: Bearer ...`).
   - Renderizar los resultados de forma clara con insignias de color (verde: prosa limpia, amarillo: moderado, rojo: alta densidad de muletillas).
3. **Pruebas**:
   - Verificar manualmente en el navegador que al hacer clic se obtenga el desglose de calidad y no se produzcan errores de JavaScript en la consola.
