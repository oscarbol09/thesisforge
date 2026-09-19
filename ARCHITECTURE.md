# ThesisForge Architecture Deep Dive 🏗️

This document details the architectural design, security boundaries, and data flow of **ThesisForge**.

---

## 1. High-Level Architecture Overview

ThesisForge is built as a modular, local-first research platform with a strict **Three-Layer Unidirectional Architecture**:

```mermaid
flowchart TD
    subgraph Presentacion [1. Capa de Presentación]
        DESK[Desktop GUI - PyWebView]
        WEB[Web Browser - SPA Tailwind]
    end

    subgraph API [2. Capa API y Controladores - FastAPI]
        ROUTERS[Routers Tipados - Pydantic v2 DTOs]
        WS[WebSocket Streamer - Tokens en tiempo real]
    end

    subgraph Servicios [3. Capa de Dominio y Servicios]
        ADV[AdvisorService - Asesor Metodológico]
        RAG[RAGService - Semantic Scholar y ArXiv]
        DRAFT[DraftService - Memoria Jerárquica Contextual]
        EXP[ExportService - Formateador APA 7 y LaTeX]
        LLM[LLMRouter - Multi-proveedor BYOK]
    end

    subgraph CoreSeguridad [4. Seguridad y Persistencia]
        SSRF[SSRFGuard - Filtro Anti-SSRF]
        VAULT[KeyStoreRepository - Cifrado Fernet 256-bit]
        LOGGER[StructuredLogger - Sanitizador CWE-117]
        DB[(SQLite Asíncrono - SQLAlchemy 2.0)]
    end

    DESK --> ROUTERS
    WEB --> ROUTERS
    ROUTERS --> ADV
    ROUTERS --> RAG
    ROUTERS --> DRAFT
    ROUTERS --> EXP
    ROUTERS --> LOGGER
    ADV --> LLM
    DRAFT --> LLM
    RAG --> SSRF
    LLM --> VAULT
    ADV --> DB
    DRAFT --> DB
    RAG --> DB
```

---

## 2. Methodological Advisor State Machine

The research formulation workflow enforces methodological consistency using a strict deterministic state machine:

```mermaid
stateDiagram-v2
    [*] --> TOPIC_SELECTION: Project Created
    TOPIC_SELECTION --> PROBLEM_FORMULATION: Topic & Scope Defined
    PROBLEM_FORMULATION --> OBJECTIVES_ALIGNMENT: Problem Statement Validated
    OBJECTIVES_ALIGNMENT --> HYPOTHESIS_VARIABLES: Objectives (General & Specific) Aligned
    HYPOTHESIS_VARIABLES --> METHODOLOGICAL_DESIGN: Variables & Indicators Defined
    METHODOLOGICAL_DESIGN --> COMPLETED: Methodology Validated
    COMPLETED --> [*]: Ready for Literature RAG & Chapter Drafting

    note right of OBJECTIVES_ALIGNMENT
        Validates Bloom's taxonomy verbs 
        and alignment with problem statement
    end note
```

---

## 3. Anti-Hallucination Literature RAG Pipeline

To prevent fabricated citations and non-existent DOIs, ThesisForge implements a dual-verification retrieval pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor User as Researcher
    participant Draft as DraftService
    participant RAG as RAGService
    participant SSRF as SSRFGuard
    participant Ext as Semantic Scholar / ArXiv API
    participant VStore as Local Vector Store (PDFs)
    participant LLM as LLMRouter (BYOK)

    User->>Draft: Request Chapter Draft (e.g. Chapter 1)
    Draft->>RAG: Fetch verified sources for chapter topics
    RAG->>SSRF: Validate API & download URLs
    SSRF-->>RAG: URL verified (non-private IP)
    RAG->>Ext: Search indexed papers & fetch DOIs / abstracts
    RAG->>VStore: Query local indexed PDFs (hybrid lexical + vector)
    RAG-->>Draft: Return structured verified literature citations
    Draft->>LLM: Generate text with strict source grounding prompt
    LLM-->>Draft: Stream draft with verified parenthetical citations [Smith, 2024]
    Draft-->>User: Output chapter with zero hallucinated references
```

---

## 4. Security & Defense-in-Depth

### 4.1 Server-Side Request Forgery (SSRF) Guard
- All outgoing network requests initiated when downloading research papers or interacting with custom LLM endpoints pass through `SSRFGuard.validate_url()`.
- Resolves DNS hostname to IP address prior to connection.
- Rejects connections if the target IP falls into private or restricted subnets (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1/128`).

### 4.2 Local Key Vault Encryption
- User-provided BYOK API keys (OpenAI, Anthropic, Gemini, OpenRouter) are encrypted at rest using 256-bit symmetric Fernet encryption before persisting to SQLite.
- Keys are decrypted only transiently in memory during request dispatching.

### 4.3 Log Injection (CWE-117) & Formula Injection Defense
- User input is sanitized to remove CR/LF characters before writing to logs.
- Document and tabular export routines prefix formula triggers (`=`, `+`, `-`, `@`) with apostrophes to protect researchers opening files in Microsoft Word or Excel.
