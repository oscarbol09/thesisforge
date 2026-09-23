# Guía de Contribución a ThesisForge

Gracias por tu interés en contribuir a **ThesisForge**. El objetivo de este proyecto es ofrecer a estudiantes e investigadores hispanohablantes una herramienta rigurosa, ética y transparente para estructurar trabajos de grado e investigaciones académicas asistidas por IA.

---

## Código de Conducta

Al participar en este proyecto, te comprometes a respetar nuestro [Código de Conducta](https://github.com/oscarbol09/thesisforge/blob/main/CODE_OF_CONDUCT.md). Cualquier comportamiento que vulnere un ambiente de respeto debe reportarse directamente al mantenedor del repositorio.

---

## Áreas Abiertas de Contribución

Aceptamos activamente contribuciones en las siguientes áreas técnicas:

1. **Conectores de literatura académica:** Integración de nuevos motores de búsqueda abierta (por ejemplo, OpenAlex, PubMed Central, Europe PMC, IEEE Xplore, DOAJ, Scielo o Redalyc).
2. **Motores de exportación:** Generación de formatos adicionales como LaTeX / Overleaf (`.tex` y `.bib`) o Markdown estructurado junto con el pipeline actual de Word APA 7 (`.docx`).
3. **Estilos de citación:** Soporte para normas adicionales como IEEE, Vancouver, Chicago o Harvard.
4. **Gestores bibliográficos:** Sincronización local con bibliotecas de Zotero o Mendeley.
5. **Asesor metodológico:** Ampliación del árbol de validación y preguntas para diseños experimentales, cualitativos puros o estudios etnográficos.

Revisa los problemas marcados con las etiquetas [`good first issue`](https://github.com/oscarbol09/thesisforge/labels/good%20first%20issue) o [`help wanted`](https://github.com/oscarbol09/thesisforge/labels/help%20wanted). También puedes consultar nuestro [Catálogo de Primeros Issues](guides/GOOD_FIRST_ISSUES.md) para ver tareas listas para implementar.

---

## Configuración del Entorno de Desarrollo

### Requisitos previos
- **Python:** `>= 3.10`
- **Gestor de paquetes:** [`uv`](https://github.com/astral-sh/uv) (recomendado) o `pip`
- **Git**

### Pasos de instalación

```bash
# 1. Clona tu bifurcación (fork) del repositorio:
git clone https://github.com/<tu-usuario>/thesisforge.git
cd thesisforge

# 2. Crea y activa el entorno virtual con uv:
uv venv .venv

# En Linux / macOS:
source .venv/bin/activate
# En Windows (PowerShell):
.venv\Scripts\activate

# 3. Instala las dependencias y herramientas de desarrollo en modo editable:
uv pip install -e ".[dev,docs]"

# 4. Configura los archivos de entorno iniciales:
cp .env.example .env
cp config.yaml.example config.yaml
```

---

## Principios de Ingeniería y Calidad

Para mantener un estándar de código profesional y evitar patrones de código autogenerado de baja calidad, toda contribución debe cumplir con:

### 1. I/O Asíncrono No Bloqueante
- **Prohibido** bloquear el bucle de eventos (`Event Loop`) en funciones `async def` mediante llamadas síncronas o `time.sleep()`.
- Utiliza siempre `httpx.AsyncClient`, `asyncio.sleep()` y `aiofiles`.

### 2. Manejo Estricto de Marcas de Tiempo UTC
- **Prohibido** el uso de `datetime.now()` sin zona horaria. Emplea exclusivamente `datetime.now(timezone.utc)` o las utilidades de `thesisforge.core.time`.

### 3. Seguridad de Aplicaciones (AppSec)
- **Defensa SSRF Dual-Stack:** Toda URL externa procesada para descargar literatura o PDFs debe validar su resolución DNS contra rangos privados (`127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`, `169.254.0.0/16`, `::1/128`, etc.) y direcciones IPv4-mapped en IPv6 mediante `assert_safe_academic_url`.
- **Inyección de Logs (CWE-117):** Sanitiza retornos de carro (`\r`, `\n`) antes de registrar entradas de usuario y nunca imprimas claves de API o tokens en texto plano.
- **Inyección de Fórmulas (CWE-1236):** Prefija con un apóstrofe (`'`) cualquier celda de tabla exportada que inicie con `=`, `+`, `-`, `@`, `|` o tabulaciones.

### 4. Arquitectura en Capas
Respeta el flujo de dependencias unidireccional:
$$\text{Routers (DTOs)} \longrightarrow \text{Servicios (Lógica de Dominio)} \longrightarrow \text{Repositorios (Persistencia / SQLite)}$$

---

## Pasos para Enviar un Pull Request

1. **Crea una rama descriptiva para tu cambio:**
   ```bash
   git checkout -b feat/conector-openalex
   # o
   git checkout -b fix/resolucion-dns-ssrf
   ```
2. **Usa la convención de Conventional Commits (en inglés):**
   - `feat: add OpenAlex literature client with async httpx transport`
   - `fix: prevent duplicate DOI insertion in project bibliography`
   - `docs: update BYOK configuration guide for local Ollama`
   - `test: add hypothesis property tests for APA 7 reference formatter`
3. **Ejecuta las compuertas de calidad locales antes de enviar el PR:**
   ```bash
   # Suite de pruebas con reporte de cobertura
   pytest tests/ -v --cov=thesisforge --cov-report=term-missing

   # Análisis estático de tipos
   mypy --strict src/

   # Linter y formato de código
   ruff check src/ tests/
   ruff format --check src/ tests/

   # Auditoría de seguridad SAST
   bandit -r src/ -ll
   ```
4. **Abre el Pull Request en GitHub:** Completa la plantilla de PR detallando el contexto y la motivación del cambio.
