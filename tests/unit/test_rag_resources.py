"""Tests for RAG resource ownership and application lifecycle."""

import asyncio

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

import thesisforge.api.app as app_module
import thesisforge.api.deps as deps_module
import thesisforge.rag.resources as resources_module
import thesisforge.rag.service as service_module
from thesisforge.api.deps import (
    get_db_manager,
    get_keystore_repository,
    get_llm_router,
    get_project_repository,
    get_rag_service,
)
from thesisforge.config import get_settings
from thesisforge.rag.resources import RAGServiceResources
from thesisforge.rag.service import RAGService
from thesisforge.rag.vectorstore import ChromaVectorStore
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.mark.asyncio
async def test_rag_routes_reuse_app_resources_across_requests(
    in_memory_db: DatabaseManager,
) -> None:
    settings = get_settings()
    resources = RAGServiceResources(
        db_manager=in_memory_db,
        persist_directory=settings.rag.chroma_dir,
        is_memory=True,
        embedding_provider="fast_local",
    )
    app = FastAPI()
    app.state.rag_resources = resources
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    app.dependency_overrides[get_llm_router] = lambda: None
    app.dependency_overrides[get_settings] = lambda: settings

    def get_request_project_repository(request: Request) -> ProjectRepository:
        return ProjectRepository(in_memory_db, request.headers["x-owner"])

    app.dependency_overrides[get_project_repository] = get_request_project_repository

    @app.get("/resources")
    async def get_resource_ids(
        service: RAGService = Depends(get_rag_service),
    ) -> dict[str, str]:
        return {
            "service": str(id(service)),
            "vector_store": str(id(service.vector_store)),
            "semantic_scholar": str(id(service.semantic_scholar)),
            "owner_id": service.repo.owner_id,
        }

    async def request_resources(client: AsyncClient, owner_id: str) -> dict[str, str]:
        response = await client.get("/resources", headers={"x-owner": owner_id})
        assert response.status_code == 200
        return response.json()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            first, second = await asyncio.gather(
                request_resources(client, "owner-one"),
                request_resources(client, "owner-two"),
            )
            assert first["vector_store"] == second["vector_store"]
            assert first["semantic_scholar"] == second["semantic_scholar"]
            assert first["owner_id"] == "owner-one"
            assert second["owner_id"] == "owner-two"

            concurrent = await asyncio.gather(
                *(request_resources(client, f"owner-{index}") for index in range(4))
            )
            assert {response["vector_store"] for response in concurrent} == {
                str(id(resources.vector_store))
            }
            assert {response["semantic_scholar"] for response in concurrent} == {
                str(id(resources.semantic_scholar))
            }
            assert {response["owner_id"] for response in concurrent} == {
                f"owner-{index}" for index in range(4)
            }
    finally:
        app.dependency_overrides.clear()
        await resources.close()


