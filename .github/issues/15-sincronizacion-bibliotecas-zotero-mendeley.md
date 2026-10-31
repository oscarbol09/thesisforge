### Descripción del Problema / Propuesta (RFC)
Actualmente, el motor RAG de literatura científica de ThesisForge (`src/thesisforge/infrastructure/drivers/`) permite consultar fuentes abiertas en línea (Semantic Scholar, CrossRef, ArXiv) o subir manualmente archivos PDF locales.

Muchos tesistas e investigadores ya tienen colecciones extensas y organizadas de artículos con notas, etiquetas y metadatos verificados en gestores de referencias populares como **Zotero** o **Mendeley**.

Para facilitar la adopción sin fricción y evitar que el usuario deba descargar y volver a subir decenas de PDFs uno a uno, se propone añadir conectores de sincronización local.

### Especificación de la Característica
1. **Conector Local de Zotero**:
   - Lectura de la base de datos local SQLite de Zotero (`zotero.sqlite`) o consumo de la API local de Zotero (`http://localhost:23119/api` provista por el conector / Better BibTeX).
   - O alternativamente, importación de archivos de exportación estándar: `.bib` (BibTeX), `.ris` o JSON de CSL (Citation Style Language).
2. **Ingesta e Indexación Automática**:
   - Extraer metadatos (título, autores, año, resumen, DOI) y rutas a los PDFs adjuntos en el almacenamiento local de Zotero.
   - Indexar los textos en ChromaDB asociados a la colección de literatura del proyecto en ThesisForge.
3. **Interfaz de Usuario**:
   - En la vista `literature.html`, agregar la opción *"Importar desde Zotero / RIS / BibTeX"*.
