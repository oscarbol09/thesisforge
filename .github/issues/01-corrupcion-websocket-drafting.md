---
title: "[BUG]: Corrupción de texto en streaming WebSocket de redacción por discrepancia de payload de eventos"
labels: ["bug", "critical", "drafting", "websockets", "frontend"]
assignees: []
---

## Descripción del Error
Durante la generación en tiempo real de capítulos o secciones mediante WebSockets (`/api/drafting/ws/{project_id}/{section_id}`), el editor en pantalla se llena repetitivamente de la cadena literal `"undefinedundefinedundefined..."`, corrompiendo la visualización del texto generado. Al culminar el streaming, el contador de palabras notifica erróneamente `0 palabras redactadas`.

## Componente Afectado
`Motor de Redacción Modular & WebSockets (gui/js/drafting.js, src/thesisforge/drafting/service.py)`

## Pasos para Reproducir
1. Iniciar el servidor con `thesisforge run`.
2. Crear o seleccionar un proyecto y avanzar a la pestaña **Redacción**.
3. Seleccionar cualquier sección (ej. `sec_1_1`) y hacer clic en **"Generar con IA (Streaming)"**.
4. Observar el área de texto del editor mientras llegan los tokens del modelo LLM.

## Comportamiento Esperado vs. Actual
- **Esperado**: Cada token generado por el LLM debe concatenarse suavemente al contenido del editor en tiempo real, y al finalizar debe mostrar el texto limpio y el número real de palabras.
- **Actual**: Se concatena la palabra `"undefined"` por cada token recibido. Al finalizar, la sección queda corrupta o en blanco.

## Causa Raíz
En `src/thesisforge/drafting/service.py` (líneas 226 y 241), el generador asíncrono emite:
```python
yield {"event": "token", "data": token}
yield {"event": "complete", "section": section.model_dump(mode="json")}
```

Sin embargo, en `gui/js/drafting.js` (líneas 162-169):
```javascript
if (data.event === 'token') {
    this.streamingTokens += data.token; // ERROR: data.token no existe, es data.data
    this.editorContent = this.streamingTokens;
} else if (data.event === 'complete') {
    this.editorContent = data.content || this.streamingTokens; // ERROR: data.content no existe, es data.section.content
    Alpine.store('app').toast('success', 'Generación Completada', `Se redactaron ${data.word_count || 0} palabras.`); // ERROR: es data.section.word_count
}
```

## Solución Propuesta
Actualizar `gui/js/drafting.js` para normalizar y leer las propiedades correctas del payload:
```javascript
if (data.event === 'token') {
    const chunk = data.data ?? data.token ?? '';
    this.streamingTokens += chunk;
    this.editorContent = this.streamingTokens;
} else if (data.event === 'complete') {
    const sectionData = data.section || data;
    this.editorContent = sectionData.content || this.streamingTokens;
    this.isStreaming = false;
    this.wsSocket = null;
    Alpine.store('app').toast('success', 'Generación Completada', `Se redactaron ${sectionData.word_count || 0} palabras.`);
    this.loadSections();
}
```
