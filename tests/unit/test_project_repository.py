"""Unit tests for SQLite repositories: ProjectRepository & SecureKeyStoreRepository."""

import pytest

from thesisforge.core.security import LocalKeyVault
from thesisforge.exceptions import ProjectNotFoundError
from thesisforge.models import ProjectPhase, ProjectStateDTO
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.keystore_repository import SecureKeyStoreRepository
from thesisforge.repository.project_repository import ProjectRepository


@pytest.mark.asyncio
async def test_project_crud_lifecycle(
    in_memory_db: DatabaseManager, sample_project: ProjectStateDTO
):
    """Verify transactional persistence, retrieval, modification, and deletion of research projects."""
    repo = ProjectRepository(in_memory_db)

    created = await repo.create_project(sample_project)
    assert created.id == sample_project.id

    fetched = await repo.get_project(sample_project.id)
    assert fetched.id == sample_project.id
    assert fetched.title == sample_project.title
    assert len(fetched.sections) == 2

    fetched.title = "Título Modificado con Éxito"
    fetched.phase = ProjectPhase.DRAFTING
    updated = await repo.update_project(fetched)
    assert updated.title == "Título Modificado con Éxito"
    assert updated.phase == ProjectPhase.DRAFTING

    summaries = await repo.list_projects()
    assert len(summaries) == 1
    assert summaries[0].id == sample_project.id
    assert summaries[0].title == "Título Modificado con Éxito"

    drafting_projects = await repo.list_by_phase(ProjectPhase.DRAFTING)
    assert len(drafting_projects) == 1
    setup_projects = await repo.list_by_phase(ProjectPhase.SETUP)
    assert len(setup_projects) == 0

    assert await repo.delete_project(sample_project.id) is True

    with pytest.raises(ProjectNotFoundError):
        await repo.get_project(sample_project.id)


@pytest.mark.asyncio
async def test_project_not_found_errors(in_memory_db: DatabaseManager):
    """Test that querying or modifying non-existent projects raises ProjectNotFoundError."""
    repo = ProjectRepository(in_memory_db)

    with pytest.raises(ProjectNotFoundError):
        await repo.get_project("non-existent-id")

    with pytest.raises(ProjectNotFoundError):
        await repo.delete_project("non-existent-id")

    dummy_project = ProjectStateDTO(id="ghost-id", title="Ghost")
    with pytest.raises(ProjectNotFoundError):
        await repo.update_project(dummy_project)


@pytest.mark.asyncio
async def test_project_owner_isolation(in_memory_db: DatabaseManager):
    """Verify multi-tenant owner scoping prevents Insecure Direct Object References (IDOR)."""
    repo = ProjectRepository(in_memory_db)
    proj_alice = ProjectStateDTO(
        id="proj-alice-01",
        title="Tesis de Alice",
        owner_id="user_alice",
    )
    await repo.create_project(proj_alice)

    # 1. Alice can access her own project
    fetched = await repo.get_project("proj-alice-01", owner_id="user_alice")
    assert fetched.id == "proj-alice-01"
    assert fetched.owner_id == "user_alice"

    # 2. Bob cannot access Alice's project (IDOR blocked)
    with pytest.raises(ProjectNotFoundError):
        await repo.get_project("proj-alice-01", owner_id="user_bob")

    # 3. Listing is scoped by owner
    alice_list = await repo.list_projects(owner_id="user_alice")
    assert len(alice_list) == 1
    assert alice_list[0].id == "proj-alice-01"

    bob_list = await repo.list_projects(owner_id="user_bob")
    assert len(bob_list) == 0

    # 4. Bob cannot delete Alice's project
    with pytest.raises(ProjectNotFoundError):
        await repo.delete_project("proj-alice-01", owner_id="user_bob")

    # 5. Alice can delete her own project
    assert await repo.delete_project("proj-alice-01", owner_id="user_alice") is True


@pytest.mark.asyncio
async def test_keystore_repository(in_memory_db: DatabaseManager, vault: LocalKeyVault):
    """Test storing, reading, listing, and deleting encrypted API keys."""
    repo = SecureKeyStoreRepository(in_memory_db, vault)

    await repo.store_key("openrouter", "mock-openrouter-key-test")
    await repo.store_key("GEMINI", "mock-gemini-key-test")

    or_key = await repo.get_key("OpenRouter")
    assert or_key == "mock-openrouter-key-test"

    gemini_key = await repo.get_key("gemini")
    assert gemini_key == "mock-gemini-key-test"

    assert await repo.get_key("anthropic") is None

    providers = await repo.list_configured_providers()
    assert sorted(providers) == ["gemini", "openrouter"]

    assert await repo.delete_key("openrouter") is True
    assert await repo.get_key("openrouter") is None
    assert await repo.delete_key("openrouter") is False
