### Descripción del Problema
En el archivo `Dockerfile`, durante la etapa de construcción y copia de archivos hacia la imagen de producción:
```dockerfile
# Dockerfile actual
COPY src ./src
COPY gui ./gui
COPY pyproject.toml README.md ./
```
Se observa que el directorio `assets/` (que contiene `logo.png`, `logo_dark.png`, `logo_light.png` y `favicon.ico`) **no es copiado** al contenedor Docker.

### Impacto
Al levantar la aplicación con Docker o Docker Compose:
```bash
docker compose up
```
1. El navegador solicita `GET /favicon.ico` o los logos de la aplicación servidos en `/assets/*`, recibiendo respuestas `HTTP 404 Not Found`.
2. La interfaz de usuario muestra imágenes rotas en la cabecera y en la pestaña del navegador.

### Solución Esperada (Good First Issue)
1. En `Dockerfile`, añadir la instrucción de copia:
   ```dockerfile
   COPY assets ./assets
   ```
2. Verificar que los permisos de lectura sean adecuados para el usuario sin privilegios (`non-root USER`).
3. Comprobar que en el endpoint estático de FastAPI (`app.py`), la ruta `/assets` monte correctamente dicho directorio si existe.
