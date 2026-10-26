from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from app.client import (
    PortalClient,
    PortalClientError,
    PortalResponseError,
    PortalTimeoutError,
    PortalUpstreamError,
)
from app.models import (
    DistributionTransformer,
    EnergyResponse,
    MeterLocationResponse,
    MeterSummary,
    PortalPage,
)


def create_app(
    portal_client: PortalClient | None = None,
    *,
    timeout: float = 10.0,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
        if portal_client is not None:
            application.state.portal_client = portal_client
            try:
                yield
            finally:
                await portal_client.aclose()
            return

        from app.config import PORTAL_BASE_URL

        client = PortalClient(
            PORTAL_BASE_URL,
            timeout=timeout,
            transport=transport,
        )
        application.state.portal_client = client
        try:
            yield
        finally:
            await client.aclose()

    application = FastAPI(
        title="Flock Energy API",
        description="Read-only proxy for verified Urja portal operations.",
        lifespan=lifespan,
    )

    @application.exception_handler(PortalTimeoutError)
    async def handle_portal_timeout(
        _request: Request, _exc: PortalTimeoutError
    ) -> JSONResponse:
        _ = _request, _exc
        return JSONResponse(
            status_code=504,
            content={"detail": "Portal request timed out"},
        )

    @application.exception_handler(PortalUpstreamError)
    @application.exception_handler(PortalResponseError)
    @application.exception_handler(PortalClientError)
    async def handle_portal_error(
        _request: Request, _exc: PortalClientError
    ) -> JSONResponse:
        _ = _request, _exc
        return JSONResponse(
            status_code=502,
            content={"detail": "Portal request failed"},
        )

    def get_client(request: Request) -> PortalClient:
        client = getattr(request.app.state, "portal_client", None)
        if client is None:
            raise HTTPException(
                status_code=503,
                detail="Portal client is not initialized",
            )
        return client

    @application.get(
        "/meters",
        response_model=PortalPage[MeterSummary],
        response_model_by_alias=True,
    )
    async def search_meters(
        request: Request,
        q: str = Query(default=""),
        page: int = Query(default=1, ge=1),
    ) -> PortalPage[MeterSummary]:
        return await get_client(request).list_meters(query=q, page=page)

    @application.get(
        "/meters/{meter_id}/geo",
        response_model=MeterLocationResponse,
        response_model_by_alias=True,
    )
    async def get_meter_location(
        request: Request,
        meter_id: str = Path(min_length=1),
    ) -> MeterLocationResponse:
        return await get_client(request).get_meter_location(meter_id)

    @application.get(
        "/meters/{meter_id}/energy",
        response_model=EnergyResponse,
        response_model_by_alias=True,
    )
    async def get_meter_energy(
        request: Request,
        meter_id: str = Path(min_length=1),
    ) -> EnergyResponse:
        return await get_client(request).get_meter_energy(meter_id)

    @application.get(
        "/transformers",
        response_model=PortalPage[DistributionTransformer],
        response_model_by_alias=True,
    )
    async def list_transformers(
        request: Request,
        page: int = Query(default=1, ge=1),
    ) -> PortalPage[DistributionTransformer]:
        return await get_client(request).list_transformers(page=page)

    return application


app = create_app()