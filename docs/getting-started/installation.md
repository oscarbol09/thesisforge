# Guía de Instalación

ThesisForge ofrece múltiples opciones de instalación según tu entorno y flujo de trabajo:

---

## 1. Vía PyPI / Pip (Recomendado para Pythonistas)

```bash
# Instalar paquete oficial
pip install thesisforge

# Iniciar servidor y abrir en navegador
thesisforge run
```

---

## 2. Vía uv (Entorno de Desarrollo Rápido)

```bash
# 1. Clonar el repositorio
git clone https://github.com/oscarbol09/thesisforge.git
cd thesisforge

# 2. Crear entorno virtual
uv venv .venv
# En Linux/macOS:
source .venv/bin/activate
# En Windows (PowerShell):
.venv\Scripts\activate

# 3. Instalar dependencias en modo editable con herramientas de desarrollo
uv pip install -e ".[dev]"
```

---

## 3. Vía Docker & Docker Compose (Self-Hosted)

Si deseas desplegar ThesisForge en un servidor personal o VPS:

```bash
# Clonar y levantar
git clone https://github.com/oscarbol09/thesisforge.git
cd thesisforge
docker compose up -d
```

El servicio estará disponible en `http://localhost:8000`.

---

## 4. Ejecutable de Escritorio Standalone (.exe / .dmg)

Para usuarios no técnicos o investigadores que prefieren una aplicación tradicional:
1. Ve a la sección [Releases en GitHub](https://github.com/oscarbol09/thesisforge/releases).
2. Descarga el instalador correspondiente a tu sistema operativo (`ThesisForge-Windows-x64.exe` o `ThesisForge-macOS.dmg`).
3. Ejecuta la aplicación. No requiere instalar Python ni dependencias externas.
