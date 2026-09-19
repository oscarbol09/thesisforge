# 🔨 ThesisForge

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/type_checked-mypy_strict-brightgreen.svg)](https://mypy.readthedocs.io/)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

> **Asistente y forjador de proyectos de investigación académica con IA, RAG y BYOK.**  
> Diseñado para guiar al estudiante de pregrado y posgrado paso a paso en la formulación metodológica, búsqueda de literatura real indexada y redacción modular de capítulos con formato APA 7ª edición.

---

## 🎯 Visión y Objetivos

ThesisForge resuelve tres problemas estructurales en la investigación asistida por IA:
1. **Enfoque Metodológico Débil:** Guiar mediante una entrevista interactiva estructurada para definir problemas, objetivos, hipótesis y diseños metodológicos sólidos.
2. **Alucinaciones en Referencias:** Cero citas inventadas. Integración directa con Semantic Scholar, ArXiv y CrossRef + indexación local de PDFs vía RAG.
3. **Inconsistencia entre Capítulos:** Generación modular con memoria acumulativa jerárquica (chunking contextual por capítulos).

---

## 🏗️ Arquitectura del Sistema

```text
ThesisForge
├── Presentation Layer: Desktop GUI (PyWebView) & Web SPA (Tailwind + Alpine.js)
├── API Layer: FastAPI con endpoints tipados (Pydantic v2 DTOs) + WebSockets
├── Service Layer:
│   ├── AdvisorService (Entrevista guiada y máquina de estados)
│   ├── RAGService (Búsqueda académica, chunking léxico y vector store)
│   ├── DraftService (Generación modular con memoria acumulativa)
│   └── ExportService (Compilación DOCX APA 7 y sanitización de fórmulas)
├── Security & Core:
│   ├── SSRF Guard (Validación de subredes e IPs privadas)
│   ├── LocalKeyVault (Cifrado simétrico Fernet para API keys locales)
│   └── Structured Logger (Sanitización CWE-117 contra Log Injection)
└── Persistence Layer: SQLite Asíncrono (aiosqlite / SQLAlchemy 2.0)
```

---

## 🚀 Inicio Rápido

### Prerrequisitos
- Python `>= 3.10`
- [uv](https://github.com/astral-sh/uv) (recomendado) o `pip`

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/oscarbol09/thesisforge.git
cd thesisforge

# 2. Crear y activar entorno virtual con uv
uv venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux / macOS:
source .venv/bin/activate

# 3. Instalar dependencias en modo editable con herramientas de desarrollo
uv pip install -e ".[dev]"

# 4. Configurar variables de entorno
cp .env.example .env
cp config.yaml.example config.yaml
```

### Ejecutar Pruebas y Control de Calidad

```bash
# Ejecutar suite de pruebas con pytest
pytest tests/ -v --cov=thesisforge

# Linter y chequeo de tipos estricto
ruff check src/ tests/
mypy --strict src/

# Auditoría SAST
bandit -r src/ -ll
```

---

## 🛡️ Seguridad y Principios de Ingeniería

- **Sin bloqueo de Event Loop:** Todo el I/O es asíncrono (`httpx.AsyncClient`, `aiofiles`, `aiosqlite`).
- **Defensa contra SSRF:** Toda URL externa es verificada contra rangos IP reservados (`127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`, `169.254.0.0/16`, etc.).
- **Bóveda de Claves Local:** Cifrado simétrico Fernet de 256 bits para claves BYOK en reposo.
- **Fechas UTC Estrictas:** Timestamps basados en `datetime.now(timezone.utc)`.

---

## 📄 Licencia

Este proyecto está bajo la Licencia **Apache 2.0**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

Copyright (c) 2026 Oscar Madera / ThesisForge Contributors.
