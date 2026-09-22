# Manual de Usuario Oficial — ThesisForge

Guía integral para la formulación, fundamentación bibliográfica, redacción modular y compilación de proyectos de tesis y artículos científicos con **ThesisForge**.

---

## 1. Introducción y Filosofía de Diseño

ThesisForge es una plataforma de software diseñada para asistir a tesistas, investigadores y directores de tesis a lo largo de todo el ciclo de vida del trabajo de grado. A diferencia de generadores de texto genéricos, ThesisForge implementa:

1. **Garantía Metodológica**: Validación taxonómica basada en taxonomía de Bloom y matrices de consistencia científica.
2. **Trazabilidad Probatoria (RAG Real)**: Cada afirmación fáctica puede contrastarse contra literatura indexada en tiempo real (Semantic Scholar, ArXiv, CrossRef y PDFs propios).
3. **Memoria Contextual Jerárquica**: Los capítulos se redactan conservando la memoria viva de la metodología aprobada y los resúmenes de las secciones precedentes.
4. **Privacidad Estricta (BYOK + AppSec)**: Claves API cifradas localmente con AES-256-GCM y defensas perimetrales contra SSRF y Formula Injection (CWE-1236).
5. **Formateo Editorial APA 7ª Edición**: Generación automatizada de archivos Microsoft Word (`.docx`) respetando tipografía, sangría francesa, márgenes y estilos de tablas.

---

## 2. Requisitos del Sistema e Instalación

### Requisitos Previos
* **Python**: Versión 3.10 o superior (recomendado Python 3.12).
* **Gestor de Paquetes**: `uv` (recomendado) o `pip`.
* **Motor LLM**: Servidor local Ollama, clave Google Gemini, OpenAI o cuenta en OpenRouter.

### Instalación Rápida
```bash
# Clonar el repositorio
git clone https://github.com/oscarbol09/thesisforge.git
cd thesisforge

# Crear entorno virtual e instalar dependencias
uv venv
uv pip install -e ".[dev]"
```

---

## 3. Flujo de Trabajo en Cuatro Fases

