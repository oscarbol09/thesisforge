"""Unit tests for project deletion via the REST router."""

from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from thesisforge.api.deps import get_current_owner, get_project_repository, get_rag_service
from thesisforge.api.routes_project import router
from thesisforge.core.auth import LOCAL_OWNER_ID
from thesisforge.exceptions import ProjectNotFoundError

PROJECT_ID = "00000000-0000-0000-0000-000000000001"


class FakeProjectRepository:
    def __init__(self, missing: bool = False) -> None:
        self.missing = missing
        self.deleted_ids: list[str] = []

    async def delete_project(self, project_id: str) -> bool:
        if self.missing:
            raise ProjectNotFoundError("not found")
        self.deleted_ids.append(project_id)
        return True


class FakeVectorStore:
    def __init__(self) -> None:
        self.deleted_collections: list[str] = []

    async def delete_project_collection(self, project_id: str) -> None:
        self.deleted_collections.append(project_id)


def make_client(repo: FakeProjectRepository, vector_store: FakeVectorStore) -> httpx.AsyncClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_project_repository] = lambda: repo
    app.dependency_overrides[get_rag_service] = lambda: SimpleNamespace(vector_store=vector_store)
    app.dependency_overrides[get_current_owner] = lambda: LOCAL_OWNER_ID
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_delete_existing_project_returns_204() -> None:
    repo = FakeProjectRepository()
    vector_store = FakeVectorStore()

    async with make_client(repo, vector_store) as client:
        response = await client.delete(f"/api/projects/{PROJECT_ID}")

    assert response.status_code == 204
    assert response.content == b""
    assert repo.deleted_ids == [PROJECT_ID]
    assert vector_store.deleted_collections == [PROJECT_ID]


@pytest.mark.asyncio
async def test_delete_missing_project_returns_404() -> None:
    repo = FakeProjectRepository(missing=True)
    vector_store = FakeVectorStore()

    async with make_client(repo, vector_store) as client:
        response = await client.delete(f"/api/projects/{PROJECT_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": f"Project with id '{PROJECT_ID}' not found"}
    assert repo.deleted_ids == []
    assert vector_store.deleted_collections == []
