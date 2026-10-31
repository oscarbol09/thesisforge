### Descripción del Problema
Al configurar NVIDIA NIM como proveedor de inferencia LLM en la bóveda de claves (`api_keys`), las llamadas a modelos de NVIDIA NIM fallan debido a dos discrepancias en la capa de enrutamiento (`router.py`):

1. **Resolución de la API Key en `router.py`**:
   En `src/thesisforge/infrastructure/llm/router.py`, al resolver la clave del proveedor:
   ```python
   # router.py (línea ~81)
   if provider in ("openai", "openrouter", "groq", "together"):
       ...
   ```
   El proveedor `"nvidia_nim"` no está contemplado en la tupla de verificación o no se mapea a la clave de entorno `NVIDIA_NIM_API_KEY` ni a la bóveda Fernet con el identificador exacto de proveedor, lo que provoca `LLMProviderError: No API key configured for provider 'nvidia_nim'`.

2. **Normalización del prefijo del modelo**:
   LiteLLM y el cliente compatible OpenAI de NVIDIA NIM esperan que los modelos lleven el prefijo `nvidia_nim/<model>` o que el `base_url` apunte a `https://integrate.api.nvidia.com/v1`. La lógica de normalización de cadenas de modelos no antepone automáticamente este prefijo si el usuario selecciona un modelo como `meta/llama-3.1-70b-instruct` o `mistralai/mixtral-8x22b-instruct`.

### Comportamiento Esperado
1. `router.py` debe soportar explícitamente `nvidia_nim` tanto en la extracción de claves desde `LocalKeyVault` como desde la variable de entorno `NVIDIA_NIM_API_KEY`.
2. Mapear de forma determinista el `api_base` hacia `https://integrate.api.nvidia.com/v1` y normalizar el nombre del modelo anteponiendo `nvidia_nim/` si no está presente al invocar `acompletion()`.
3. Añadir pruebas unitarias específicas en `tests/unit/test_llm_router.py` para el proveedor `nvidia_nim`.