```
┌─────────────────────────────────────────────────────────────┐
│ FASE 1: Orientación & Formulación Metodológica             │
│ (Tema -> Problema -> Objetivos -> Matriz de Consistencia)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 2: Contexto Bibliográfico & Evidencia RAG              │
│ (Búsqueda Real -> Ingestión PDF -> Citation Guard)          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 3: Redacción Modular & Compilación APA 7               │
│ (Capítulos 1-5 -> Memoria Jerárquica -> DOCX Compilado)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 4: Tribunal Multi-Agente & Defensa Oral Socrática     │
│ (Auditoría 4 Jurados -> Veredicto -> Rondas de Réplica WS)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Fase 1: Delimitación Metodológica con el Asesor

### Creación de un Proyecto
El proyecto almacena la configuración de nivel académico (Pregrado, Maestría, Doctorado), enfoque metodológico (Cuantitativo, Cualitativo, Mixto) y estado de avance.

```bash
# Iniciar el servidor local
thesisforge run --port 8000
```

A través de la API REST o interfaz web:
* `POST /api/projects`: Define el título tentativo, área de estudio y nivel.
* `POST /api/advisor/{project_id}/step`: Permite completar secuencialmente cada uno de los 7 pasos metodológicos guiados:
  1. `problem_statement`: Planteamiento del problema (mínimo 100 caracteres con diagnóstico empírico).
  2. `research_question`: Pregunta general (inicia con pronombre interrogativo y signo de cierre).
  3. `hypothesis`: Hipótesis explicativa (obligatoria en cuantitativo/mixto, omitible en cualitativo).
  4. `general_objective`: Objetivo general encabezado por verbo en infinitivo evaluable.
  5. `specific_objectives`: Lista de objetivos específicos derivados.
  6. `justification`: Relevancia teórica, metodológica y práctica.
  7. `methodology`: Tipo y diseño de investigación, población, muestra e instrumentos.

---

## 5. Fase 2: Búsqueda y Verificación Bibliográfica (RAG)

### Búsqueda en Bases de Datos Reales
ThesisForge consulta directamente los índices abiertos de Semantic Scholar, ArXiv y CrossRef:

```bash
# Búsqueda desde la terminal
thesisforge search-papers "machine learning in healthcare" --limit 5 --format apa
```

### Ingestión de Documentos PDF Propios
Los artículos en formato PDF se procesan extrayendo metadatos, limpiando encabezados repetitivos y dividiendo el texto en fragmentos que preservan abreviaturas académicas:

```bash
# Endpoint para subir e indexar artículos al vector store local
POST /api/literature/projects/{project_id}/documents/index-pdf
```

### Validación de Afirmaciones (Citation Guard)
Para verificar si un enunciado teórico está respaldado por los documentos indexados:
```bash
POST /api/literature/projects/{project_id}/verify-claim
{
  "claim": "Los modelos de lenguaje basados en transformers mejoran la precisión en diagnósticos preliminares."
}
```

---

## 6. Fase 3: Redacción Modular por Capítulos

### Estructura Canónica de 5 Capítulos
ThesisForge inicializa automáticamente la estructura estándar requerida por universidades de habla hispana:

* **Capítulo I: Planteamiento del Problema**
  * `sec_1_1`: Descripción de la realidad problemática
  * `sec_1_2`: Formulación del problema (general y específicos)
  * `sec_1_3`: Objetivos de la investigación
  * `sec_1_4`: Justificación y viabilidad
  * `sec_1_5`: Delimitación y limitaciones
* **Capítulo II: Marco Teórico**
  * `sec_2_1`: Antecedentes internacionales y nacionales
  * `sec_2_2`: Bases teórico-científicas
  * `sec_2_3`: Definición de términos básicos
  * `sec_2_4`: Hipótesis y operacionalización de variables
* **Capítulo III: Metodología**
  * `sec_3_1`: Tipo, nivel y diseño de investigación
  * `sec_3_2`: Población y muestra
  * `sec_3_3`: Técnicas e instrumentos de recolección
  * `sec_3_4`: Procedimientos de análisis de datos
* **Capítulo IV: Resultados y Discusión**
  * `sec_4_1`: Presentación de resultados descriptivos
  * `sec_4_2`: Contrastación de hipótesis
  * `sec_4_3`: Discusión de hallazgos frente a antecedentes
* **Capítulo V: Conclusiones y Recomendaciones**
  * `sec_5_1`: Conclusiones vinculadas a objetivos
  * `sec_5_2`: Recomendaciones académicas y aplicadas

### Comandos CLI de Redacción
```bash
# Inicializar la estructura capitular de un proyecto
thesisforge draft-init --project-id "proj_abc123"

# Listar las secciones y su estado de avance
thesisforge draft-list --project-id "proj_abc123"
```

### Streaming en Tiempo Real vía WebSockets
Para observar la generación progresiva de un capítulo o sección:

```javascript
const ws = new WebSocket("ws://localhost:8000/api/drafting/ws/proj_abc123/sec_1_1");

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: "generate",
    user_instructions: "Profundizar en antecedentes de los últimos 3 años."
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.event === "token") {
    process.stdout.write(msg.data);
  } else if (msg.event === "complete") {
    console.log("\nBorrador generado con éxito:", msg.section.word_count, "palabras");
  }
};
```

---

## 7. Compilación y Exportación APA 7ª Edición

ThesisForge compila directamente el estado del proyecto en un archivo `.docx` con las especificaciones editoriales oficiales de la American Psychological Association (APA 7th Edition):

* **Márgenes**: 2.54 cm (1.0 pulgada) en los cuatro costados.
* **Tipografía**: Times New Roman 12 pt (o Calibri 11 pt).
* **Interlineado**: Doble espacio (2.0) sin espaciado adicional entre párrafos.
* **Sangría**: Primera línea de cada párrafo con 1.27 cm (0.5 pulgadas).
* **Portada para Estudiante / Profesional**: Título en negrita centrado, autor, afiliación institucional, asesor y fecha.
* **Paginación**: Número de página en esquina superior derecha de cada encabezado.
* **Tablas**: Estilo APA 7 con bordes horizontales únicamente y sanitización estricta contra inyección de fórmulas (CWE-1236).
* **Referencias**: Sangría francesa de 1.27 cm y ordenación alfabética automática.

### Compilación desde la Terminal
```bash
thesisforge export-docx \
  --project-id "proj_abc123" \
  --output "./tesis_final.docx" \
  --author "Lic. Valeria Mendoza" \
  --institution "Universidad Nacional de Ingeniería" \
  --advisor "Dra. Carmen Soto"
