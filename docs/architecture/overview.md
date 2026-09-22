# Arquitectura del Sistema

ThesisForge está diseñado bajo principios de software para ingeniería de producción, con separación estricta de responsabilidades, tipado estático riguroso y concurrencia asíncrona no bloqueante.

---

## Patrón Arquitectónico en 4 Capas

```mermaid
flowchart TD
    subgraph CapaPresentacion [1. Capa de Presentación & CLI]
        GUI[Desktop GUI - PyWebView]
        WEB[Web Client - SPA Tailwind]
        CLI[CLI - rich & argparse]
    end

    subgraph CapaAPI [2. Capa API, WebSockets y Routers]
        ROUTERS[FastAPI Routers - Pydantic DTOs]
        WS[WebSocket Hub - Drafting & Defense]
    end

    subgraph CapaServicios [3. Servicios y Lógica de Dominio]
        ADV[AdvisorService]
        RAG[RAGService]
        DRAFT[DraftService]
        EXP[ExportService]
        JURY[JuryService - MultiAgentJuryEngine & DefenseSimulator]
        ROUTER[LLMRouter]
    end

    subgraph CapaPersistencia [4. Persistencia y Seguridad]
        DB[(Async SQLite - aiosqlite WAL)]
        CHROMA[(ChromaDB Vector Store)]
        VAULT[KeyVault - Fernet 256-bit]
        SSRF[SSRFGuard]
        LOG[StructuredLogger]
    end

    GUI --> ROUTERS
    WEB --> ROUTERS
    CLI --> ROUTERS
    ROUTERS --> ADV
    ROUTERS --> RAG
    ROUTERS --> DRAFT
    ROUTERS --> EXP
    ROUTERS --> JURY
    WS --> DRAFT
    WS --> JURY
    ADV --> ROUTER
    DRAFT --> ROUTER
    JURY --> ROUTER
    ADV --> DB
    RAG --> DB
    DRAFT --> DB
    JURY --> DB
    RAG --> CHROMA
    ROUTER --> VAULT
    RAG --> SSRF
    ROUTERS --> LOG
```

---

## Principios de Diseño

1. **Cero Bloqueo de Event Loop:** Todas las operaciones de red (`httpx.AsyncClient`), bases de datos (`aiosqlite`) y archivos (`aiofiles`) son estrictamente no bloqueantes.
2. **Tipado Estático Riguroso:** Verificación con `mypy --strict` en todo el paquete `src/thesisforge`.
3. **Manejo Estructurado de Errores:** Jerarquía de excepciones de dominio tipadas (`ThesisForgeError`, `MethodologyValidationError`, `JuryEvaluationError`, `DefenseSessionError`, `SecurityError`, etc.) con códigos de error legibles por máquinas.
4. **Fechas UTC:** Manejo exclusivo de fechas y horas conscientes de zona horaria (`datetime.now(timezone.utc)`).
5. **Auditoría Científica Híbrida:** Combinación de validación determinista de consistencia epistemológica (reglas duras) con deliberación cualitativa distribuida en tribunal multi-agente.
