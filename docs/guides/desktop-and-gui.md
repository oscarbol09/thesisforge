# Guía de Interfaz SPA & Entorno de Escritorio Nativo

Esta guía explica la arquitectura, características y modo de uso de la **interfaz de usuario SPA (Single-Page Application)** y el **lanzador de escritorio nativo con PyWebView** introducidos en ThesisForge v0.5.0.

---

## 1. Visión General de la Interfaz Visual

ThesisForge incluye una interfaz web moderna, reactiva y ligera construida con **Tailwind CSS** y **Alpine.js**, servida directamente por el backend de FastAPI sin necesidad de cadenas de compilación complejas ni dependencias de Node.js.

```
┌─────────────────────────────────────────────────────────────┐
│                 Ventana Nativa (PyWebView)                  │
│                                                             │
│  ┌─────────────────────── SPA Monomando ─────────────────┐  │
│  │ [Dashboard] [Asesor] [RAG] [Redacción] [Word] [Jury]   │  │
│  │                                                       │  │
│  │  • Telemetría de Proyecto & Métricas en Vivo          │  │
│  │  • Stepper Metodológico de 9 Pasos                    │  │
│  │  • Búsqueda Federada & Subida Directa de PDFs         │  │
│  │  • Streaming por WebSockets en Redacción              │  │
│  │  • Descarga Directa de Manuscrito APA 7 (.docx)       │  │
│  │  • Deliberación de Tribunal Doctoral y Defensa Oral   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Lanzamiento del Entorno de Escritorio

### Comando CLI de Escritorio
Para abrir ThesisForge en una ventana nativa independiente de escritorio:

```bash
thesisforge gui
```

### Opciones Avanzadas del Lanzador
```bash
# Especificar puerto fijo o interfaz de red
thesisforge gui --port 8080 --host 127.0.0.1

# Habilitar herramientas de inspección y desarrollo (DevTools)
thesisforge gui --debug
```

### Cómo Funciona Internamente el Lanzador
1. **Descubrimiento Dinámico de Puerto**: El módulo `thesisforge.desktop.launcher` busca un puerto TCP libre en `127.0.0.1` si se especifica el puerto `0` (comportamiento por defecto).
2. **Servidor en Hilo Daemon**: Inicia la API de FastAPI / Uvicorn en un subproceso en segundo plano.
3. **Sondeo de Salud Asíncrono**: Verifica la disponibilidad del endpoint `/health` antes de renderizar la ventana.
4. **Contenedor PyWebView**: Abre una ventana nativa del sistema operativo (usando WebView2 en Windows, WebKit2GTK en Linux o WebKit en macOS).

---

## 3. Módulos y Vistas de la SPA

### A. Portafolio & Dashboard (`gui/js/dashboard.js`)
- Gestión centralizada de proyectos con tarjetas informativas.
- Indicadores de estado de avance, número de palabras redactadas y fuentes bibliográficas validadas.
- Creación rápida de proyectos con asignación de título, nivel académico (Pregrado, Maestría, Doctorado) y área de estudio.

### B. Asesor Metodológico (`gui/js/advisor.js`)
- Flujo secuencial guiado por la máquina de estados finita.
- Validación interactiva de verbos taxonómicos en objetivos e hipótesis.
- Ficha de consistencia metodológica con aprobación formal.

### C. Literatura & RAG Científico (`gui/js/literature.js`)
- Búsqueda académica federada en tiempo real en **Semantic Scholar**, **ArXiv** y **CrossRef**.
- Subida directa de archivos PDF e indexación vectorial automática en ChromaDB con extracción PyMuPDF.
- Validador de afirmaciones científicas (*Citation Guard*) para verificar respaldo probatorio contra la literatura indexada.

### D. Redacción Capitular por Streaming (`gui/js/drafting.js`)
- Navegación interactiva por el esquema de 5 capítulos y 19 secciones temáticas.
- Generación con streaming en tiempo real mediante WebSockets (`ws://localhost:8000/api/drafting/ws/...`).
- Higiene estricta de conexiones: desconexión automática y nulificación de sockets al cambiar de sección para prevenir fugas de memoria.
- Aprobación de secciones con síntesis automática en la memoria jerárquica de 4 capas.

### E. Compilación y Descarga APA 7 (`gui/js/export.js`)
- Formulario de metadatos institucionales (autor, afiliación, asesor, año).
- Opciones editoriales: inclusión de portada, tabla de contenidos (TOC) y referencias desduplicadas.
- Compilación y descarga directa del archivo `.docx` formateado con márgenes de 2.54 cm, tipografía formal y sangría francesa.

### F. Tribunal Multi-Agente & Sustentación Oral (`gui/js/jury.js`, `gui/js/defense.js`)
- Evaluación simultánea por los 4 jurados académicos doctorales.
- Rúbrica dimensional cuantitativa (0–100) y veredicto oficial.
- Simulador de sustentación socrática por turnos con retroalimentación inmediata.

### G. Ajustes BYOK y Seguridad (`gui/js/settings.js`)
- Modal para configurar claves de API de proveedores LLM (Google Gemini, OpenRouter, OpenAI, Groq, NVIDIA NIM) o servidor local Ollama (`http://localhost:11434`).
- Las credenciales se almacenan cifradas localmente con una clave Fernet de 256 bits (`LocalKeyVault`).