@pytest.mark.asyncio
async def test_keyed_rag_services_keep_semantic_scholar_clients_request_scoped(
    in_memory_db: DatabaseManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSemanticScholarClient:
        def __init__(self, *, api_key: str | None, cache: object) -> None:
            self.api_key = api_key
            self.cache = cache
            self.close_calls = 0

        async def close(self) -> None:
            self.close_calls += 1

    clients: list[FakeSemanticScholarClient] = []

    def create_client(*, api_key: str | None, cache: object) -> FakeSemanticScholarClient:
        client = FakeSemanticScholarClient(api_key=api_key, cache=cache)
        clients.append(client)
        return client

    monkeypatch.setattr(service_module, "SemanticScholarClient", create_client)
    settings = get_settings()
    resources = RAGServiceResources(
        db_manager=in_memory_db,
        persist_directory=settings.rag.chroma_dir,
        is_memory=True,
        embedding_provider=settings.rag.embedding_provider,
    )
    project_repo = ProjectRepository(in_memory_db, "owner")
    try:
        first = RAGService(
            db_manager=in_memory_db,
            project_repo=project_repo,
            resources=resources,
            semantic_scholar_api_key="first-request-key",
        )
        second = RAGService(
            db_manager=in_memory_db,
            project_repo=project_repo,
            resources=resources,
            semantic_scholar_api_key="second-request-key",
        )

        assert first.semantic_scholar is not second.semantic_scholar
        assert first.semantic_scholar.api_key == "first-request-key"
        assert second.semantic_scholar.api_key == "second-request-key"
        assert resources.semantic_scholar.api_key is None

        await asyncio.gather(first.close(), second.close())
        assert [client.close_calls for client in clients] == [1, 1]
    finally:
        await resources.close()


@pytest.mark.asyncio
async def test_request_resources_close_when_handler_fails(
    in_memory_db: DatabaseManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeResources:
        def __init__(
            self,
            db_manager: DatabaseManager,
            persist_directory: str,
            is_memory: bool,
            embedding_provider: str | None,
        ) -> None:
            del db_manager, persist_directory, is_memory, embedding_provider
            self.cache = object()
            self.semantic_scholar = object()
            self.arxiv = object()
            self.crossref = object()
            self.openalex = object()
            self.vector_store = object()
            self.close_calls = 0

        async def close(self) -> None:
            self.close_calls += 1

    class FakeSemanticScholarClient:
        def __init__(self, *, api_key: str | None, cache: object) -> None:
            self.api_key = api_key
            self.cache = cache
            self.close_calls = 0

        async def close(self) -> None:
            self.close_calls += 1

    clients: list[FakeSemanticScholarClient] = []

    def create_client(*, api_key: str | None, cache: object) -> FakeSemanticScholarClient:
        client = FakeSemanticScholarClient(api_key=api_key, cache=cache)
        clients.append(client)
        return client

    class FakeKeyStore:
        async def get_key(self, provider: str) -> str | None:
            assert provider == "semantic_scholar"
            return "request-key"

    created_resources: list[FakeResources] = []

    def create_resources(
        db_manager: DatabaseManager,
        persist_directory: str,
        is_memory: bool,
        embedding_provider: str | None,
    ) -> FakeResources:
        resources = FakeResources(db_manager, persist_directory, is_memory, embedding_provider)
        created_resources.append(resources)
        return resources

    monkeypatch.setattr(deps_module, "RAGServiceResources", create_resources)
    monkeypatch.setattr(service_module, "SemanticScholarClient", create_client)
    app = FastAPI()
    settings = get_settings()
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    app.dependency_overrides[get_llm_router] = lambda: None
    app.dependency_overrides[get_project_repository] = lambda: ProjectRepository(
        in_memory_db, "owner"
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_keystore_repository] = lambda: FakeKeyStore()

    @app.get("/failure")
    async def fail_request(service: RAGService = Depends(get_rag_service)) -> None:
        assert service.resources is created_resources[0]
        raise RuntimeError("handler failed")

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with pytest.raises(RuntimeError, match="handler failed"):
                await client.get("/failure")
    finally:
        app.dependency_overrides.clear()

    assert len(created_resources) == 1
    assert created_resources[0].close_calls == 1
    assert len(clients) == 1
    assert clients[0].api_key == "request-key"
    assert clients[0].close_calls == 1


@pytest.mark.asyncio
async def test_resource_close_attempts_all_clients_and_vector_store(
    in_memory_db: DatabaseManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeClient:
        def __init__(self, should_fail: bool = False) -> None:
            self.should_fail = should_fail
            self.close_calls = 0

        async def close(self) -> None:
            self.close_calls += 1
            if self.should_fail:
                raise RuntimeError("client close failed")

    class FakeVectorStore:
        def __init__(self) -> None:
            self.close_calls = 0

        def close(self) -> None:
            self.close_calls += 1

    clients = [FakeClient(should_fail=True), FakeClient(), FakeClient(), FakeClient()]
    client_iterator = iter(clients)
    vector_store = FakeVectorStore()

    def make_client(*, cache: object) -> FakeClient:
        del cache
        return next(client_iterator)

    def make_vector_store(**kwargs: object) -> FakeVectorStore:
        del kwargs
        return vector_store

    monkeypatch.setattr(resources_module, "SemanticScholarClient", make_client)
    monkeypatch.setattr(resources_module, "ArxivClient", make_client)
    monkeypatch.setattr(resources_module, "CrossRefClient", make_client)
    monkeypatch.setattr(resources_module, "OpenAlexClient", make_client)
    monkeypatch.setattr(resources_module, "ChromaVectorStore", make_vector_store)

    resources = RAGServiceResources(in_memory_db, "unused", True, "fast_local")
    with pytest.raises(RuntimeError, match="client close failed"):
        await resources.close()

    assert [client.close_calls for client in clients] == [1, 1, 1, 1]
    assert vector_store.close_calls == 1


def test_vector_store_closes_client_when_supported() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.close_calls = 0

        def close(self) -> None:
            self.close_calls += 1

    client = FakeClient()
    store = object.__new__(ChromaVectorStore)
    store._client = client

    store.close()

    assert client.close_calls == 1


@pytest.mark.asyncio
async def test_app_lifespan_closes_rag_resources_on_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeDatabase:
        def __init__(self) -> None:
            self.initialized = False
            self.closed = False

        async def initialize(self) -> None:
            self.initialized = True

        async def close(self) -> None:
            self.closed = True

    class FakeCache:
        def __init__(self, db_manager: FakeDatabase) -> None:
            del db_manager

        async def prune_expired(self) -> int:
            return 0

    class FakeResources:
        def __init__(
            self,
            db_manager: FakeDatabase,
            persist_directory: str,
            is_memory: bool,
            embedding_provider: str,
        ) -> None:
            del db_manager, persist_directory, is_memory, embedding_provider
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    database = FakeDatabase()
    monkeypatch.setattr(app_module, "get_db_manager", lambda: database)
    monkeypatch.setattr(app_module, "LiteratureCache", FakeCache)
    monkeypatch.setattr(app_module, "RAGServiceResources", FakeResources)
    app = app_module.create_app()

    with pytest.raises(RuntimeError, match="request failed"):
        async with app.router.lifespan_context(app):
            resources = app.state.rag_resources
            assert database.initialized
            raise RuntimeError("request failed")

    assert resources.closed
    assert app.state.rag_resources is None
    assert database.closed
