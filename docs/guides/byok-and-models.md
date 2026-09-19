# BYOK & Configuración de Modelos 🔑

ThesisForge adopta una filosofía estricta de **Bring Your Own Key (BYOK)** y **Local-First**. No cobramos suscripciones por uso de modelos ni intermediamos tus tokens.

---

## 🌐 Proveedores Soportados

| Proveedor | Modelos Recomendados | Nivel de Privacidad | Cómo Obtener Clave |
|:----------|:---------------------|:-------------------:|:-------------------|
| **Ollama (Local)** | `llama3.1:8b`, `mistral-nemo`, `qwen2.5:14b` | 🔒 100% Offline / Privado | No requiere clave ([ollama.ai](https://ollama.ai)) |
| **OpenRouter** | `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.1-70b-instruct` | 🌐 Cloud BYOK | [openrouter.ai/keys](https://openrouter.ai/keys) |
| **Google Gemini** | `gemini-1.5-pro-latest`, `gemini-1.5-flash` | 🌐 Cloud BYOK | [aistudio.google.com](https://aistudio.google.com/) |
| **Groq Cloud** | `llama-3.1-70b-versatile`, `mixtral-8x7b-32768` | 🌐 Cloud BYOK | [console.groq.com](https://console.groq.com) |
| **OpenAI Compatible**| `gpt-4o`, `gpt-4o-mini`, vLLM, LM Studio endpoints | 🌐 / 🔒 Según host | [platform.openai.com](https://platform.openai.com) |

---

## 🖥️ Configuración de Ollama (100% Local y Gratuito)

Para ejecutar ThesisForge completamente sin conexión a internet y con privacidad absoluta de tus datos de investigación:

```bash
# 1. Instalar Ollama y descargar un modelo adecuado para investigación
ollama run llama3.1:8b

# 2. En ThesisForge:
# - Seleccionar proveedor: "Ollama"
# - URL Endpoint: "http://localhost:11434"
# - Modelo: "llama3.1:8b"
```

---

## 🔐 Cifrado de Claves en Reposo

Tus claves privadas nunca viajan a ningún servidor central:
- Se cifran localmente con el algoritmo simétrico **Fernet (AES-128-CBC + HMAC-SHA256)**.
- La llave maestra de descifrado reside únicamente en tu entorno de ejecución local (`.env` o variable de entorno del sistema).