```

### Compilación desde la API REST
```bash
curl -X POST "http://localhost:8000/api/export/projects/proj_abc123/docx" \
  -H "Content-Type: application/json" \
  -d '{
    "author_name": "Valeria Mendoza",
    "institution_name": "Universidad Nacional",
    "advisor_name": "Dra. Carmen Soto",
    "year": 2026
  }' \
  --output tesis_compilada.docx
```

---

## 8. Fase 4: Tribunal Multi-Agente y Simulador de Defensa Socrática

### Composición del Tribunal Académico
ThesisForge somete la tesis a una evaluación multidisciplinaria conformada por cuatro perfiles académicos rigurosos:

1. **Dr. Arístides Valenzuela (Metodólogo Principal)**: Evalúa la alineación epistemológica entre el problema, los objetivos, la hipótesis y el diseño metodológico.
2. **Dra. Beatriz Salamanca (Especialista Temática)**: Revisa la densidad teórica, la relevancia empírica del marco conceptual y la pertinencia de los antecedentes.
3. **Dr. Camilo Restrepo (Auditor Estadístico)**: Audita el cálculo muestral, la validez interna/externa, la coherencia de los contrastes de hipótesis y los análisis estadísticos.
4. **Dr. Demetrio Sotomayor (Abogado del Diablo)**: Identifica sesgos de confirmación, variables confusoras no controladas, causalidades espurias y debilidades argumentativas.

### Auditoría Científica Híbrida
El motor de evaluación combina:
* **Reglas Deterministas**: Verificación formal de matrices de consistencia, correspondencia entre enfoque cuantitativo e hipótesis explícitas, y umbral mínimo de citas APA 7.
* **Deliberación Cualitativa**: Dictámenes analíticos con ponderaciones de 0 a 100 y clasificación de observaciones (`CRITICAL`, `MAJOR`, `MINOR`, `SUGGESTION`).
* **Veredictos Oficiales**: `APROBADO_CON_DISTINCION`, `APROBADO`, `MODIFICACIONES_MENORES`, `MODIFICACIONES_MAYORES`, `NO_APROBADO` (con regla estricta de veto automático ante anomalías críticas).

### Simulador Socrático de Defensa Oral
Permite al tesista ensayar la sustentación de su trabajo frente al tribunal:
* **Generación de Preguntas Calibradas**: Basadas en las debilidades reales detectadas durante la auditoría del proyecto.
* **Evaluación de Réplicas por Turnos**: Calificación de respuestas (0–100) con retroalimentación detallada y rúbricas formativas.
* **Sesiones en Tiempo Real vía WebSocket**: Conexión bidireccional continua en `/api/defense/ws/{session_id}`.

### Comandos de Consola (CLI)
```bash
# Ejecutar auditoría completa del jurado y guardar acta formal
thesisforge jury-audit --project-id "proj_abc123" --save

# Iniciar simulación interactiva de sustentación en la terminal
thesisforge defense-start --project-id "proj_abc123" --turns 4
```

---

## 9. Seguridad y Privacidad

* **Cero Fuga de Datos**: Las claves de API se almacenan localmente en la base de datos SQLite cifradas con una clave maestra local AES-256 (`LocalKeyVault`).
* **Protección SSRF**: Cualquier descarga de artículos remotos pasa por filtros que bloquean direcciones IP privadas, de enlace local (`169.254.169.254`), bucles locales y esquemas inseguros (`file://`, `gopher://`).
* **Defensa CWE-1236**: Los datos contenidos en tablas se escapan ante fórmulas maliciosas de Excel/Word (`=`, `+`, `-`, `@`, `\t`, `\r`).
