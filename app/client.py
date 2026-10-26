from typing import TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from app.models import (
    DistributionTransformer,
    EnergyResponse,
    MeterLocationResponse,
    MeterSummary,
    PortalPage,
)


class PortalClientError(Exception):
    """Base class for failures communicating with the portal."""


class PortalTimeoutError(PortalClientError):
    """The portal did not respond before the configured timeout."""


class PortalUpstreamError(PortalClientError):
    """The portal returned a non-success HTTP status."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Portal returned HTTP {status_code}")


class PortalResponseError(PortalClientError):
    """The portal response was not valid JSON matching the observed schema."""


ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class PortalClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("Portal base URL must not be empty")

        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout),
            follow_redirects=False,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def list_meters(
        self, *, query: str = "", page: int = 1
    ) -> PortalPage[MeterSummary]:
        return await self._get(
            "/portal/meters/search",
            PortalPage[MeterSummary],
            params={"q": query, "page": page},
        )

    async def get_meter_location(
        self, meter_id: str
    ) -> MeterLocationResponse:
        return await self._get(
            f"/portal/meters/{quote(meter_id, safe='')}/geo",
            MeterLocationResponse,
        )

    async def get_meter_energy(self, meter_id: str) -> EnergyResponse:
        return await self._get(
            f"/portal/meters/{quote(meter_id, safe='')}/energy",
            EnergyResponse,
        )

    async def list_transformers(
        self, *, page: int = 1
    ) -> PortalPage[DistributionTransformer]:
        return await self._get(
            "/portal/dts",
            PortalPage[DistributionTransformer],
            params={"page": page},
        )

    async def _get(
        self,
        path: str,
        response_model: type[ResponseModel],
        *,
        params: dict[str, str | int] | None = None,
    ) -> ResponseModel:
        try:
            response = await self._http.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise PortalTimeoutError("Portal request timed out") from exc
        except httpx.RequestError as exc:
            raise PortalClientError("Could not connect to the portal") from exc

        if not response.is_success:
            raise PortalUpstreamError(response.status_code)

        try:
            payload = response.json()
            return response_model.model_validate(payload)
        except (ValueError, ValidationError) as exc:
            raise PortalResponseError(
                "Portal returned an invalid response"
            ) from exc