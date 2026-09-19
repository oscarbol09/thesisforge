# Inicio Rápido 🚀

Aprende a configurar tu primer proyecto de investigación en menos de 5 minutos.

---

## 1. Iniciar la Aplicación

Inicia ThesisForge ejecutando:

```bash
thesisforge run
```

Abre tu navegador en `http://127.0.0.1:8000` o utiliza la ventana de la aplicación de escritorio.

---

## 2. Configurar tu Proveedor LLM (BYOK)

En la sección **Ajustes de Proveedor (BYOK)**:
- **OpenRouter:** Ingresa tu `sk-or-v1-...` para acceder a modelos como Claude 3.5 Sonnet o GPT-4o.
- **Google Gemini:** Ingresa tu `AIzaSy...` para usar Gemini 1.5 Pro o Flash.
- **Ollama Local (100% Offline):** Deja la clave en blanco y selecciona `http://localhost:11434` con modelos como `llama3.1:8b` o `mistral`.

> [!TIP]
> Tus API keys son cifradas localmente en tu base de datos SQLite con una clave Fernet de 256 bits. Nunca se envían a servidores de ThesisForge.

---

## 3. Crear tu Proyecto de Investigación

1. Haz clic en **Nuevo Proyecto**.
2. Asigna un título provisional y selecciona tu nivel académico (Pregrado, Maestría o Doctorado).
3. Selecciona el enfoque metodológico inicial (Cuantitativo, Cualitativo o Mixto).

---

## 4. Iniciar la Entrevista Metodológica

El **Asesor Metodológico** te guiará a través de 5 preguntas clave:
1. **Delimitación del Problema:** ¿Cuál es la situación observada y la brecha de conocimiento?
2. **Formulación de Objetivos:** Validación de verbos taxonómicos (determinar, analizar, evaluar).
3. **Hipótesis y Variables:** Identificación de variables independiente y dependiente o categorías de análisis.
4. **Enfoque y Diseño:** Definición del diseño muestral y técnicas de recolección de datos.

Al completar la entrevista, tu **Ficha Metodológica** queda sellada y lista para la búsqueda RAG y la redacción de capítulos.
