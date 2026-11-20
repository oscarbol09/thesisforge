### Descripción del Problema
El auditor de fabricación bibliográfica `AIFailureGateAuditor._audit_literature_fabrication()` genera falsos positivos sistemáticos sobre citas APA 7 reales provenientes de CrossRef, Semantic Scholar, OpenAlex y arXiv, marcando capítulos válidos con hallazgos críticos de presunta alucinación de fuentes.

### Causa Raíz
1. En `src/thesisforge/jury/ai_failure_gate.py` (líneas 171–208):
   ```python
   known_authors = {
       author.lower()
       for cit in project.validated_citations
       for author in cit.authors
   }
   in_text_authors = re.findall(
       r"\(([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)(?:\s+et\s+al\.)?,\s*\d{4}\)",
       all_content,
   )
   unmatched_authors = [
       a for a in in_text_authors if known_authors and a.lower() not in known_authors
   ]
   ```
   - `cit.authors` almacena nombres completos o normalizados con iniciales (p. ej. `"Ashish Vaswani"`, `"Vaswani, A."` o `"Gabriel García-Márquez"`), mientras que la regex extrae únicamente el primer token de apellido simple (`"Vaswani"`).
   - Como `"vaswani"` no es igual al string completo `"ashish vaswani"`, **ninguna** cita parentética estándar `(Vaswani et al., 2017)` coincide con `known_authors`.
2. Adicionalmente, la expresión regular actual no contempla:
   - Apellidos compuestos con guion o espacios (p. ej. `(García-Márquez, 1982)` o `(De la Cruz, 2021)`).
   - Citas parentéticas de dos autores con `&` o `y` (p. ej. `(Pérez & López, 2023)`).
3. En `tests/unit/test_ai_failure_gate.py` (líneas 53 y 59), la prueba pasó únicamente porque el fixture simuló autores monónimos (`["Gómez", "Pérez"]`) y usó citas narrativas (`Gómez (2024)`), las cuales la regex ignoró por completo.

### Comportamiento Esperado
1. Extraer el apellido normalizado (en minúsculas y sin signos de puntuación) de cada entrada en `cit.authors` (soportando formatos `"Nombre Apellido"` y `"Apellido, N."`).
2. Ampliar la extracción de citas en el texto para contemplar apellidos compuestos, dos autores (`&` / `y`), `et al.`, y opcionalmente citas narrativas `Apellido (Año)`.
3. Añadir pruebas unitarias en `tests/unit/test_ai_failure_gate.py` con nombres completos reales (`["Ashish Vaswani", "Vaswani, A."]` y `(Vaswani et al., 2017)`) verificando cero falsos positivos, manteniendo la detección real ante autores inventados `(Smith, 2025)`.
