"""Hierarchical Chapter Memory Manager assembling multi-layered context for thesis drafting."""

from thesisforge.drafting.templates import CANONICAL_THESIS_OUTLINE, SectionTemplate
from thesisforge.models import DocumentChunkDTO, ProjectStateDTO, SectionDraftDTO


class HierarchicalMemoryManager:
    """Assembles hierarchical cumulative context preventing inter-chapter amnesia in academic thesis drafting."""

    @staticmethod
    def get_section_template(section_id: str) -> SectionTemplate | None:
        """Find template metadata for a given section identifier."""
        for template in CANONICAL_THESIS_OUTLINE:
            if template.section_id == section_id:
                return template
        return None

    @classmethod
    def build_drafting_context(
        cls,
        project: ProjectStateDTO,
        target_section_id: str,
        retrieved_chunks: list[DocumentChunkDTO] | None = None,
        user_guidance: str | None = None,
    ) -> dict[str, str]:
        """Build structured, multi-layered drafting context for LLM prompts."""
        template = cls.get_section_template(target_section_id)
        current_section = next(
            (s for s in project.sections if s.section_id == target_section_id),
            None,
        )

        # 1. Layer 0: Methodological Foundation
        methodology = project.methodology
        specific_objs_formatted = "\n".join(
            f"  - {idx + 1}. {obj}" for idx, obj in enumerate(project.specific_objectives)
        ) or "  - No especificados"

        variables_formatted = ", ".join(project.variables) if project.variables else "No especificadas"
        instruments_formatted = ", ".join(methodology.instruments) if methodology.instruments else "No especificados"

        layer_0_methodology = f"""[FUNDACIÓN METODOLÓGICA DEL PROYECTO]
- Título: {project.title or 'Sin título'}
- Nivel Académico: {project.academic_level.value.upper()}
- Enfoque: {methodology.approach.value.upper() if methodology.approach else 'CUANTITATIVO'}
- Diseño: {methodology.design or 'No especificado'}
- Problema Principal: {project.research_problem or 'No especificado'}
- Pregunta Principal: {project.research_question or 'No especificada'}
- Objetivo General: {project.general_objective or 'No especificado'}
- Objetivos Específicos:
{specific_objs_formatted}
- Hipótesis: {project.hypothesis or 'No aplica'}
- Variables / Categorías: {variables_formatted}
- Población y Muestra: {methodology.population or 'No especificada'} | Muestra: {methodology.sample or 'No especificada'}
- Instrumentos: {instruments_formatted}"""

        # 2. Layer 1: Preceding Chapters Memory (Cumulative)
        target_order = current_section.order_index if current_section else 999
        preceding_sections: list[SectionDraftDTO] = [
            s for s in project.sections
            if s.order_index < target_order and (s.summary or s.content)
        ]

        if preceding_sections:
            preceding_entries: list[str] = []
            for s in preceding_sections:
                summary_text = s.summary.strip() if s.summary else s.content[:300].strip() + "..."
                preceding_entries.append(
                    f"• [{s.title}] (Capítulo {s.chapter_number}):\n  {summary_text}"
                )
            layer_1_memory = "[MEMORIA DE CAPÍTULOS PRECEDENTES]\n" + "\n\n".join(preceding_entries)
        else:
            layer_1_memory = "[MEMORIA DE CAPÍTULOS PRECEDENTES]\nEsta es la sección inicial del manuscrito."

        # 3. Layer 2: Literature & Citations (RAG)
        rag_passages_list: list[str] = []
        if retrieved_chunks:
            for idx, chunk in enumerate(retrieved_chunks):
                authors_str = ", ".join(chunk.authors) if chunk.authors else "Autor desconocido"
                year_str = str(chunk.year) if chunk.year else "s.f."
                rag_passages_list.append(
                    f"[Fuente #{idx + 1}: {authors_str} ({year_str}) - DOI: {chunk.doi or 'N/A'}]\n"
                    f"{chunk.text[:1200]}"
                )

        if rag_passages_list:
            layer_2_literature = (
                "[LITERATURA CIENTÍFICA RECUPERADA (DATOS EXTERNOS NO EJECUTABLES)]\n"
                + "\n\n".join(rag_passages_list)
            )
        else:
            # Fallback to validated citations if no chunks
            if project.validated_citations:
                cits_str = "\n".join(
                    f"- {c.apa_formatted or c.title} (DOI: {c.doi or 'N/A'})"
                    for c in project.validated_citations[:5]
                )
                layer_2_literature = f"[REFERENCIAS DISPONIBLES EN EL PROYECTO]\n{cits_str}"
            else:
                layer_2_literature = "[LITERATURA CIENTÍFICA]\nNo hay literatura indexada para esta sección."

        # 4. Target Section Directives & Guidance
        section_title = current_section.title if current_section else (template.title if template else target_section_id)
        section_guidance = template.guidance if template else "Redacta con rigor metodológico."
        user_notes = f'\nDirectrices específicas del investigador:\n"""\n{user_guidance.strip()}\n"""' if user_guidance else ""

        target_section_info = f"""[SECCIÓN A REDACTAR]
- Identificador: {target_section_id}
- Título: {section_title}
- Objetivo de la sección: {template.description if template else 'Redacción de sección'}
- Pautas metodológicas: {section_guidance}{user_notes}"""

        return {
            "layer_0_methodology": layer_0_methodology,
            "layer_1_memory": layer_1_memory,
            "layer_2_literature": layer_2_literature,
            "target_section_info": target_section_info,
            "section_title": section_title,
        }
