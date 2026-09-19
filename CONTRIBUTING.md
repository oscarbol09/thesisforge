# Contributing to ThesisForge 🔨

First off, thank you for considering contributing to **ThesisForge**! It's people like you that make ThesisForge a great, ethical, and rigorous tool for students and researchers around the world.

Please take a moment to review this document to ensure a smooth and productive collaboration.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any unacceptable behavior to the project maintainers.

---

## How Can I Contribute?

### 1. Open Contribution Areas (High Priority 🌟)

We actively welcome contributions in the following areas:
- **Academic Source Connectors:** Adding new literature search drivers (e.g., PubMed, IEEE Xplore, DOAJ, OpenAlex, Scopus).
- **Export Formats:** Implementing LaTeX / Overleaf (`.tex` + `.bib`) or Markdown exports alongside our APA 7 `.docx` pipeline.
- **Citation Styles:** Adding support for IEEE, Vancouver, Chicago, or Harvard citation styles.
- **Reference Managers:** Local integrations with Zotero or Mendeley APIs.
- **Internationalization (i18n):** Translating the UI strings into additional languages (Portuguese, French, German, etc.).
- **Methodological Advisors:** Expanding guided question trees for qualitative, quantitative, mixed, and experimental research designs.

Check out our issues labeled [`good first issue`](https://github.com/oscarbol09/thesisforge/labels/good%20first%20issue) or [`help wanted`](https://github.com/oscarbol09/thesisforge/labels/help%20wanted).

---

## Development Setup

### Prerequisites
- **Python:** `>= 3.10`
- **Package Manager:** [`uv`](https://github.com/astral-sh/uv) (strongly recommended) or `pip`
- **Git**

### Step-by-Step Setup

```bash
# 1. Fork the repository on GitHub and clone your fork:
git clone https://github.com/<your-username>/thesisforge.git
cd thesisforge

# 2. Create and activate a virtual environment with uv:
uv venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\activate

# 3. Install dependencies with dev tools in editable mode:
uv pip install -e ".[dev]"

# 4. Copy environment configuration:
cp .env.example .env
cp config.yaml.example config.yaml
```

---

## Development & Engineering Principles

To maintain staff-level software quality and eliminate AI-generated code smells, all contributions must strictly adhere to these principles:

### 1. Strict Async Non-Blocking I/O
- **NEVER** block the event loop in `async def` with `requests.get()`, `time.sleep()`, or synchronous file I/O.
- Always use `httpx.AsyncClient`, `asyncio.sleep()`, and `aiofiles`.

### 2. Strict UTC Timestamps
- **NEVER** use naive `datetime.now()`. Always use timezone-aware `datetime.now(timezone.utc)`.

### 3. Application Security & AppSec
- **SSRF Defense:** All external URLs fetched for papers or PDFs must resolve DNS and be verified against private IP ranges (`127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`, `169.254.0.0/16`, etc.) using our `SSRFGuard`.
- **Log Injection (CWE-117):** Sanitize carriage returns (`\r`, `\n`) and never log raw API keys or tokens.
- **Formula Injection Defense:** Prefix spreadsheet/table cells starting with `=`, `+`, `-`, `@` with an apostrophe (`'`).

### 4. Layered Architecture
Maintain strict one-way dependency flow:
$$\text{API Routers (DTOs)} \longrightarrow \text{Services (Domain Logic)} \longrightarrow \text{Repositories (Persistence)}$$

---

## Running Tests & Quality Gates

Before submitting any Pull Request, ensure all quality gates pass:

```bash
# 1. Run the hermetic test suite with coverage:
pytest tests/ -v --cov=thesisforge

# 2. Check formatting and linting:
ruff check src/ tests/
ruff format --check src/ tests/

# 3. Strict static type analysis:
mypy --strict src/

# 4. Security SAST audit:
bandit -r src/ -ll
```

---

## Pull Request Guidelines

1. **Create a descriptive feature branch:**
   ```bash
   git checkout -b feat/pubmed-connector
   # or
   git checkout -b fix/ssrf-dns-resolution
   ```
2. **Follow Conventional Commits:**
   - `feat: add PubMed literature fetcher with async httpx client`
   - `fix: prevent duplicate DOI insertion in project bibliography`
   - `docs: update BYOK configuration guide for local Ollama`
   - `test: add hypothesis property tests for APA 7 reference formatter`
3. **Include tests:** Every new feature or bug fix must be covered by hermetic tests.
4. **Open a PR:** Fill out our [PR Template](.github/PULL_REQUEST_TEMPLATE.md) and link the relevant issue.

---

## Community & Questions

- **Discussions:** Use [GitHub Discussions](https://github.com/oscarbol09/thesisforge/discussions) for general questions, feature brainstorming, or methodology design discussions.
- **Issues:** Use [GitHub Issues](https://github.com/oscarbol09/thesisforge/issues) for reproducible bug reports or structured RFCs.

Thank you for building ThesisForge with us! 🚀
