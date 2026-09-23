# Guía: Tribunal Académico Multi-Agente y Defensa Socrática

Esta guía detalla el funcionamiento del sistema de evaluación por jurado multi-agente y el simulador de defensa oral socrática introducido en ThesisForge v0.4.0.

---

## 1. El Tribunal Académico Multi-Agente

ThesisForge modela un tribunal colegiado de cuatro examinadores con criterios de evaluación ortogonales y complementarios:

| Jurado | Rol Académico | Foco de Evaluación | Ponderación |
| :--- | :--- | :--- | :---: |
| **Dr. Arístides Valenzuela** | Metodólogo Principal | Consistencia epistemológica, diseño del estudio, hipótesis y objetivos | 35% |
| **Dra. Beatriz Salamanca** | Especialista Temática | Marco conceptual, estado del arte, pertinencia y densidad bibliográfica | 25% |
| **Dr. Camilo Restrepo** | Auditor Estadístico | Muestreo, análisis de datos, potencia estadística e inferencias | 25% |
| **Dr. Demetrio Sotomayor** | Abogado del Diablo | Causalidades espurias, variables confusoras y sesgos argumentativos | 15% |

---

## 2. Motor de Auditoría Científica Híbrida

La auditoría se ejecuta mediante dos capas complementarias:

### A. Reglas Deterministas (Hard Rules)
- **Consistencia Cuantitativa**: Si el enfoque es cuantitativo o mixto, la presencia de hipótesis contrastables es obligatoria.
- **Taxonomía de Objetivos**: Exige la presencia de un objetivo general y al menos un objetivo específico redactados con verbos de desempeño evaluables.
- **Densidad Bibliográfica**: Se comprueba la existencia de citas indexadas bajo norma APA 7ª edición.

### B. Deliberación Cualitativa de LLM
Cada jurado evalúa el proyecto y emite:
- **Puntuación Dimensional (0–100)** con justificación académica fundamentada.
- **Observaciones Tipadas**: Clasificadas por severidad (`CRITICAL`, `MAJOR`, `MINOR`, `NOTE`) y tipo (`METHODOLOGICAL_INCONSISTENCY`, `UNSUPPORTED_CLAIM`, `SAMPLING_BIAS`, `INVALID_INSTRUMENT`, `MISSING_LIMITATIONS`, etc.).

### C. Veredictos Formales y Regla de Veto
- **Aprobado con Distinción** ($\ge 95.0$ puntos y 0 fallos críticos).
- **Aprobado** ($\ge 80.0$ puntos y 0 fallos críticos).
- **Modificaciones Menores** ($\ge 70.0$ puntos y 0 fallos críticos).
- **Modificaciones Mayores** ($\ge 50.0$ puntos o $\ge 3$ fallos mayores).
- **No Aprobado** ($< 50.0$ puntos o presencia de cualquier fallo `CRITICAL`).

---

## 3. Simulador Socrático de Defensa Oral

El simulador permite preparar la sustentación del proyecto frente a réplicas incisivas generadas dinámicamente a partir de los puntos débiles detectados en la auditoría.

### Ciclo de Turnos de Sustentación
1. **Pregunta del Jurado**: Un miembro del tribunal formula una pregunta crítica orientada a una debilidad específica.
2. **Réplica del Tesista**: El estudiante argumenta su respuesta técnica y metodológica.
3. **Evaluación y Feedback**: El jurado califica el desempeño en el turno (0–100) y proporciona sugerencias de mejora inmediata.

### Streaming en Tiempo Real vía WebSockets
La conexión bidireccional `/api/defense/ws/{session_id}` permite interactuar en vivo:

```json
// Enviar respuesta a un turno
{
  "action": "submit_turn",
  "turn_index": 0,
  "student_answer": "El tamaño muestral se calculó considerando un poder estadístico del 80% y un alfa de 0.05 con corrección de Bonferroni."
}
```

---

## 4. Comandos de Consola (CLI)

```bash
# Auditar proyecto y generar acta formal
thesisforge jury-audit --project-id "proj_123" --save

# Iniciar defensa socrática interactiva de 4 turnos
thesisforge defense-start --project-id "proj_123" --turns 4
```
