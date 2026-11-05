### Descripción del Problema
En el endpoint de prueba de conectividad de modelos de lenguaje:
`POST /api/settings/test-connection` (`src/thesisforge/api/routes_settings.py`),
cuando un usuario ingresa una clave de API en el formulario para probar un proveedor, la aplicación guarda inmediatamente dicha clave en la base de datos de manera definitiva, sobrescribiendo la clave previamente almacenada.

Si la prueba de conexión falla (por ejemplo, por escribir mal la clave, ingresar un token expirado o probar un modelo no habilitado), la clave original válida del usuario ya fue destruida en la base de datos SQLite y no es posible recuperarla.

### Causa Raíz
En `src/thesisforge/api/routes_settings.py` (líneas 150-153):
```python
# Temporarily store or pass key if testing unsaved key
if payload.api_key and payload.api_key.strip():
    await keystore.store_key(normalized_provider, payload.api_key.strip())
```
A pesar del comentario (`Temporarily store`), el método `keystore.store_key` cifra y guarda de forma persistente la clave en la tabla `keystore`. Si la llamada posterior a `router_instance.complete(...)` lanza una excepción (línea 170), el bloque `except Exception as exc:` se limita a registrar el error y devolver `status: "error"`, dejando la clave defectuosa guardada en la base de datos sin ningún mecanismo de rollback.

### Comportamiento Esperado
1. Un endpoint de prueba (`test-connection`) no debe tener efectos secundarios destructivos en la persistencia.
2. Si el usuario envía un `api_key` temporal para probar, `LLMRouter` debe recibir esa clave directamente en memoria para la petición de prueba sin alterar el registro en `SecureKeyStoreRepository`.
3. La clave sólo debe guardarse en la base de datos cuando el usuario haga clic explícitamente en "Guardar Clave" (`POST /api/settings/keys`).
4. Añadir tests unitarios que verifiquen que probar una clave errónea en `/test-connection` no modifique la clave almacenada en el keystore.
