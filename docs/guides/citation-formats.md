# Formatos de Citación: IEEE y Vancouver

ThesisForge soporta tres normativas de citación académica. Además del formato APA 7ª edición (descrito en [Exportación APA 7](apa7-export.md)), la v0.6.0 incorpora formateadores completos para **IEEE** y **Vancouver/NLM**.

---

## 1. Formateador IEEE (`IEEEFormatter`)

Implementado en `src/thesisforge/rag/ieee_formatter.py`. Sigue estrictamente las directrices del *IEEE Editorial Style Manual* con citas numéricas entre corchetes.

### Formato de citas en el texto

| Situación | Ejemplo |
| :--- | :--- |
| Cita básica | `[1]` |
| Cita con página | `[1, p. 25]` |
| Cita con rango de páginas | `[1, pp. 25-26]` |

### Formato de citas narrativas

| Autores | Ejemplo |
| :--- | :--- |
| 1 autor | `Smith [1]` |
| 2 autores | `Smith and Jones [1]` |
| 3+ autores | `Smith et al. [1]` |

### Formato de entradas bibliográficas

Estructura general:

```
[1] J. K. Author and A. B. Coauthor, "Título del artículo," *Nombre de la Revista*, 2024. doi: 10.xxxx/yyyy.
```

Reglas especiales:

- **Hasta 6 autores:** se listan todos en formato `Iniciales. Apellido`.
- **Más de 6 autores:** se lista solo el primero seguido de `et al.`
- **Autores corporativos** (organizaciones, instituciones, acrónimos como IEEE, WHO, NASA): se escriben tal cual, sin inversión de nombre.
- El título del artículo va entre comillas dobles; el nombre de la revista en *cursiva*.

### Uso programático

```python
from thesisforge.rag.ieee_formatter import IEEEFormatter
from thesisforge.models import CitationDTO

citation = CitationDTO(
    id="doc-001",
    title="Deep Learning for Medical Image Analysis",
    authors=["Litjens, Geert", "Kooi, Thijs", "Bejnordi, Babak Ehteshami"],
    year=2017,
    journal="Medical Image Analysis",
    doi="10.1016/j.media.2017.07.005",
)

# Cita en texto: [1]
print(IEEEFormatter.format_in_text(number=1))

# Cita narrativa: Litjens et al. [1]
print(IEEEFormatter.format_narrative(citation, number=1))

# Entrada bibliográfica completa
print(IEEEFormatter.format_reference_entry(citation, number=1))
# → [1] G. Litjens, T. Kooi, and B. E. Bejnordi, "Deep Learning for Medical Image Analysis,"
#     *Medical Image Analysis*, 2017. doi: 10.1016/j.media.2017.07.005.
```

---

## 2. Formateador Vancouver / NLM (`VancouverFormatter`)

Implementado en `src/thesisforge/rag/vancouver_formatter.py`. Sigue las directrices ICMJE (*International Committee of Medical Journal Editors*) y el estilo NLM (*National Library of Medicine*), ampliamente utilizado en ciencias de la salud.

### Formato de citas en el texto

| Situación | Ejemplo |
| :--- | :--- |
| Cita básica | `(1)` |
| Cita con página | `(1, p. 25)` |
| Cita con rango de páginas | `(1, pp. 25-26)` |

### Formato de citas narrativas

| Autores | Ejemplo |
| :--- | :--- |
| 1 autor | `Smith (1)` |
| 2 autores | `Smith and Jones (1)` |
| 3+ autores | `Smith et al. (1)` |

### Formato de entradas bibliográficas

Estructura general:

```
1. Smith JK, Jones AB, Author TC. Título del artículo. Nombre de la Revista. 2024. doi: 10.xxxx/yyyy.
```

Reglas especiales:

- **Hasta 6 autores:** se listan todos en formato `Apellido Iniciales` (iniciales sin puntos, adyacentes).
- **Más de 6 autores:** se listan los primeros seis seguidos de `, et al.`
- El título del artículo va en mayúscula solo en la primera letra (sentence case).
- El nombre de la revista en texto plano (sin cursiva).

### Uso programático

```python
from thesisforge.rag.vancouver_formatter import VancouverFormatter
from thesisforge.models import CitationDTO

citation = CitationDTO(
    id="doc-002",
    title="Machine learning and the future of neuroscience",
    authors=["Savage, Neil"],
    year=2019,
    journal="Nature",
    doi="10.1038/d41586-019-02212-4",
)

# Cita en texto: (1)
print(VancouverFormatter.format_in_text(number=1))

# Cita narrativa: Savage (1)
print(VancouverFormatter.format_narrative(citation, number=1))

# Entrada bibliográfica completa
print(VancouverFormatter.format_reference_entry(citation, number=1))
# → 1. Savage N. Machine learning and the future of neuroscience.
#     Nature. 2019. doi: d41586-019-02212-4.
```

---

## 3. Comparativa de los tres formatos

| Aspecto | APA 7 | IEEE | Vancouver |
| :--- | :--- | :--- | :--- |
| **Tipo de cita en texto** | Autor-fecha `(González, 2023)` | Numérica `[1]` | Numérica `(1)` |
| **Ordenación en referencias** | Alfabética por apellido | Orden de aparición | Orden de aparición |
| **Autores en bibliografía** | Hasta 20; `et al.` a partir del 21 | Hasta 6; `et al.` a partir del 7 | Hasta 6; `et al.` a partir del 7 |
| **Formato de autores** | `Apellido, I.` | `I. Apellido` | `Apellido I` (sin puntos) |
| **Título del artículo** | Sin cursiva, mayúscula solo en la primera letra | Entre comillas dobles | Sentence case, sin marcas |
| **Nombre de revista** | En *cursiva* | En *cursiva* | En texto plano |
| **Campo de uso típico** | Ciencias sociales, educación, psicología | Ingeniería, tecnología, ciencias exactas | Medicina, ciencias de la salud |
| **Clase Python** | `APA7Formatter` | `IEEEFormatter` | `VancouverFormatter` |

---

## 4. Acceso vía API REST

```bash
# Formatear una cita en APA 7
POST /api/literature/format-apa
Content-Type: application/json
{ ... CitationDTO ... }

# Para IEEE y Vancouver, use los formateadores directamente desde código
# (los endpoints REST están planificados para v0.7.0)
```
