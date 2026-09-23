# Exportación en Formato APA 7ª Edición

ThesisForge genera documentos en formato Microsoft Word (`.docx`) y Markdown estructurado, configurados siguiendo los lineamientos oficiales del *Manual de Publicación de la American Psychological Association (7ª edición)*.

---

## Estándares de Formato Aplicados

Al compilar tu proyecto de investigación, ThesisForge aplica automáticamente:

1. **Página de Título (Portada):**
   - Título del proyecto en negrita y centrado en la mitad superior.
   - Nombre del autor, afiliación institucional, departamento académico, nombre del asesor y fecha.
2. **Tabla de Contenidos (Índice General):**
   - Inclusión automática de campo dinámico Word `TOC \o "1-3" \h \z \u` compatible con Microsoft Word, LibreOffice y Google Docs.
   - Lista estructurada de capítulos y secciones temáticas.
3. **Tipografía y Espaciado:**
   - Opciones tipográficas estandarizadas: *Times New Roman 12pt*, *Arial 11pt*, o *Calibri 11pt*.
   - Interlineado doble (2.0) en todo el cuerpo del documento sin espaciado extra entre párrafos.
   - Márgenes de 2.54 cm (1 pulgada) en los 4 bordes.
4. **Encabezados Jerárquicos (Nivel 1 al 5):**
   - **Nivel 1:** Centrado, Negrita, Título en Mayúsculas y Minúsculas.
   - **Nivel 2:** Alineado a la izquierda, Negrita.
   - **Nivel 3:** Alineado a la izquierda, Negrita y Cursiva.
   - **Nivel 4:** Alineado a la izquierda con sangría de 1.27 cm, Negrita, finaliza con punto.
   - **Nivel 5:** Alineado a la izquierda con sangría de 1.27 cm, Negrita y Cursiva, finaliza con punto.
5. **Tablas y Figuras:**
   - Estilo APA 7 con bordes horizontales limpios y sin líneas verticales.
   - Sanitización contra inyección de fórmulas (CWE-1236) para proteger la apertura del archivo en suites ofimáticas.
6. **Lista de Referencias Desduplicadas:**
   - Sangría francesa de 1.27 cm (0.5 pulgadas).
   - Orden alfabético estricto por apellido del primer autor.
   - Desduplicación inteligente cruzando identificadores DOI normalizados y firmas canónicas autor-título-año.
   - DOIs activos en formato de hipervínculo estándar (`https://doi.org/...`).

