<div align="center">

# 🔨 ThesisForge

### Asistente y Forjador de Investigación Académica con IA, RAG y BYOK

[![CI Quality Gate](https://github.com/oscarbol09/thesisforge/actions/workflows/ci.yml/badge.svg)](https://github.com/oscarbol09/thesisforge/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/type_checked-mypy_strict-brightgreen.svg)](https://mypy.readthedocs.io/)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Good First Issues](https://img.shields.io/github/issues/oscarbol09/thesisforge/good%20first%20issue?color=purple&label=good%20first%20issues)](https://github.com/oscarbol09/thesisforge/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)

**Cero citas inventadas • Orientación metodológica paso a paso • Exportación nativa APA 7ª edición • 100% BYOK y Local-First**

[Documentación](https://oscarbol09.github.io/thesisforge/) • [Inicio Rápido](#-inicio-rápido) • [Arquitectura](ARCHITECTURE.md) • [Roadmap](ROADMAP.md) • [Reportar Bug](https://github.com/oscarbol09/thesisforge/issues/new/choose)

---

</div>

<!-- DEMO PREVIEW -->
<p align="center">
  <img src="docs/assets/demo.gif" alt="ThesisForge Demo Workflow" width="850" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);" onerror="this.style.display='none'">
</p>
<p align="center">
  <em>De la pregunta de investigación a la exportación en Word APA 7 en minutos, con literatura real indexada de Semantic Scholar y ArXiv.</em>
</p>

---

## 🎯 ¿Por Qué ThesisForge?

Los estudiantes de pregrado, posgrado e investigadores enfrentan **tres fricciones críticas** al usar IA genérica en el ámbito académico:

1. **Enfoque Metodológico Débil:** Dificultad para formular preguntas formales, hipótesis y objetivos delimitados que respeten la taxonomía científica.
2. **Citas Inventadas y Alucinaciones:** Los chatbots comerciales inventan papers y DOIs inexistentes, destruyendo el rigor académico.
3. **Inconsistencia entre Capítulos:** Generar textos extensos en un solo prompt degrada el contexto, desconectando la metodología de los objetivos.

**ThesisForge** forja el proyecto de investigación a través de un flujo estructurado:  
$$\text{Orientación Metodológica (Entrevista)} \longrightarrow \text{Contextualización (RAG Científico)} \longrightarrow \text{Redacción Modular por Capítulos (APA 7)}$$

---

## 🆚 Tabla Comparativa vs Alternativas

| Característica | **ThesisForge** | **NotebookLM** | **Jenni AI / SciSpace** | **ChatGPT Plus** |
|:---------------|:---------------:|:--------------:|:-----------------------:|:----------------:|
| **Privacidad & BYOK (Tus Propias Keys)** | ✅ **100%** | ❌ Solo Google | ❌ Suscripción cerrada | ❌ Suscripción cerrada |
| **Modelos 100% Locales (Ollama / VLLM)** | ✅ **Soportado** | ❌ | ❌ | ❌ |
| **Entrevista Metodológica Guiada** | ✅ **Máquina de estados** | ❌ Prompt libre | 🟡 Parcial | ❌ Sin estructura |
| **Cero Alucinaciones en Citas** | ✅ **RAG con DOIs reales** | 🟡 Parcial | ✅ | ❌ Alucina referencias |
| **Memoria Modular por Capítulos** | ✅ **Contextual chunking** | ❌ 1 solo chat | 🟡 Parcial | ❌ Pérdida de contexto |
| **Exportación Nativa APA 7 (.docx)** | ✅ **Completa con portada** | ❌ Markdown plano | 🟡 Con pago | ❌ Texto plano |
| **Licencia & Costo** | ✅ **Gratis / Apache 2.0** | Freemium | \$12 – \$30 / mes | \$20 / mes |

---

## 🚀 Inicio Rápido

### Opción 1: Instalación vía Pip (Python 3.10+)

```bash
# 1. Instalar ThesisForge
pip install thesisforge

# 2. Iniciar servidor API y abrir interfaz
thesisforge run
```

### Opción 2: Desarrollo con `uv` (Recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/oscarbol09/thesisforge.git
cd thesisforge

# 2. Crear y activar entorno virtual
uv venv .venv
source .venv/bin/activate    # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias en modo editable
uv pip install -e ".[dev]"

# 4. Iniciar la aplicación
python -m thesisforge.cli run --reload
```

### Opción 3: Despliegue con Docker (Self-Hosted)

```bash
docker compose up -d
```
Accede inmediatamente en `http://localhost:8000`.

---

## 🏗️ Arquitectura del Sistema

ThesisForge aplica una arquitectura estricta en 3 capas unidireccionales y principios de ingeniería para producción:

```mermaid
flowchart TD
    subgraph Presentacion [1. Capa de Presentación]
        DESK[Desktop GUI - PyWebView]
        WEB[Web Client - SPA Tailwind]
    end

    subgraph API [2. Capa API - FastAPI]
        ROUTERS[Routers Tipados - Pydantic v2 DTOs]
        WS[WebSocket Streamer - Tokens en tiempo real]
    end

    subgraph Servicios [3. Capa de Servicios y Dominio]
        ADV[AdvisorService - Asesor Metodológico]
        RAG[RAGService - Semantic Scholar y ArXiv]
        DRAFT[DraftService - Memoria Jerárquica]
        EXP[ExportService - Formateador DOCX APA 7]
        LLM[LLMRouter - Multi-proveedor BYOK]
    end

    subgraph SeguridadPersistencia [4. Seguridad y Persistencia]
        SSRF[SSRFGuard - Filtro Anti-SSRF]
        VAULT[Local KeyVault - Cifrado Fernet 256-bit]
        DB[(SQLite Asíncrono - SQLAlchemy 2.0)]
    end

    DESK --> ROUTERS
    WEB --> ROUTERS
    ROUTERS --> ADV
    ROUTERS --> RAG
    ROUTERS --> DRAFT
    ROUTERS --> EXP
    ADV --> LLM
    DRAFT --> LLM
    RAG --> SSRF
    LLM --> VAULT
    ADV --> DB
    DRAFT --> DB
```

---

## 🛡️ Principios de Ingeniería & Seguridad

- ⚡ **Sin Bloqueo de Event Loop:** Todo el I/O es 100% asíncrono (`httpx.AsyncClient`, `aiofiles`, `aiosqlite`).
- 🛡️ **Defensa contra SSRF:** Verificación de resolución DNS y bloqueo estricto de subredes privadas (`127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`, `169.254.0.0/16`, `::1/128`).
- 🔐 **Bóveda de Claves Local:** Cifrado simétrico Fernet (256 bits) para claves BYOK en reposo dentro de SQLite.
- 🧼 **Sanitización CWE-117:** Logs estructurados inmunes a Log Injection.
- 📊 **Protección contra Formula Injection:** Sanitización de celdas con caracteres de comando (`=`, `+`, `-`, `@`) en exportaciones.
- 🧪 **Testing Hermético:** Pruebas unitarias, de integración con `respx` y pruebas basadas en propiedades con `Hypothesis`.

---

## 🗺️ Roadmap de Desarrollo

- [x] **v0.1.0:** Asesor Metodológico (Máquina de estados), Router BYOK y Core de Seguridad.
- [ ] **v0.2.0:** Motor RAG de literatura real (Semantic Scholar, ArXiv, CrossRef + PDFs locales).
- [ ] **v0.3.0:** Redacción modular por capítulos con memoria acumulativa y exportación DOCX APA 7.
- [ ] **v1.0.0:** Binarios de escritorio standalone (.exe/.dmg), exportador LaTeX y sincronización con Zotero.

Consulta nuestro [ROADMAP.md](ROADMAP.md) para más detalles.

---

## 🤝 Cómo Contribuir

¡Agradecemos enormemente las contribuciones de la comunidad! Revisa nuestra [Guía de Contribución](CONTRIBUTING.md) para conocer las áreas de trabajo prioritarias (nuevos conectores académicos, soporte para estilos IEEE/Vancouver, etc.).

---

## ⭐ Apoya la Investigación Abierta

Si **ThesisForge** te resulta útil para tu tesis, proyecto de grado o investigación, considera darle una ⭐ en GitHub. ¡Ayuda a que más investigadores descubran una alternativa rigurosa, ética y libre de suscripciones!

[![Star on GitHub](https://img.shields.io/github/stars/oscarbol09/thesisforge?style=social)](https://github.com/oscarbol09/thesisforge)

---

## 📄 Licencia

Este proyecto está bajo la Licencia **Apache 2.0**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

Copyright (c) 2026 Oscar Madera / ThesisForge Contributors.
