"""Local-First Project Portability: .thesisforge bundle export and import manager."""

import hashlib
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from thesisforge import __version__
from thesisforge.core.logging import get_logger
from thesisforge.core.time import utc_now
from thesisforge.exceptions import ExportError, ProjectNotFoundError
from thesisforge.models import ProjectStateDTO
from thesisforge.repository.project_repository import ProjectRepository

logger = get_logger(__name__)


class ProjectBundleManifest(BaseModel):
    """Integrity manifest for a .thesisforge portable research archive."""

    model_config = ConfigDict(extra="ignore")

    format_version: str = "1.0.0"
    app_version: str = __version__
    project_id: str
    title: str
    academic_level: str
    phase: str
    created_at: datetime = Field(default_factory=utc_now)
    project_sha256: str
    section_count: int = 0
    citation_count: int = 0


class ProjectBundleService:
    """Service managing atomic serialization, SHA-256 integrity checksumming, and restoration of .thesisforge archives."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self.repo = project_repo

    async def export_bundle_bytes(self, project_id: str) -> bytes:
        """Export project into an in-memory .thesisforge ZIP archive."""
        project = await self.repo.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(f"El proyecto '{project_id}' no existe.")

        project_json_str = project.model_dump_json(indent=2)
        project_sha256 = hashlib.sha256(project_json_str.encode("utf-8")).hexdigest()

        manifest = ProjectBundleManifest(
            project_id=project.id,
            title=project.title or "Proyecto de Tesis",
            academic_level=project.academic_level.value,
            phase=project.phase.value,
            project_sha256=project_sha256,
            section_count=len(project.sections),
            citation_count=len(project.validated_citations),
        )

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # 1. Manifest
            zf.writestr("manifest.json", manifest.model_dump_json(indent=2))

            # 2. Master Project State
            zf.writestr("project.json", project_json_str)

            # 3. Individual Chapter Section Files (for human inspectability)
            for section in project.sections:
                clean_sec_name = f"{section.chapter_number:02d}_{section.section_id}.md"
                zf.writestr(f"sections/{clean_sec_name}", section.content or "")

            # 4. Validated Citations Dataset
            cits_data = [c.model_dump(mode="json") for c in project.validated_citations]
            zf.writestr("citations.json", json.dumps(cits_data, indent=2, ensure_ascii=False))

        logger.info(
            "Exported .thesisforge project bundle.",
            extra={"project_id": project_id, "size_bytes": buffer.tell()},
        )
        return buffer.getvalue()

    async def export_bundle_file(self, project_id: str, output_path: str | Path) -> Path:
        """Export project bundle directly to a local disk file."""
        bundle_bytes = await self.export_bundle_bytes(project_id)
        target = Path(output_path)
        if target.is_dir():
            target = target / f"{project_id}.thesisforge"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(bundle_bytes)
        return target

    async def import_bundle_bytes(
        self,
        bundle_bytes: bytes,
        new_project_id: str | None = None,
    ) -> ProjectStateDTO:
        """Validate integrity and restore a ProjectStateDTO from a .thesisforge archive."""
        if not bundle_bytes:
            raise ExportError("El archivo .thesisforge está vacío o no es un archivo ZIP válido.")

        try:
            buffer = io.BytesIO(bundle_bytes)
            with zipfile.ZipFile(buffer, mode="r") as zf:
                infolist = zf.infolist()
                if len(infolist) > 100:
                    raise ExportError(
                        f"El paquete contiene demasiados archivos ({len(infolist)} > 100)."
                    )

                total_uncompressed = 0
                for info in infolist:
                    # Prevent Zip-Slip directory traversal
                    if ".." in info.filename or info.filename.startswith(("/", "\\")):
                        raise ExportError("Ruta de archivo no permitida en el paquete ZIP.")
                    # Prevent Zip-Bomb memory exhaustion
                    if info.file_size > 15 * 1024 * 1024:
                        raise ExportError(
                            f"El archivo '{info.filename}' excede el límite de 15 MB descomprimidos."
                        )
                    total_uncompressed += info.file_size
                    if total_uncompressed > 30 * 1024 * 1024:
                        raise ExportError(
                            "El tamaño total descomprimido del paquete excede el límite de 30 MB."
                        )

                file_list = zf.namelist()
                if "manifest.json" not in file_list or "project.json" not in file_list:
                    raise ExportError(
                        "El archivo no es un paquete .thesisforge válido (faltan manifest.json o project.json)."
                    )

                manifest_raw = zf.read("manifest.json").decode("utf-8")
                manifest = ProjectBundleManifest.model_validate_json(manifest_raw)

                # Validate format version compatibility
                if not manifest.format_version.startswith("1."):
                    raise ExportError(
                        f"Versión de formato no soportada en el paquete .thesisforge: '{manifest.format_version}'."
                    )

                project_raw_bytes = zf.read("project.json")
                calculated_sha256 = hashlib.sha256(project_raw_bytes).hexdigest()

                if calculated_sha256 != manifest.project_sha256:
                    raise ExportError(
                        "Fallo de integridad: El checksum SHA-256 no coincide con el manifiesto "
                        "(posible corrupción de archivo o manipulación no autorizada)."
                    )

                project_dict = json.loads(project_raw_bytes.decode("utf-8"))
                project = ProjectStateDTO.model_validate(project_dict)

                # Validate structural coherence between manifest and project payload (TF-EXPORT-001)
                if manifest.project_id != project.id:
                    raise ExportError(
                        f"Incoherencia estructural en el paquete .thesisforge: "
                        f"El manifiesto declara project_id '{manifest.project_id}' "
                        f"pero project.json tiene '{project.id}'."
                    )
                if manifest.title != (project.title or "Proyecto de Tesis"):
                    raise ExportError(
                        f"Incoherencia estructural en el paquete .thesisforge: "
                        f"El manifiesto declara título '{manifest.title}' "
                        f"pero project.json tiene '{project.title}'."
                    )
                if manifest.academic_level != project.academic_level.value:
                    raise ExportError(
                        f"Incoherencia estructural en el paquete .thesisforge: "
                        f"El manifiesto declara nivel académico '{manifest.academic_level}' "
                        f"pero project.json tiene '{project.academic_level.value}'."
                    )
                if manifest.phase != project.phase.value:
                    raise ExportError(
                        f"Incoherencia estructural en el paquete .thesisforge: "
                        f"El manifiesto declara fase '{manifest.phase}' "
                        f"pero project.json tiene '{project.phase.value}'."
                    )
                if manifest.section_count != len(project.sections):
                    raise ExportError(
                        f"Incoherencia estructural en el paquete .thesisforge: "
                        f"El manifiesto declara {manifest.section_count} secciones "
                        f"pero project.json contiene {len(project.sections)}."
                    )
                if manifest.citation_count != len(project.validated_citations):
                    raise ExportError(
                        f"Incoherencia estructural en el paquete .thesisforge: "
                        f"El manifiesto declara {manifest.citation_count} citas "
                        f"pero project.json contiene {len(project.validated_citations)}."
                    )

                # Validate section file content consistency with canonical project.json
                for section in project.sections:
                    sec_filename = f"sections/{section.chapter_number:02d}_{section.section_id}.md"
                    if sec_filename in file_list:
                        sec_raw = zf.read(sec_filename).decode("utf-8")
                        if sec_raw != (section.content or ""):
                            raise ExportError(
                                f"Incoherencia de contenido en sección: '{sec_filename}' "
                                f"no coincide con el contenido canónico de project.json."
                            )

                if new_project_id:
                    project.id = new_project_id

                # Save or update project in repository
                try:
                    await self.repo.get_project(project.id)
                    await self.repo.update_project(project)
                except ProjectNotFoundError:
                    await self.repo.create_project(project)

                logger.info(
                    "Imported .thesisforge project bundle successfully.",
                    extra={"project_id": project.id, "title": project.title},
                )
                return project

        except zipfile.BadZipFile as err:
            raise ExportError("El archivo no tiene un formato ZIP válido.") from err
        except Exception as err:
            if isinstance(err, ExportError):
                raise
            raise ExportError(f"Error procesando el paquete de proyecto: {err}") from err

    async def import_bundle_file(
        self,
        file_path: str | Path,
        new_project_id: str | None = None,
    ) -> ProjectStateDTO:
        """Import a project bundle from a local file system path."""
        path = Path(file_path)
        if not path.is_file():
            raise ExportError(f"El archivo '{file_path}' no existe.")
        return await self.import_bundle_bytes(path.read_bytes(), new_project_id=new_project_id)
