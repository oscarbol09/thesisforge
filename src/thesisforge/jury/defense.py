"""Interactive socratic thesis defense simulator and turn-based oral exam engine."""

import uuid

from thesisforge.core.logging import get_logger
from thesisforge.core.time import utc_now
from thesisforge.exceptions import DefenseSessionError, DefenseTurnNotFoundError
from thesisforge.llm.prompts import (
    DEFENSE_QUESTIONS_GENERATION_PROMPT,
    DEFENSE_REPLY_EVALUATION_PROMPT,
)
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AcademicLevel,
    DefenseSessionDTO,
    DefenseStatus,
    DefenseTurnDTO,
    JurorRole,
    JuryEvaluationReportDTO,
    ProjectStateDTO,
)

logger = get_logger(__name__)


class ThesisDefenseSimulator:
    """Orchestrates interactive, multi-turn oral thesis defenses with simulated scientific jurors."""

    def __init__(self, llm_router: LLMRouter | None = None) -> None:
        self.llm = llm_router

    def _generate_default_questions(
        self,
        project: ProjectStateDTO,
        evaluation: JuryEvaluationReportDTO | None = None,
    ) -> list[DefenseTurnDTO]:
        """Generate high-rigor default questions calibrated by academic level and project attributes."""
        level = project.academic_level
        methodology = project.methodology
        design = methodology.design if methodology and methodology.design else "diseño metodológico"
        sample = methodology.sample if methodology and methodology.sample else "muestra de estudio"
        technique = (
            methodology.analysis_technique
            if methodology and methodology.analysis_technique
            else "análisis de datos"
        )

        level_qualifier = (
            "doctoral"
            if level == AcademicLevel.DOCTORADO
            else ("de maestría" if level == AcademicLevel.MAESTRIA else "de pregrado")
        )

        # Question 1: Methodologist
        if project.hypothesis:
            q_met = (
                f"Para un nivel {level_qualifier}, ¿cómo garantiza que el {design} seleccionado controle las variables extrañas "
                f"y prevenga el error Tipo I al contrastar su hipótesis '{project.hypothesis[:120]}'?"
            )
        else:
            q_met = (
                f"En su propuesta, ¿cuáles son las principales amenazas a la validez interna de su {design} "
                f"y qué criterios de consistencia garantizan que los objetivos específicos alcancen el objetivo general?"
            )

        # Question 2: Domain Specialist
        citation_count = len(project.validated_citations)
        q_dom = (
            f"Frente al estado del arte internacional indexado ({citation_count} fuentes analizadas), "
            f"¿cuál es la novedad conceptual estricta de su investigación frente a los modelos teóricos preexistentes en su área?"
        )

        # Question 3: Statistical/Empirical Auditor
        q_stat = (
            f"En relación con su universo y {sample}, ¿cómo justifica la representatividad estadística o la saturación teórica "
            f"de los datos recolectados mediante {technique} frente a posibles sesgos de selección?"
        )

        # Question 4: Devil's Advocate / Critical Challenger
        q_crit = (
            "Si un investigador independiente intentara replicar su estudio y encontrara resultados diametralmente opuestos, "
            "¿qué supuestos no declarados o factores contextuales podrían explicar dicha discrepancia?"
        )

        turns = [
            DefenseTurnDTO(
                turn_index=0,
                juror_role=JurorRole.METODOLOGO,
                juror_name="Dr. Arístides Valenzuela",
                focus_area="Validez Interna y Consistencia Metodológica",
                question=q_met,
                created_at=utc_now(),
            ),
            DefenseTurnDTO(
                turn_index=1,
                juror_role=JurorRole.ESPECIALISTA_TEMATICO,
                juror_name="Dra. Beatriz Salamanca",
                focus_area="Marco Teórico y Estado del Arte",
                question=q_dom,
                created_at=utc_now(),
            ),
            DefenseTurnDTO(
                turn_index=2,
                juror_role=JurorRole.AUDITOR_ESTADISTICO,
                juror_name="Dr. Camilo Restrepo",
                focus_area="Muestreo y Rigor Empírico",
                question=q_stat,
                created_at=utc_now(),
            ),
            DefenseTurnDTO(
                turn_index=3,
                juror_role=JurorRole.ABOGADO_DEL_DIABLO,
                juror_name="Dr. Demetrio Sotomayor",
                focus_area="Supuestos Ocultos y Límites Epistemológicos",
                question=q_crit,
                created_at=utc_now(),
            ),
        ]
        return turns

    async def initialize_defense_session(
        self,
        project: ProjectStateDTO,
        evaluation: JuryEvaluationReportDTO | None = None,
    ) -> DefenseSessionDTO:
        """Create a new oral defense session with 4 tailored questions."""
        turns = self._generate_default_questions(project, evaluation)

        if self.llm:
            try:
                sections_summary = (
                    "\n".join(
                        f"- {s.title}: {s.summary or s.content[:150] + '...'}"
                        for s in project.sections
                    )
                    or "Borradores no inicializados."
                )

                known_flaws = ""
                if evaluation:
                    known_flaws = "\n".join(
                        f"- {i.title}: {i.description}" for i in evaluation.issues[:4]
                    )
                else:
                    known_flaws = "Sin auditoría previa registrada."

                prompt = DEFENSE_QUESTIONS_GENERATION_PROMPT.format(
                    title=project.title or "Proyecto de Investigación",
                    academic_level=project.academic_level.value,
                    research_question=project.research_question or "No especificada",
                    general_objective=project.general_objective or "No especificado",
                    hypothesis=project.hypothesis or "No formulada",
                    approach=project.methodology.approach.value
                    if project.methodology and project.methodology.approach
                    else "No definido",
                    design=project.methodology.design if project.methodology else "No definido",
                    population=project.methodology.population
                    if project.methodology
                    else "No definida",
                    sample=project.methodology.sample if project.methodology else "No definida",
                    instruments=", ".join(project.methodology.instruments)
                    if project.methodology
                    else "Ninguno",
                    analysis_technique=project.methodology.analysis_technique
                    if project.methodology
                    else "No especificada",
                    sections_summary=sections_summary,
                    known_flaws=known_flaws,
                )

                parsed_json = await self.llm.complete_json(prompt=prompt, system_prompt="")
                raw_questions = parsed_json.get("questions", [])
                if len(raw_questions) >= 4:
                    llm_turns: list[DefenseTurnDTO] = []
                    role_map = {
                        "metodologo": (JurorRole.METODOLOGO, "Dr. Arístides Valenzuela"),
                        "especialista_tematico": (
                            JurorRole.ESPECIALISTA_TEMATICO,
                            "Dra. Beatriz Salamanca",
                        ),
                        "auditor_estadistico": (
                            JurorRole.AUDITOR_ESTADISTICO,
                            "Dr. Camilo Restrepo",
                        ),
                        "abogado_del_diablo": (
                            JurorRole.ABOGADO_DEL_DIABLO,
                            "Dr. Demetrio Sotomayor",
                        ),
                    }
                    for idx, q_data in enumerate(raw_questions[:4]):
                        role_str = str(q_data.get("juror_role", "")).lower()
                        role_enum, default_name = role_map.get(
                            role_str, (JurorRole.METODOLOGO, "Dr. Arístides Valenzuela")
                        )
                        llm_turns.append(
                            DefenseTurnDTO(
                                turn_index=idx,
                                juror_role=role_enum,
                                juror_name=str(q_data.get("juror_name", default_name)),
                                focus_area=str(q_data.get("focus_area", "Defensa Metodológica")),
                                question=str(q_data.get("question", turns[idx].question)),
                                created_at=utc_now(),
                            )
                        )
                    turns = llm_turns
            except Exception as exc:
                logger.warning(
                    "Could not generate custom LLM defense questions; falling back to calibrated defaults.",
                    extra={"error": str(exc), "project_id": project.id},
                )

        session = DefenseSessionDTO(
            id=uuid.uuid4().hex[:12],
            project_id=project.id,
            academic_level=project.academic_level,
            status=DefenseStatus.IN_PROGRESS,
            current_turn_index=0,
            total_turns=len(turns),
            turns=turns,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        return session

    def _heuristic_evaluate_answer(
        self,
        turn: DefenseTurnDTO,
        student_answer: str,
        project: ProjectStateDTO,
    ) -> tuple[float, str]:
        """Perform deterministic evaluation of student answer based on length, keywords and domain depth."""
        answer_clean = student_answer.strip()
        word_count = len(answer_clean.split())

        if word_count < 15:
            return 45.0, (
                "La respuesta es excesivamente escueta y evasiva. "
                "En una sustentación formal debe desarrollar una argumentación técnica sólida con respaldo metodológico."
            )

        score = 70.0

        # Terminology & empirical grounding heuristics
        technical_keywords = [
            "metodología",
            "diseño",
            "validez",
            "muestra",
            "variables",
            "análisis",
            "control",
            "hipótesis",
            "confiabilidad",
            "instrumento",
            "limitación",
            "alcance",
            "datos",
            "empírico",
            "evidencia",
            "teoría",
            "triangulación",
        ]
        matches = sum(1 for kw in technical_keywords if kw in answer_clean.lower())
        score += min(20.0, matches * 4.0)

        if word_count >= 50:
            score += 5.0
        if word_count >= 100:
            score += 5.0

        score = min(100.0, max(0.0, score))

        if score >= 90.0:
            feedback = (
                "Réplica sólida, rigurosa y bien fundamentada. "
                "El tesista demostró dominio disciplinar y claridad frente a la objeción planteada."
            )
        elif score >= 75.0:
            feedback = (
                "Respuesta aceptable que aborda los puntos principales de la pregunta. "
                "Se recomienda profundizar aún más en la justificación empírica de los resultados."
            )
        elif score >= 60.0:
            feedback = "La réplica presenta argumentos plausibles pero muestra vacíos conceptuales o metodológicos frente al cuestionamiento."
        else:
            feedback = "La argumentación es insuficiente para responder a la objeción del jurado. Falta respaldo metodológico concreto."

        return score, feedback

    async def submit_defense_turn(
        self,
        session: DefenseSessionDTO,
        turn_index: int,
        student_answer: str,
        project: ProjectStateDTO,
    ) -> DefenseSessionDTO:
        """Process student response for a given turn, score it, and advance session state."""
        if session.status != DefenseStatus.IN_PROGRESS:
            raise DefenseSessionError(
                f"La sesión de sustentación ya finalizó con estado '{session.status.value}'.",
                details={"session_id": session.id, "status": session.status.value},
            )

        if turn_index < 0 or turn_index >= len(session.turns):
            raise DefenseTurnNotFoundError(
                f"El turno de defensa #{turn_index} no existe en la sesión '{session.id}'.",
                details={"session_id": session.id, "turn_index": str(turn_index)},
            )

        if turn_index != session.current_turn_index:
            raise DefenseSessionError(
                f"El turno actual esperado es #{session.current_turn_index}, pero se recibió #{turn_index}.",
                details={
                    "expected_turn": str(session.current_turn_index),
                    "received_turn": str(turn_index),
                },
            )

        turn = session.turns[turn_index]
        if turn.is_answered:
            raise DefenseSessionError(
                f"El turno #{turn_index} ya ha sido respondido y evaluado.",
                details={"session_id": session.id, "turn_index": str(turn_index)},
            )

        answer_clean = student_answer.strip()
        if not answer_clean:
            raise DefenseSessionError(
                "La respuesta del estudiante no puede estar vacía.",
                details={"turn_index": str(turn_index)},
            )

        # Evaluate Answer
        if self.llm:
            try:
                prompt = DEFENSE_REPLY_EVALUATION_PROMPT.format(
                    juror_name=turn.juror_name,
                    juror_role=turn.juror_role.value,
                    question=turn.question,
                    focus_area=turn.focus_area,
                    academic_level=session.academic_level.value,
                    student_answer=answer_clean,
                )
                parsed_json = await self.llm.complete_json(prompt=prompt, system_prompt="")
                raw_score = float(parsed_json.get("turn_score", 75.0))
                turn_score = round(max(0.0, min(100.0, raw_score)), 1)
                feedback = str(
                    parsed_json.get(
                        "feedback",
                        "El jurado evaluó la réplica del estudiante con argumentos metodológicos suficientes.",
                    )
                )
            except Exception as exc:
                logger.warning(
                    "LLM answer evaluation failed; using heuristic evaluation engine.",
                    extra={"error": str(exc), "session_id": session.id},
                )
                turn_score, feedback = self._heuristic_evaluate_answer(turn, answer_clean, project)
        else:
            turn_score, feedback = self._heuristic_evaluate_answer(turn, answer_clean, project)

        # Update Turn
        turn.student_answer = answer_clean
        turn.juror_feedback = feedback
        turn.turn_score = turn_score
        turn.is_answered = True

        # Advance or Finalize Session
        session.current_turn_index += 1
        session.updated_at = utc_now()

        if session.current_turn_index >= session.total_turns:
            # Finalize defense session
            scores = [t.turn_score for t in session.turns if t.turn_score is not None]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
            session.final_score = avg_score

            if avg_score >= 90.0:
                session.final_verdict = DefenseStatus.PASSED_WITH_HONORS
                session.status = DefenseStatus.PASSED_WITH_HONORS
                session.final_remarks = (
                    f"Sustentación sobresaliente con calificación de {avg_score}/100. "
                    "El tesista demostró excelencia metodológica, dominio del estado del arte y solvencia argumentativa."
                )
            elif avg_score >= 70.0:
                session.final_verdict = DefenseStatus.PASSED
                session.status = DefenseStatus.PASSED
                session.final_remarks = (
                    f"Sustentación aprobada con calificación de {avg_score}/100. "
                    "El tesista defendió satisfactoriamente los postulados centrales de su investigación."
                )
            elif avg_score >= 50.0:
                session.final_verdict = DefenseStatus.NEEDS_REVISION
                session.status = DefenseStatus.NEEDS_REVISION
                session.final_remarks = (
                    f"Sustentación con réplica condicionada ({avg_score}/100). "
                    "Se requiere complementar y aclarar aspectos metodológicos y empíricos señalados en las observaciones."
                )
            else:
                session.final_verdict = DefenseStatus.FAILED
                session.status = DefenseStatus.FAILED
                session.final_remarks = (
                    f"Sustentación no aprobada ({avg_score}/100). "
                    "Las réplicas no lograron justificar las inconsistencias críticas formuladas por el tribunal evaluador."
                )

        return session
