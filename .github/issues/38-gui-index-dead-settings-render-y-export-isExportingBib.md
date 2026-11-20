### Descripción del Problema
Se detectaron cuatro inconsistencias menores en la capa de presentación (`gui/index.html` y `gui/js/export.js`) que provocan llamadas a métodos inexistentes, carga duplicada de scripts, iconos faltantes en notificaciones de advertencia y variables reactivas no declaradas en el estado inicial.

### Evidencia en Código
1. **Llamada a `render()` inexistente en Settings (`gui/index.html`, líneas 311–315):**
   El contenedor de configuración tiene `x-data="settingsComponent()"` pero invoca `x-html="render()"` a pesar de que `gui/js/settings.js` no implementa ningún método `render()`.
2. **Carga duplicada de Tailwind config (`gui/index.html`, líneas 67 y 655):**
   `<script src="js/tailwind-config.js"></script>` se incluye dos veces en el mismo documento HTML.
3. **Icono faltante para toasts `'warning'` (`gui/index.html`, líneas 638–642):**
   La plantilla SVG de los toasts no contempla `t.type === 'warning'`, aunque `gui/js/advisor.js` (líneas 326 y 330) dispara notificaciones de tipo `'warning'`.
4. **Propiedad `isExportingBib` no declarada en el estado inicial (`gui/js/export.js`, líneas 6–25, 78 y 150–155):**
   `export.js` lee y muta `isExportingBib` en plantilla y métodos (líneas 78 y 150–155), pero omite declararla (`isExportingBib: false`) en el objeto retornado por `exportComponent()`.

### Solución Esperada (Good First Issue)
1. Eliminar la directiva muerta `x-html="render()"` del contenedor de `settingsComponent()` en `gui/index.html` (líneas 311–315) o definir el comportamiento esperado si se migra a renderizado dinámico.
2. Eliminar la inclusión duplicada de `js/tailwind-config.js` en `gui/index.html`.
3. Añadir la rama `t.type === 'warning'` en el `<template>` de iconos SVG del sistema de toasts en `gui/index.html`.
4. Declarar `isExportingBib: false` dentro del estado inicial de `exportComponent()` en `gui/js/export.js` (líneas 6–25).
