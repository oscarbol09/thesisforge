# RAG y Búsqueda de Literatura Real 📚

Una de las principales debilidades de los modelos de lenguaje comercial (ChatGPT, Claude) es la invención de citas bibliográficas, autores y DOIs falsos (*alucinaciones*).

ThesisForge implementa un motor RAG (**Retrieval-Augmented Generation**) diseñado específicamente para literatura científica.

---

## 🔍 Fuentes Indexadas en Tiempo Real

ThesisForge se conecta de manera asíncrona a las siguientes bases de datos científicas abiertas:

1. **Semantic Scholar Academic Graph API:** Acceso a más de 200 millones de papers, resúmenes, métricas de citación e influencias metodológicas.
2. **ArXiv API:** Búsqueda en repositorios preprint de ciencias de la computación, física, matemáticas y estadística.
3. **CrossRef API:** Validación cruzada de metadatos de publicación y resolución estricta de DOIs.

---

## 📑 Búsqueda Vectorial Local (Tus Propios PDFs)

Puedes subir tus propios archivos PDF (artículos, libros, tesis previas):
- **Chunking Contextual:** División en fragmentos de 1500 caracteres con solapamiento de 200 caracteres para preservar la semántica del párrafo.
- **Indexación Vectorial:** Almacenamiento local mediante ChromaDB / SQLite-vec con embeddings de última generación.
- **Reranking:** Los fragmentos más relevantes son rankeados por relevancia léxica y semántica antes de ser inyectados en el prompt.

---

## 🛡️ Filtro Anti-Alucinaciones

Antes de redactar cualquier sección bibliográfica:
1. Toda cita debe tener un identificador verificado (DOI, ArXiv ID o fuente local cargada).
2. Si un modelo sugiere una afirmación sin respaldo en los fragmentos recuperados, el validador exige confirmación o la descarta.
3. Las citas se formatean automáticamente en el cuerpo del texto como `(Apellido, Año)` o `Apellido (Año)`.
