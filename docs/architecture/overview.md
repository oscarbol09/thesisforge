# Arquitectura del Sistema

ThesisForge está diseñado bajo principios de software para ingeniería de producción, con separación estricta de responsabilidades, tipado estático riguroso y concurrencia asíncrona no bloqueante.

---

## Patrón Arquitectónico en 3 Capas

```mermaid
flowchart TD
    subgraph CapaPresentacion [1. Capa de Presentación]
        GUI[Desktop GUI - PyWebView]
        WEB[Web Client - SPA Tailwind]
    end

    subgraph CapaAPI [2. Capa API y Routers]
        ROUTERS[FastAPI Routers - Pydantic DTOs]
    end

    subgraph CapaServicios [3. Servicios y Lógica de Dominio]
        ADV[AdvisorService]
        RAG[RAGService]
        DRAFT[DraftService]
        EXP[ExportService]
        ROUTER[LLMRouter]
    end

    subgraph CapaPersistencia [4. Persistencia y Seguridad]
        DB[(Async SQLite - SQLAlchemy 2.0)]
        VAULT[KeyVault - Fernet 256-bit]
        SSRF[SSRFGuard]
        LOG[StructuredLogger]
    end

    GUI --> ROUTERS
    WEB --> ROUTERS
    ROUTERS --> ADV
    ROUTERS --> RAG
    ROUTERS --> DRAFT
    ROUTERS --> EXP
    ADV --> ROUTER
    DRAFT --> ROUTER
    ADV --> DB
    RAG --> DB
    ROUTER --> VAULT
    RAG --> SSRF
    ROUTERS --> LOG
```

---

## Principios de Diseño

1. **Cero Bloqueo de Event Loop:** Todas las operaciones de red (`httpx.AsyncClient`), bases de datos (`aiosqlite`) y archivos (`aiofiles`) son estrictamente no bloqueantes.
2. **Tipado Estático Riguroso:** Verificación con `mypy --strict` en todo el paquete `src/thesisforge`.
3. **Manejo Estructurado de Errores:** Jerarquía de excepciones de dominio tipadas (`ThesisForgeError`, `MethodologyValidationError`, `SecurityError`, etc.) con códigos de error legibles por máquinas.
4. **Fechas UTC:** Manejo exclusivo de fechas y horas conscientes de zona horaria (`datetime.now(timezone.utc)`).
