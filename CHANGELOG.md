# Changelog 📜

All notable changes to **ThesisForge** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- GitHub Community health files (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `ROADMAP.md`, `SUPPORT.md`, `ARCHITECTURE.md`).
- Structured GitHub Issue and Pull Request templates.
- Release workflow with PyInstaller desktop packaging and automated GitHub Releases.
- Documentation portal configuration with MkDocs Material.
- Multi-stage `Dockerfile` and `docker-compose.yml` for self-hosted deployment.
- CLI script entry point (`thesisforge`) in `pyproject.toml`.

---

## [0.1.0] - 2026-09-18

### Added
- **Advisor Engine:** State-machine based Methodological Advisor (`AdvisorStateMachine`, `AdvisorService`) validating research problem statements, objectives, and hypotheses.
- **LLM Router:** Pluggable multi-provider BYOK (Bring Your Own Key) router supporting OpenRouter, Gemini, Groq, Ollama, and OpenAI-compatible endpoints with tenacity-based retries and fallbacks.
- **Security & Core:**
  - `SSRFGuard`: DNS-resolving security guard preventing Server-Side Request Forgery against private/reserved subnets.
  - `KeyStoreRepository`: Symmetric 256-bit Fernet encryption for local user API keys.
  - `StructuredLogger`: Log sanitization removing `\r` and `\n` to prevent Log Injection (CWE-117).
  - Time utilities enforcing timezone-aware UTC timestamps.
- **FastAPI Layer:** REST API endpoints (`/api/projects`, `/api/advisor`) with strict Pydantic v2 schemas and error handlers.
- **Persistence Layer:** Asynchronous SQLite storage via SQLAlchemy 2.0 and `aiosqlite`.
- **Testing & CI:** Complete hermetic test suite with unit, integration, and Hypothesis property-based testing running on Ubuntu and Windows matrices across Python 3.10, 3.11, and 3.12.
