# BYOK & Configuración de Modelos

ThesisForge adopta una filosofía estricta de **Bring Your Own Key (BYOK)** y **Local-First**. No cobramos suscripciones por uso de modelos ni intermediamos tus tokens.

---

## Catálogo Curado de Proveedores y Modelos

ThesisForge clasifica los modelos recomendados en opciones gratuitas (*Free / Open*) y modelos de alto rendimiento cognitivo (*Tier Superior*), asegurando que siempre utilices identificadores vigentes y compatibles:

| Proveedor | Modelos Gratuitos (*Free Tier*) | Modelos Tier Superior (*High Capacity*) | Cómo Obtener Clave |
| :--- | :--- | :--- | :--- |
| **OpenRouter** | `meta-llama/llama-3.3-70b-instruct:free`<br>`google/gemini-2.0-flash-exp:free`<br>`qwen/qwen-2.5-72b-instruct:free` | `anthropic/claude-3.5-sonnet`<br>`openai/gpt-4o`<br>`deepseek/deepseek-r1` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| **Google Gemini** | `gemini-2.0-flash`<br>`gemini-2.5-flash` | `gemini-2.5-pro`<br>`gemini-2.0-pro` | [aistudio.google.com](https://aistudio.google.com/) |
| **Anthropic** | *(No ofrece free tier directo)* | `claude-3-7-sonnet-20250219`<br>`claude-3-5-sonnet-20241022` | [console.anthropic.com](https://console.anthropic.com/) |
| **OpenAI** | *(No ofrece free tier directo)* | `gpt-4o`<br>`gpt-4o-mini`<br>`o3-mini` | [platform.openai.com](https://platform.openai.com/) |
| **Groq Cloud** | `llama-3.3-70b-versatile`<br>`llama-3.1-8b-instant` | `deepseek-r1-distill-llama-70b`<br>`qwen-2.5-32b` | [console.groq.com](https://console.groq.com/) |
| **Ollama (Local)** | `llama3.3:latest`<br>`qwen2.5:14b`<br>`deepseek-r1:14b`<br>`mistral-nemo:12b` | Ejecución en hardware local propio | [ollama.ai](https://ollama.ai/) |


---

## Verificación de Conexión en Tiempo Real

La interfaz y la API de ThesisForge incluyen una utilidad para comprobar la validez de las credenciales y el estado del modelo antes de iniciar una sesión de redacción:

```bash
# Probar conexión con un modelo y proveedor específico
POST /api/settings/test-connection
Content-Type: application/json

{
  "provider": "openrouter",
  "model": "meta-llama/llama-3.3-70b-instruct:free",
  "api_key": "sk-or-v1-..."  # Opcional si ya está cifrada en la bóveda
}
```

Respuesta estructurada:
```json
{
  "status": "success",
  "provider": "openrouter",
  "model": "meta-llama/llama-3.3-70b-instruct:free",
  "latency_ms": 420.5,
  "message": "Conexión exitosa con OpenRouter (meta-llama/llama-3.3-70b-instruct:free) en 420.5 ms."
}
```

---

## Configuración de Ollama (100% Local y Gratuito)

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

## Cifrado de Claves en Reposo

Tus claves privadas nunca viajan a ningún servidor central:
- Se cifran localmente con el algoritmo simétrico **Fernet (AES-128-CBC + HMAC-SHA256)**.
- La llave maestra de descifrado reside únicamente en tu entorno de ejecución local (`.env` o variable de entorno del sistema).

---

## Normalización de Modelos en OpenRouter

ThesisForge gestiona de forma transparente identificadores con prefijo de organización en OpenRouter (`src/thesisforge/llm/router.py`):
- Los modelos como `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.1-70b-instruct` u `openai/gpt-4o` son normalizados automáticamente con el prefijo `openrouter/` sin alterar el nombre del proveedor en la petición.

---

## Configuración de Embeddings Semánticos

Para la indexación y recuperación vectorial con ChromaDB:
- **FastLocal (Por defecto):** Algoritmo hash de 384 dimensiones sin consumo de memoria extra ni descargas de modelos pesados, ideal para arranque instantáneo.
- **Sentence Transformers (Opcional):** Configura `embedding_provider: sentence-transformers` en `config.yaml` o mediante la variable `THESISFORGE_EMBEDDING_PROVIDER` para usar modelos como `all-MiniLM-L6-v2` o `paraphrase-multilingual-MiniLM-L12-v2`.

---

## Variables de Entorno de Seguridad

| Variable | Descripción | Valor por Defecto |
|:---|:---|:---|
| `THESISFORGE_INSTANCE_TOKEN` | Token secreto para proteger peticiones HTTP y WebSockets | Generado automáticamente |
| `THESISFORGE_AUTH_DISABLED` | Desactiva autenticación (solo para desarrollo local/tests) | `false` |
| `THESISFORGE_KEYVAULT_SECRET` | Clave maestra para el cifrado Fernet de las API keys | Clave de desarrollo |

