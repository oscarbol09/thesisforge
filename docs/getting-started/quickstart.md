# Inicio Rápido

Aprende a configurar tu primer proyecto de investigación en menos de 5 minutos.

---

## 1. Iniciar la Aplicación

Inicia ThesisForge ejecutando:

```bash
# Opción A: Iniciar en modo escritorio interactivo (Ventana nativa con PyWebView)
thesisforge gui

# Opción B: Iniciar únicamente el servidor web local
thesisforge run
```

Abre tu navegador en `http://127.0.0.1:8000` o interactúa directamente en la ventana de escritorio.

---

## 2. Configurar tu Proveedor LLM (BYOK)

En la sección **Ajustes de Proveedor (BYOK)**:
- **Google Gemini:** Ingresa tu `AIzaSy...` para usar Gemini 2.5 Flash (Gratuito) o Gemini 2.5 Pro (Avanzado).
- **OpenRouter:** Ingresa tu `sk-or-v1-...` para acceder a modelos como Claude 3.5 Sonnet, GPT-4o o DeepSeek R1.
- **Groq:** Ingresa tu `gsk_...` para inferencia ultrarrápida con Llama 3.3 70B Versatile.
- **Ollama Local (100% Offline):** Deja la clave en blanco y selecciona `http://localhost:11434` con modelos como `llama3.1:8b` o `mistral`.
- **Botón Probar Conexión:** Haz clic en **Probar Conexión** para validar tus credenciales y latencia antes de guardar.

> [!TIP]
> Tus API keys son cifradas localmente en tu base de datos SQLite con una clave Fernet de 256 bits. Nunca se envían a servidores de ThesisForge.

---

## 3. Crear tu Proyecto de Investigación

1. Haz clic en **Nuevo Proyecto**.
2. Asigna un título provisional y selecciona tu nivel académico (Pregrado, Maestría o Doctorado).
3. Selecciona el enfoque metodológico inicial (Cuantitativo, Cualitativo o Mixto).

---

## 4. Estructuración Metodológica Asistida

El **Asesor Metodológico** te guiará a través de sus 7 secciones canónicas:
1. **Título y Nivel Académico:** Definición del tema, nivel y línea de investigación.
2. **Enfoque y Paradigma:** Selección del marco epistemológico (Positivista, Interpretativo, Crítico, Pragmático) y enfoque del estudio.
3. **Problema, Justificación y Alcance:** Caracterización empírica del problema (8 movimientos), vacío cognoscitivo, justificación por dimensiones y limitaciones.
4. **Objetivos y Preguntas de Investigación:** Formulación isomórfica de preguntas y objetivos con verbos taxonómicos en infinitivo.
5. **Marco Teórico y Estado del Arte:** Ejes conceptuales, antecedentes empíricos y fundamentación doctrinal.
6. **Hipótesis / Supuestos y Variables / Categorías:** Hipótesis cuantitativas con variables operacionales o supuestos cualitativos con categorías de análisis.
7. **Metodología, Técnicas, Instrumentos y Muestreo:** Diseño metodológico, población y muestra ($G*\text{Power}$ / saturación teórica), técnicas e instrumentos estructurados uno a uno.

Al completar la estructuración y validación de consistencia ($100\%$), tu **Ficha Metodológica** queda sellada y lista para la búsqueda RAG y la redacción de capítulos.
