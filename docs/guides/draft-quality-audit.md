# Auditoría de Calidad de Prosa Académica

ThesisForge v0.6.0 incorpora el módulo `src/thesisforge/drafting/detox.py`, que detecta y corrige patrones de escritura sint\u00e9tica generados por IA en los borradores académicos.

El objetivo es garantizar que el texto enviado al tribunal y publicado en el DOCX final tenga registro académico auténtico, ritmo sintáctico variado y citas con anclaje empírico profundo (nivel L3).

---

## 1. Auditoría: `audit_scholarly_draft()`

La función principal analiza un bloque de texto y devuelve un `DraftQualityAuditResult` con:

### Dimensiones evaluadas

| Dimensión | Métrica calculada | Penalización |
| :--- | :--- | :--- |
| **Densidad de IA-slop** | Ocurrencias por 1 000 palabras | Hasta −40 puntos |
| **Ritmo sintáctico** | Desviación estándar de longitud de oraciones | −15 puntos si es monótono |
| **Cobertura de citas L3** | Proporción de citas con localizador explícito | Hasta −20 puntos si < 30 % |

El **puntaje final** va de 0 a 100. Un borrador con puntaje ≥ 80 puede considerarse listo para revisión del asesor.

### Patrones de IA-slop detectados (bilingüe)

| Categoría | Ejemplos detectados |
| :--- | :--- |
| `ai_cliche_en` | *pivotal role*, *delve into*, *tapestry of*, *beacon of* |
| `ai_cliche_es` | *un papel fundamental*, *pieza fundamental*, *tapiz de* |
| `boilerplate_filler` | *cabe destacar que*, *es importante resaltar que*, *vale la pena mencionar que* |
| `formulaic_closure` | *en resumen,*, *en conclusión,*, *a modo de conclusión,* |
| `hyperbole` | *game changer*, *paradigma transformador*, *revolucionar el campo* |
| `hedging_fog` | *se podría argumentar que potencialmente*, *uno podría considerar la posibilidad de que* |

### Citas L3 — ¿qué son?

Una cita de **nivel L3** incluye un localizador específico dentro de la fuente:

- `(González, 2023, p. 45)` — con número de página
- `(Smith et al., 2021, pp. 112-115)` — con rango de páginas
- `(Hernández, 2022, párr. 3)` — con párrafo
- `(Torres, 2020, sec. 2.1)` — con sección

Una cita sin localizador como `(González, 2023)` es estándar (L1/L2) pero no ancla la afirmación a un fragmento específico. El auditor reporta la proporción L3 y recomienda aumentarla por encima del 50 % en secciones con afirmaciones empíricas clave.

### Ejemplo de uso

```python
from thesisforge.drafting.detox import audit_scholarly_draft

texto = """
Cabe destacar que el machine learning juega un papel fundamental en la transformación
del sector salud. Es importante resaltar que esta tecnología es un game changer que
revolucionará el campo de la medicina. En resumen, los resultados demuestran un avance
significativo (García, 2023).
"""

resultado = audit_scholarly_draft(texto)

print(f"Puntaje: {resultado.score}/100")
print(f"Instancias de IA-slop: {resultado.slop_count}")
print(f"Densidad: {resultado.slop_density_per_1k:.1f} por 1 000 palabras")
print(f"Ritmo monótono: {resultado.is_rhythm_monotonous}")
print(f"Cobertura L3: {resultado.l3_coverage_ratio:.0%}")

for rec in resultado.recommendations:
    print(f"→ {rec}")
```

Salida esperada para el texto anterior:

```
Puntaje: 44.0/100
Instancias de IA-slop: 5
Densidad: 125.0 por 1 000 palabras
Ritmo monótono: False
Cobertura L3: 0%
→ Se detectaron 5 instancias de lenguaje sintético/clichés de IA. Reemplace muletillas...
→ Mejore el anclaje de citas a nivel L3: incluya localizadores específicos...
```

---

## 2. Desintoxicación determinista: `detoxify_text()`

La función `detoxify_text()` realiza una limpieza automática y no destructiva del texto, eliminando las muletillas meta-discursivas más frecuentes sin alterar el contenido empírico:

| Patrón eliminado | Transformación |
| :--- | :--- |
| `Cabe destacar que X` | `X` (con X en mayúscula) |
| `Es importante resaltar que X` | `X` |
| `Vale la pena mencionar que X` | `X` |
| `Es imperativo subrayar que X` | `X` |
| `En resumen, X` | `X` |
| `En conclusión, X` | `X` |
| `A modo de conclusión, X` | `X` |

La función **no** reemplaza clichés temáticos como *papel fundamental* o *game changer* — esos requieren intervención humana con criterio semántico. Para esos usa el reporte de `audit_scholarly_draft()` con la lista de `slop_occurrences`.

```python
from thesisforge.drafting.detox import detoxify_text

texto_original = "Cabe destacar que los resultados muestran una mejora significativa del 23%."
texto_limpio = detoxify_text(texto_original)
# → "Los resultados muestran una mejora significativa del 23%."
```

---

## 3. Acceso vía API REST

```bash
# Auditar la calidad de una sección específica
GET /api/drafting/projects/{project_id}/sections/{section_id}/quality-audit
```

Respuesta:

```json
{
  "score": 72.5,
  "word_count": 480,
  "slop_count": 2,
  "slop_density_per_1k": 4.2,
  "sentence_count": 18,
  "mean_sentence_length": 26.7,
  "sentence_length_std_dev": 3.1,
  "is_rhythm_monotonous": true,
  "standard_citations_count": 6,
  "l3_locator_citations_count": 1,
  "l3_coverage_ratio": 0.14,
  "recommendations": [
    "Se detectaron 2 instancias de lenguaje sintético...",
    "El ritmo sintáctico es monótono...",
    "Mejore el anclaje de citas a nivel L3..."
  ]
}
```

---

## 4. Flujo de trabajo recomendado

```
Generar borrador (DraftService)
        │
        ▼
Auditar con audit_scholarly_draft()   ← puntaje < 80?
        │                                      │
        │ puntaje ≥ 80                         ▼
        │                         Aplicar detoxify_text()
        │                         + Revisar slop_occurrences manualmente
        │                         + Añadir localizadores L3 a citas clave
        │                                      │
        ▼                                      ▼
Aprobar sección (DraftService.approve_section)
```
